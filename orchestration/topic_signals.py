#!/usr/bin/env python3
"""
topic_signals.py — сбор ВНЕШНИХ сигналов спроса на темы (PL), по рубрикам канала.

Зачем отдельно от `idea_miner.py`: тот заточен под YouTube (outlier-детект по V/S, топ ниши,
комменты) и стоит квоты. Здесь — бесплатный слой поисковых подсказок из трёх независимых
источников, сгруппированный по широкой редакционной карте и производственным рубрикам.

Принцип тот же, что и везде в проекте: скрипт СОБИРАЕТ формулировки живых людей, решения
принимает человек. Тему не выдумываем — берём то, что реально набирают в строке поиска.

⚠️ Собственную статистику канала сюда НЕ подмешиваем (решение владельца 2026-08-14): она
отражает историю канала, а не спрос рынка, и загоняет темы в повтор.

Использование:
    python3 orchestration/topic_signals.py                      # все рубрики → stdout (JSON)
    python3 orchestration/topic_signals.py --rubric day_body    # одна рубрика
    python3 orchestration/topic_signals.py --out signals.json   # в файл
    python3 orchestration/topic_signals.py --seed "kawa rano"   # свой засев

Источники (проверены 2026-08-14, все отдают 200 без ключей и прокси):
  - Google Suggest (веб-поиск, hl=pl&gl=pl) — самые богатые формулировки;
  - YouTube Suggest (тот же endpoint, ds=yt) — что ищут именно на платформе;
  - DuckDuckGo Autocomplete — независимая проверка, что сигнал не артефакт Google.
Полный разбор доступности источников — orchestration/research/67_external_demand_sources.md
"""
from __future__ import annotations
import re
import sys
import json
import time
import argparse
import urllib.parse
import urllib.request
from collections import OrderedDict

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"}

# Засев по рубрикам. Формулировки польские и намеренно «незаконченные» — подсказка
# дополняет их так, как это делает живой человек в строке поиска.
SEEDS: dict[str, list[str]] = {
    "plate": [
        "ile żelaza w", "ile białka w", "ile wapnia w", "ile magnezu w", "witaminy w",
        "co niszczy witaminy", "gotowanie warzyw", "smażenie na oleju", "mrożone warzywa",
        "przechowywanie warzyw", "podgrzewanie jedzenia", "jajka", "kasza", "jogurt naturalny"],
    "day_body": [
        "kawa rano", "picie wody", "jedzenie wieczorem", "zmęczenie po jedzeniu",
        "senność po obiedzie", "budzenie się w nocy", "głód wieczorem", "spacer po jedzeniu",
        "telefon przed snem", "jedzenie przed snem", "kolejność jedzenia", "drzemka"],
    "how_much": [
        "ile cukru w", "ile kofeiny ma", "ile wody dziennie", "ile białka dziennie",
        "ile soli dziennie", "ile kroków dziennie", "ile godzin snu", "ile błonnika dziennie"],
    "really_true": [
        "czy jajka są", "czy mleko jest", "czy sól", "czy chleb", "czy cukier",
        "czy mikrofalówka", "czy owoce wieczorem", "czy kawa szkodzi", "czy gluten",
        "czy ziemniaki tuczą", "czy warto jeść"],
    "label": [
        "jaka forma magnezu", "przyswajalność", "witamina d dawka", "co oznacza na etykiecie"],
    # Тело, мозг, спорт и рабочая продуктивность — самостоятельные области поиска, а не
    # запасные варианты к питанию/добавкам.
    "body_signals": ["objawy niedoboru", "co oznacza", "dlaczego mam"],
    "at_shelf": ["który jogurt lepszy", "który olej lepszy", "różnica między produktami"],
    "kitchen_chem": ["dlaczego jedzenie", "co się dzieje gdy", "jak przechowywać"],
    "movement": [
        "trening siłowy", "ćwiczenia", "chodzenie", "bieganie", "regeneracja",
        "mobilność", "siedzenie", "zakwasy"],
    "brain": [
        "koncentracja", "pamięć", "nauka", "uwaga", "stres a mózg", "sen a mózg",
        "przerwy w pracy", "decyzje"],
    "performance": [
        "produktywność", "praca przy komputerze", "zmęczenie przy komputerze",
        "kawa a skupienie", "światło rano", "przerwy w pracy", "siedzenie", "energia w pracy"],
    "research_lab": [
        "nowe badanie zdrowie", "badanie sen", "badanie kawa", "badanie mózg",
        "meta analiza zdrowie", "naukowcy odkryli", "przegląd badań"],
}

# Подсказки поиска — общая свалка: по «magnez» приходит `magnus carlsen`, по «czy to prawda»
# — сплетни про блогеров. Два фильтра: чёрный список явно чужих доменов смысла и требование
# хотя бы одного слова из бытового словаря еды/самочувствия.
_JUNK = re.compile(
    r"(magnus|carlsen|monster|magnet|piosenk|tekst|cda|film|serial|lyrics|mem\b|gra\b|"
    r"minecraft|fortnite|tiktok|kanał|nie żyje|zdrożeć|podrożeć|inpost|akwarium|"
    r"forum|w ciąży|niemowl|latek|dziecko|pies|kot\b|karolek|bajk|piosenk|minecraft|"
    r"fabuł|wojanek)", re.I)
_TOPICAL = re.compile(
    r"(ile|czy|jak|dlaczego|kiedy|co\b|witamin|białk|żelaz|magnez|wapni|cukr|kofein|sól|"
    r"wod[ay]|sen\b|snu\b|śniadan|kaw[ay]|jedz|gotow|zdrow|dawk|organizm|tłuszcz|błonnik|"
    r"jelit|energi|zmęcz|kalori|posił|jajk|mleko|chleb|olej|warzyw|owoc|trening|ćwicz|"
    r"biegan|mięśn|regener|mobil|zakwas|koncentr|pamięć|mózg|nauk|badani|uwag|praca|"
    r"produktyw|siedzen|postaw|kręgosłup|decyzj|światł)", re.I)


def _get(url: str, timeout: float = 10.0):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()


def suggest_google(q: str, youtube: bool = False, lang: str = "pl") -> list[str]:
    ds = "&ds=yt" if youtube else ""
    u = (f"https://suggestqueries.google.com/complete/search?client=firefox{ds}"
         f"&hl={lang}&gl=pl&q={urllib.parse.quote(q)}")
    try:
        return json.loads(_get(u).decode("utf-8", "replace"))[1]
    except Exception:
        return []


def suggest_ddg(q: str) -> list[str]:
    u = f"https://duckduckgo.com/ac/?q={urllib.parse.quote(q)}&kl=pl-pl"
    try:
        return [x.get("phrase", "") for x in json.loads(_get(u).decode("utf-8", "replace"))]
    except Exception:
        return []


def clean(items: list[str]) -> list[str]:
    out = []
    for s in items:
        s = (s or "").strip().lower()
        if len(s) < 6 or len(s.split()) < 2 or _JUNK.search(s) or not _TOPICAL.search(s):
            continue
        out.append(s)
    return list(OrderedDict.fromkeys(out))


def harvest(seeds: list[str], pause: float = 0.25) -> list[str]:
    bag: list[str] = []
    for s in seeds:
        bag += suggest_google(s)
        time.sleep(pause)
        bag += suggest_google(s, youtube=True)
        time.sleep(pause)
        bag += suggest_ddg(s)
        time.sleep(pause)
    return clean(bag)


def main():
    p = argparse.ArgumentParser(description="Внешние сигналы спроса на темы (PL)")
    p.add_argument("--rubric", default="", help=f"одна из: {', '.join(SEEDS)}")
    p.add_argument("--seed", action="append", default=[], help="свой засев (можно несколько)")
    p.add_argument("--out", default="", help="файл для JSON (по умолчанию stdout)")
    a = p.parse_args()

    if a.seed:
        result = {"custom": harvest(a.seed)}
    else:
        rubrics = [a.rubric] if a.rubric else list(SEEDS)
        result = {}
        for r in rubrics:
            if r not in SEEDS:
                raise SystemExit(f"неизвестная рубрика '{r}'; есть: {', '.join(SEEDS)}")
            result[r] = harvest(SEEDS[r])
            print(f"[{r}] {len(result[r])} формулировок", file=sys.stderr)

    text = json.dumps(result, ensure_ascii=False, indent=1)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)
        print(f"[ok] {a.out}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
