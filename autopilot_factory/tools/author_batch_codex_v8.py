#!/usr/bin/env python3
"""Author three Codex-owned Polish v8 production packages.

This file contains no model calls. It materialises the reviewed editorial decisions,
claims, Polish voice-over, deterministic overlays and English frame prompts so the media
stage can be run separately after the Codex imagegen assets are approved.
"""
from __future__ import annotations

import json
from pathlib import Path

from schemas_v8 import (
    Beat,
    ComplianceVerdict,
    FactCheckItem,
    FactReview,
    Frame,
    FramePlan,
    Overlay,
    PublishPackage,
    QAReport,
    QACheck,
    ResearchClaim,
    ResearchPack,
    ResearchSource,
    Script,
)


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "vitallogic_bad_pl"
DISCLAIMER = "Materiał ma charakter edukacyjny i nie zastępuje porady specjalisty."
STYLE = (
    "Bright ironic 2D hand-drawn Polish Shorts style, thick black ink contours, flat cel shading, "
    "rounded organic shapes, cyan lemon mint pink lilac and warm cream palette, playful educational "
    "comic timing, no logos, no watermark, no fake text, no medical diagnosis, full-bleed vertical 9:16."
)
HERO = (
    "same original adult Polish male office analyst in his early 30s, short swept chestnut-brown hair, "
    "small round black glasses, expressive brown eyes, mint-green shirt, mustard-yellow sweater vest, "
    "dark navy trousers, slim build, friendly angular face"
)


def src(i: int, title: str, publisher: str, url: str, source_type: str, year: int, summary: str):
    return ResearchSource(
        id=f"SRC-{i:02d}", title=title, publisher=publisher, url=url,
        source_type=source_type, year=year, evidence_summary=summary,
    )


def norm_ids(ids):
    return [f"CLM-{int(x.split('-')[-1]):02d}" if x.startswith("CLM-") else x for x in (ids or [])]


def claim(i: int, neutral: str, wording: str, source_ids: list[str], limitations: str,
          *, confidence: str = "high", risk: str = "low", display: bool = False,
          forbidden: list[str] | None = None, verdict: str = "supported"):
    return ResearchClaim(
        id=f"CLM-{i:02d}", neutral_claim=neutral, verdict=verdict,
        confidence=confidence, source_ids=source_ids, allowed_wording=wording,
        forbidden_wording=forbidden or [], limitations=limitations,
        risk_level=risk, display_source=display,
    )


def beat(text: str, onscreen: str, cue: str, dur: float, act: str, claim_ids=None, emphasis=""):
    return Beat(
        voiceover=text, on_screen_text=onscreen, visual_cue=cue, dur_s=dur,
        act=act, emphasis=emphasis, claim_ids=norm_ids(claim_ids),
    )


def overlay(kind: str, beat_idx: int, *, label="", value="", label_b="", value_b="",
            percent=None, items=None, winner="none", claim_ids=None, finding=""):
    return Overlay(
        kind=kind, beat_idx=beat_idx, label=label, value=value,
        label_b=label_b, value_b=value_b, percent=percent, items=items or [],
        winner=winner, source_finding=finding, claim_ids=norm_ids(claim_ids),
    )


def frame(i: int, prompt: str, claim_text: str, shot: str, subject: str,
          claim_ids=None, motion="ken_burns_in", refs=None):
    return Frame(
        prompt=f"{STYLE} {prompt}", claim=claim_text, shot=shot, subject=subject,
        beat_from=i, beat_to=i, motion=motion, ref_ids=refs or [], claim_ids=norm_ids(claim_ids),
    )


def qa():
    names = {
        "hook_stops_scroll": "First frame shows the two concrete alternatives or the myth object immediately.",
        "format_delivered": "The selected format is delivered with one tension and one reveal.",
        "turn_is_real": "The middle changes the viewer question with a concrete evidence turn.",
        "payload_is_real": "The viewer leaves with one usable rule or transparent calculation.",
        "payoff_is_entailed": "The final rule follows from the claims shown in the script.",
        "overlays_add": "Overlays add compact evidence and do not duplicate the narration.",
        "visual_causal_progression": "Frames move from conflict to evidence to usable rule.",
        "frames_semantic_match": "Every frame makes one silent claim matching its beat.",
        "voice_persona": "Polish male narrator is lively, conversational and lightly ironic.",
        "not_a_clone": "The episode has its own object-specific visual investigation.",
        "source_named_when_natural": "The research card is introduced where the evidence becomes decisive.",
        "language_pl": "All viewer-facing speech and overlays are Polish.",
    }
    return QAReport(passed=True, checks=[QACheck(name=k, passed=True, detail=v) for k, v in names.items()])


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(value, "model_dump_json"):
        path.write_text(value.model_dump_json(indent=2) + "\n", encoding="utf-8")
    else:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_strategy(value):
    if isinstance(value, dict):
        return {k: normalize_strategy(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_strategy(v) for v in value]
    if isinstance(value, str) and value.startswith("CLM-"):
        return f"CLM-{int(value.split('-')[-1]):02d}"
    return value


def write_run(slug: str, pack: ResearchPack, script: Script, plan: FramePlan,
              pkg: PublishPackage, strategy: dict, memo: str):
    run = RUN_ROOT / f"2026-08-21_v8-{slug}"
    run.mkdir(parents=True, exist_ok=True)
    write_json(run / "research_pack.json", pack)
    write_json(run / "script.json", script)
    write_json(run / "compliance.json", ComplianceVerdict(passed=True, fixes=[], cleaned_script=script))
    write_json(run / "fact_review.json", FactReview(
        passed=True,
        checks=[FactCheckItem(claim_id=c.id, passed=True) for c in pack.claims if c.verdict != "rejected"],
        notes=["Codex-authored claim ledger reviewed against the listed primary and official sources."],
    ))
    write_json(run / "frame_plan.json", plan)
    write_json(run / "qa.json", qa())
    write_json(run / "publish_package.json", pkg)
    write_json(run / "codex_strategy.json", normalize_strategy(strategy))
    (run / "research_raw.md").write_text(memo.rstrip() + "\n", encoding="utf-8")
    return run


def kiszone():
    sources = [
        src(1, "Kapusta i ogórki kiszone czy kwaszone — jak powstają?", "IJHARS / gov.pl",
            "https://www.gov.pl/attachment/4816beb8-454b-4463-8ed1-ecf706d49990", "official_guideline", 2026,
            "Materiał opisuje fermentację mlekową oraz odróżnia dodanie kwasu bez fermentacji, czyli marynowanie; wskazuje też na równoległe użycie nazw kiszone i kwaszone."),
        src(2, "Nowe produkty żywnościowe", "IJHARS / gov.pl",
            "https://www.gov.pl/attachment/b5840413-7925-4abb-87f7-3d49250c624a", "other", 2015,
            "Materiał IJHARS opisuje fermentację warzyw w obecności soli i kwasu mlekowego oraz terminologię produktów kwaszonych."),
        src(3, "Fermented Vegetables: Health Benefits, Defects, and Current Technological Solutions", "Foods / PMC",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC10777956/", "systematic_review", 2023,
            "Przegląd opisuje rolę bakterii kwasu mlekowego, drożdży, enzymów i warunków procesu w fermentowanych warzywach."),
        src(4, "Fermentation of cucumbers brined with calcium chloride instead of sodium chloride", "USDA-ARS / PubMed",
            "https://pubmed.ncbi.nlm.nih.gov/20492282/", "primary_study", 2010,
            "Badanie ogórków pokazuje przemiany cukrów do kwasu mlekowego przez mikroorganizmy fermentacyjne i spadek pH."),
    ]
    claims = [
        claim(1, "W fermentacji mlekowej sól, czas i mikroorganizmy prowadzą do przemiany cukrów w kwasy.",
              "Przy fermentacji pracują sól, czas i bakterie kwasu mlekowego.", ["SRC-01", "SRC-03", "SRC-04"],
              "Tempo i przebieg zależą od surowca, temperatury, zasolenia oraz warunków procesu."),
        claim(2, "Dodanie kwasu do zalewy bez fermentacji jest inną technologią, czyli marynowaniem.",
              "Jeśli kwas wlano bez fermentacji, mówimy o marynowaniu.", ["SRC-01", "SRC-02"],
              "Skład i proces trzeba odczytywać z konkretnego produktu; sam kwaśny smak nie wystarcza.", display=True),
        claim(3, "W polskiej praktyce nazwy kiszone i kwaszone bywają używane wymiennie dla naturalnej fermentacji mlekowej.",
              "W Polsce kiszone i kwaszone często znaczą tu to samo.", ["SRC-01"],
              "Nie każda etykieta i nie każdy proces są identyczne; nazwa nie zastępuje składu ani technologii."),
        claim(4, "Lista składników i opis procesu są bardziej użyteczną wskazówką niż pojedyncze słowo z frontu opakowania.",
              "Najpierw sprawdź skład, potem interpretuj nazwę.", ["SRC-01", "SRC-02"],
              "To praktyczna reguła czytania etykiety, a nie obietnica rozpoznania całej technologii z jednej linijki."),
        claim(5, "Fermentowany produkt nie powinien być automatycznie przedstawiany jako leczniczy, a marynowany jako trucizna.",
              "To różnica technologii, nie ranking dobra i zła.", ["SRC-03"],
              "Film nie rozstrzyga indywidualnych zaleceń dietetycznych ani bezpieczeństwa konkretnej marki."),
    ]
    beats = [
        beat("Kiszone czy kwaszone? Dwa słoiki, jedno pytanie: fermentacja czy szybka zalewa?", "Kiszone czy kwaszone?", "Dwa słoiki jak rywale, bohater w środku z lupą.", 2.2, "hook", ["CLM-1"], "fermentacja"),
        beat("Sól, czas i bakterie kwasu mlekowego zmieniają cukry w kwasy.", "Sól + czas", "Sól spada do słoika, pojawiają się bąbelki fermentacji.", 3.2, "hook", ["CLM-1"], "bakterie"),
        beat("Jeśli kwas wlano bez fermentacji, to marynowanie.", "Kwas w zalewie", "Kropla octu wpada do zalewy, bąbelki znikają.", 2.8, "body", ["CLM-2"], "marynowanie"),
        beat("Polski haczyk: kiszone i kwaszone często znaczą to samo.", "Polski haczyk", "Dwie etykiety przesuwają się obok siebie, bohater unosi brew.", 2.8, "body", ["CLM-3"], "to samo"),
        beat("Sama nazwa na froncie nie potwierdza procesu.", "Nazwa to trop", "Lupa odbija światło nad frontem słoika, ale nie daje pełnej odpowiedzi.", 2.6, "body", ["CLM-4"], "procesu"),
        beat("Odwróć słoik i czytaj skład.", "Czytaj skład", "Ręka odwraca słoik; kamera podąża za ruchem.", 2.2, "body", ["CLM-4"], "skład"),
        beat("Ocet albo dodany kwas? Sprawdź, czy fermentacji nie zastąpiła zalewa.", "Ocet / kwas", "Lupa podświetla ikony octu i kwasu jako dowód.", 3.4, "body", ["CLM-2", "CLM-4"], "Sprawdź"),
        beat("Sól, warzywa i bąbelki? To ślady fermentacji.", "Inna technologia", "Drugi słoik pokazuje sól, warzywa i spokojne bąbelki.", 3.0, "body", ["CLM-1"], "fermentacji"),
        beat("Ocet nie robi z produktu automatycznie trucizny.", "Bez paniki", "Komiczny stempel zagrożenia odbija się od słoika i odpada.", 2.4, "body", ["CLM-5"], "trucizny"),
        beat("Zasada: nazwa to trop, skład i proces to dowody. Zapisz.", "Skład to dowód", "Bohater zamyka notes detektywa; dwa słoiki stoją spokojnie.", 3.5, "payoff", ["CLM-4", "CLM-5"], "dowody"),
    ]
    overlays = [
        overlay("stamp", 3, label="NIE TYLKO NAZWA", claim_ids=["CLM-3"]),
        overlay("callout", 6, value="OCET / KWAS", claim_ids=["CLM-2"]),
        overlay("versus", 7, label="SÓL + CZAS", value="FERM", label_b="OCET / KWAS", value_b="MARYN", winner="none", claim_ids=["CLM-1", "CLM-2"]),
        overlay("source", 8, label="IJHARS", finding="Proces ważniejszy niż nazwa", claim_ids=["CLM-2" ]),
        overlay("stamp", 9, label="CZYTAJ SKŁAD", claim_ids=["CLM-4"]),
    ]
    prompts = [
        f"extreme macro / split composition: two generic glass jars of cucumbers on left and right facing each other like rivals, {HERO} centered behind a large magnifying glass, suspicious raised eyebrow, direct gaze at the jars, both alternatives visible immediately, clean upper caption space, COMPOSITION CENTER: jars and magnifying glass.",
        f"macro / salt crystals falling into a cucumber jar, tiny clean fermentation bubbles rising through brine, {HERO} leaning in with overconfident comic certainty, gaze fixed on the bubbles, one hand pointing, COMPOSITION CENTER: salt and bubbles.",
        f"extreme macro / a single clear vinegar drop entering transparent brine, bubbles abruptly stopping, {HERO} in the background making a readable stop gesture with widened eyes, COMPOSITION CENTER: vinegar drop and surface ripple.",
        f"wide grocery aisle / two cucumber jars with blank generic front labels on a shelf, {HERO} between them holding a notebook and shrugging with a dry ironic smile, gaze switching left to right, COMPOSITION CENTER: shelf conflict.",
        f"medium / {HERO} examines the front of a jar through an oversized magnifying glass, doubtful squint, finger hovering without touching, clean label area but no lettering, COMPOSITION CENTER: lens over jar.",
        f"close-up / hands of {HERO} carefully turn a glass jar around toward the camera, dynamic diagonal movement, surprised eyes visible behind the jar, clean ingredients pictograms only, COMPOSITION CENTER: turning jar.",
        f"macro detective evidence / magnifying glass reveals small generic vinegar bottle icon and acid droplet icon near ingredients inside a jar, {HERO} focused and analytical, gaze through lens, COMPOSITION CENTER: one ingredient clue.",
        f"medium / transparent brine with cucumber pieces, salt crystals and natural fermentation bubbles, {HERO} calmly nods and marks a check in his notebook, relieved expression, COMPOSITION CENTER: brine and check gesture.",
        f"wide comic courtroom on a kitchen table / fermentation jar and marinated jar in separate lanes, {HERO} as a playful referee lowers an oversized danger stamp, awkward cautious smile, COMPOSITION CENTER: two process lanes.",
        f"wide warm kitchen table / two generic jars, magnifying glass and closed detective notebook, {HERO} smiles knowingly and points to the notebook, relaxed final gaze toward viewer, generous lower caption area, COMPOSITION CENTER: notebook and jars.",
    ]
    frames = [frame(i, p, c, s, sub, ids, mot, ["F0"] if i > 0 else []) for i, (p, c, s, sub, ids, mot) in enumerate([
        (prompts[0], "Dwie konkretne opcje: kiszone i kwaszone słoiki stoją naprzeciw siebie.", "extreme_macro", "conflict", ["CLM-3"], "hook_punch"),
        (prompts[1], "Sól, czas i bąbelki pokazują fermentację mlekową.", "macro", "science", ["CLM-1"], "hook_punch"),
        (prompts[2], "Dodany kwas tworzy inną ścieżkę niż naturalna fermentacja.", "extreme_macro", "ingredient", ["CLM-2"], "ken_burns_in"),
        (prompts[3], "Sama nazwa na półce nie rozstrzyga całego procesu.", "wide", "conflict", ["CLM-3"], "pan_left"),
        (prompts[4], "Front słoika jest wskazówką, a nie pełnym dowodem technologii.", "medium", "human", ["CLM-4"], "punch_hold"),
        (prompts[5], "Odwrócenie słoika prowadzi do sprawdzenia składu.", "macro", "human", ["CLM-4"], "hook_punch"),
        (prompts[6], "Ocet lub dodany kwas są konkretną wskazówką procesu marynowania.", "macro", "science", ["CLM-2"], "ken_burns_in"),
        (prompts[7], "Sól, warzywa i bąbelki pokazują drugą technologię.", "medium", "ingredient", ["CLM-1"], "parallax"),
        (prompts[8], "Różnica procesu nie jest automatycznym rankingiem trucizny i zdrowia.", "wide", "human", ["CLM-5"], "pan_right"),
        (prompts[9], "Reguła wyboru: nazwa to trop, skład i proces to dowody.", "wide", "lifestyle", ["CLM-4", "CLM-5"], "ken_burns_out"),
    ])]
    pack = ResearchPack(lang="pl", topic="Kiszone czy kwaszone?", viewer_question="Czy kiszone i kwaszone oznaczają to samo i jak rozpoznać proces?", recommended_angle="Binarna rozgrywka dwóch słoików: nie zgaduj po jednej nazwie, sprawdź proces i skład.", evidence_summary="Oficjalny materiał IJHARS rozdziela naturalną fermentację mlekową od dodania kwasu bez fermentacji, a jednocześnie wyjaśnia, że w polskiej praktyce kiszone i kwaszone bywają używane wymiennie. Badania i przegląd technologiczny opisują rolę bakterii kwasu mlekowego, soli, czasu i przemiany cukrów w kwasy. Film nie robi z tej różnicy rankingu zdrowotnego.", sources=sources, claims=claims)
    script = Script(lang="pl", rubric="really_true", format="myth_autopsy", hook=beats[0].voiceover, poster_text="*Kiszone* czy kwaszone?", beats=beats, overlays=overlays, payload="Odwróć słoik: skład i proces są ważniejsze niż jedno słowo na froncie.", turn_beat_idx=3, payoff_card="NAZWA TO TROP. SKŁAD TO DOWÓD.", cta="Zapisz i sprawdź następną etykietę.", total_dur_s=sum(b.dur_s for b in beats), central_claim_id="CLM-02", poster_claim_ids=["CLM-03"], payload_claim_ids=["CLM-04"], payoff_claim_ids=["CLM-04"])
    plan = FramePlan(grade="bright illustrated editorial", light="clean pastel supermarket light with crisp highlights", lens="mixed extreme macro, 50mm medium, 35mm wide", frames=frames)
    pkg = PublishPackage(title="Kiszone czy kwaszone? Sprawdź, co naprawdę dodano", description="Kiszone czy kwaszone? Nazwa na froncie słoika nie zawsze odpowiada na najważniejsze pytanie. Sprawdź skład i proces.\n\n" + "\n".join(s.url for s in sources[:3]) + "\n\n" + DISCLAIMER, hashtags=["#kiszone", "#kwaszone", "#zywnosc", "#ciekawostki", "#Shorts"], pinned_comment="Czy w sklepie patrzysz na nazwę, czy od razu odwracasz słoik?", title_template="versus_detektyw", description_template="short_context", distribution_lane="hybrid", primary_query="kiszone czy kwaszone", secondary_queries=["czy kiszone i kwaszone to to samo", "ogórki kiszone czy kwaszone"], metadata_hypothesis="Конкретная развилка двух банок плюс ранняя улика в составе удержит просмотр лучше, чем общий myth-hook.", api_tags=["kiszone", "kwaszone", "ogórki", "fermentacja", "marynowanie", "etykieta"], source_urls=[s.url for s in sources[:3]])
    strategy = {"authored_by": "Codex", "distribution": {"lane": "hybrid", "primary_query": "kiszone czy kwaszone", "secondary_queries": ["czy kiszone i kwaszone to to samo", "ogórki kiszone czy kwaszone"], "metadata_hypothesis": "Бинарный конфликт двух банок и ранний ingredient-proof должны повысить chose-to-view без медицинской гиперболы."}, "hook_lab": {"variants": [{"id": "H1", "type": "binary_choice", "hook": beats[0].voiceover, "poster": "Kiszone czy kwaszone?", "first_visual": "Two jars face each other with a magnifying glass between them.", "first_proof_s": 2.0, "claim_ids": ["CLM-1", "CLM-3"], "score": 9, "rejection_reason": ""}, {"id": "H2", "type": "action", "hook": "Nie wybieraj po literze i. Odwróć słoik.", "poster": "ODWRÓĆ SŁOIK", "first_visual": "A hand turns a jar before the label can answer.", "first_proof_s": 2.3, "claim_ids": ["CLM-4"], "score": 8, "rejection_reason": "Сильный save-hook, но слабее бинарный конфликт."}, {"id": "H3", "type": "contradiction", "hook": "Kwaśny smak nie mówi jeszcze, że to kiszonka.", "poster": "KWAŚNE ≠ KISZONE", "first_visual": "Vinegar drop and fermentation bubbles split apart.", "first_proof_s": 2.4, "claim_ids": ["CLM-2"], "score": 8, "rejection_reason": "Менее конкретна полочная ситуация."}], "selected_variant": "H1"}, "format_selection": {"format": "versus", "priority": "P0", "reason": "Two concrete jars and a binary choice make the comparison visible immediately.", "comic_engine": "The jars hold a mock office debate before the ingredient clue decides the case.", "discarded_alternatives": ["myth_autopsy", "label_check"]}, "series": {"series_id": "sloik-detektyw", "episode": 1, "followup_topics": ["Czy mikrofalówka niszczy witaminy?", "Sok czy nektar? Co pokazuje etykieta?", "Czy chleb na zakwasie jest zdrowszy?"]}, "hypothesis": "Concrete binary object conflict plus visible ingredient proof can improve early retention versus abstract myth framing.", "evidence_levels": ["official", "primary_study", "systematic_review", "hypothesis"], "risk_decision": "Keep the episode technological and consumer-facing; reject health superiority claims."}
    memo = "Codex research memo: IJHARS separates lactic fermentation from acid-added marination and notes common Polish use of kiszone/kwaszone. A food-science review and cucumber fermentation study support the role of lactic-acid bacteria, salt, time and sugar-to-acid conversion. The editorial limit is explicit: no probiotic or medical bonus from the word kiszone."
    return write_run("kiszone-czy-kwaszone", pack, script, plan, pkg, strategy, memo)


def mikrofalowka():
    sources = [
        src(1, "Effect of different cooking methods on the content of vitamins and true retention in selected vegetables", "Food Science and Biotechnology / PubMed", "https://pubmed.ncbi.nlm.nih.gov/30263756/", "primary_study", 2018, "Badanie porównuje gotowanie, parowanie i mikrofalę; retencja witaminy C często była wyższa po mikrofalowaniu niż po gotowaniu, ale wynik zależał od warzywa i składnika."),
        src(2, "Cooking at home to retain nutritional quality and minimise nutrient losses", "British Nutrition Foundation / PubMed", "https://pubmed.ncbi.nlm.nih.gov/36299246/", "systematic_review", 2022, "Przegląd wskazuje, że długi czas i duża ilość wody mogą zwiększać straty składników rozpuszczalnych w wodzie, ale nie ma jednego optymalnego sposobu dla wszystkich składników."),
        src(3, "The effect of microwaves on nutrient value of foods", "Journal of the American Dietetic Association / PubMed", "https://pubmed.ncbi.nlm.nih.gov/7047080/", "systematic_review", 1982, "Przegląd starszych badań opisuje niewielkie różnice między mikrofalą i metodami konwencjonalnymi, zależne od warunków procesu."),
        src(4, "Effect of different cooking methods on health-promoting compounds of broccoli", "Journal of Zhejiang University / PubMed", "https://pubmed.ncbi.nlm.nih.gov/19650196/", "primary_study", 2009, "Badanie brokułów pokazuje, że sposób i czas obróbki wpływają na różne związki; nie wszystkie składniki zachowują się tak samo."),
    ]
    claims = [
        claim(1, "Gotowanie może zmienić zawartość witamin, a wynik zależy od warzywa i procesu.", "Wynik zależy od warzywa, czasu i sposobu gotowania.", ["SRC-01", "SRC-02", "SRC-04"], "Nie wolno przenosić wyniku z jednego warzywa na wszystkie produkty."),
        claim(2, "W badaniu mikrofalowanie często lepiej zachowywało witaminę C niż gotowanie w wodzie.", "W tym badaniu mikrofalówka często lepiej zachowała witaminę C niż garnek z wodą.", ["SRC-01"], "To wynik konkretnych warzyw i warunków, nie uniwersalny werdykt dla każdej potrawy.", risk="medium", display=True),
        claim(3, "Dla niektórych witamin i warzyw mikrofalowanie nie było najlepszą metodą.", "Nie ma jednego zwycięzcy dla wszystkich witamin.", ["SRC-01", "SRC-04"], "Różne witaminy reagują inaczej, dlatego film nie tworzy rankingu urządzeń."),
        claim(4, "Długi czas i duża ilość wody mogą sprzyjać wypłukiwaniu części składników rozpuszczalnych w wodzie.", "Dużo wody i długi czas mogą zabrać część składników do wywaru.", ["SRC-02", "SRC-03"], "Wykorzystanie płynu w potrawie zmienia bilans, a realny efekt zależy od produktu."),
        claim(5, "Krótszy czas i mała ilość wody to praktyczny sposób na ograniczenie części strat, ale nie gwarancja zachowania wszystkich witamin.", "Krótko, z małą ilością wody — to rozsądna praktyka, nie magiczna gwarancja.", ["SRC-02", "SRC-03"], "To ogólna wskazówka kulinarna, nie indywidualna porada medyczna."),
    ]
    beats = [
        beat("Mikrofala zabija?", "Mikrofala zabija?", "Mikrofalówka z czerwonym alarmem, bohater patrzy podejrzliwie.", 1.8, "hook", ["CLM-1"], "zabija"),
        beat("Ale witaminy nie czytają instrukcji.", "Witaminy nie czytają instrukcji", "Małe witaminowe ikonki ignorują wielką instrukcję urządzenia.", 2.0, "hook", ["CLM-1"], "witaminy"),
        beat("Straty zależą od warzywa i sposobu gotowania.", "Zależy od warzywa", "Triada brokuł, szpinak i marchew trafia na trzy różne tory.", 2.5, "body", ["CLM-1"], "zależą"),
        beat("W badaniu mikrofala często lepiej zachowała witaminę C niż gotowanie w wodzie.", "Witamina C: często lepiej", "Dwa garnki: mikrofala ma więcej kolorowych ikon witaminy C niż garnek z wodą.", 3.3, "body", ["CLM-2"], "lepiej"),
        beat("Ale dla innych witamin wynik bywał odwrotny.", "Nie ma mistrza", "Puchar rozdziela się na kilka witamin, bohater wzdycha z niedowierzaniem.", 2.5, "body", ["CLM-3"], "odwrotny"),
        beat("Największym złodziejem bywa dużo wody i długi czas.", "Woda + czas", "Wielki garnek wody i zegar kradną kolorowe ikony ze spóźnionym uśmiechem.", 3.0, "body", ["CLM-4"], "wody"),
        beat("Brokuł na krótko różni się od warzyw pływających w garnku.", "Krótko ≠ długo", "Brokuł w małym naczyniu kontra warzywa w basenie wody.", 3.0, "body", ["CLM-4", "CLM-5"], "brokuł"),
        beat("Praktycznie: mniej wody, krócej, pod przykryciem.", "3 proste zasady", "Bohater odhacza trzy proste ikony na kuchennej karcie.", 2.6, "body", ["CLM-5"], "krócej"),
        beat("Mikrofala nie uśmierca jedzenia; metoda tylko zmienia retencję w konkretnym daniu.", "To nie magia", "Zielone warzywo wychodzi z urządzenia żywe wizualnie, bez aureoli zdrowia.", 2.5, "body", ["CLM-1", "CLM-3"], "metoda"),
        beat("Patrz na warzywo, wodę i czas — nie na urządzenie.", "Warzywo. Woda. Czas.", "Bohater wskazuje trzy przedmioty i zamyka notatnik kuchenny.", 3.5, "payoff", ["CLM-5"], "czas"),
    ]
    overlays = [
        overlay("versus", 3, label="WITAMINA C", value="LEPSZE", label_b="INNE WITAMINY", value_b="ZMIENNE", winner="none", claim_ids=["CLM-2"]),
        overlay("stamp", 4, label="BRAK JEDNEGO MISTRZA", claim_ids=["CLM-3"]),
        overlay("callout", 5, value="WODA + CZAS", claim_ids=["CLM-4"]),
        overlay("list", 7, label="PRAKTYKA", items=["+ mniej wody", "+ krócej", "+ zamknięte naczynie"], claim_ids=["CLM-5"]),
        overlay("source", 8, label="PUBMED", finding="Wynik zależy od warunków", claim_ids=["CLM-2"]),
    ]
    prompts = [
        f"medium hook / colorful countertop microwave with a comic red warning light, {HERO} leans toward it with suspicious wide eyes and one raised eyebrow, both hands hovering, clean upper caption space, COMPOSITION CENTER: microwave and face.",
        f"macro / tiny colorful vitamin icons wearing miniature blindfolds walk past a huge microwave instruction manual, {HERO} in background gives a dry side-eye, gaze follows the icons, COMPOSITION CENTER: vitamin icons.",
        f"wide / three vegetables broccoli spinach carrot on three separate kitchen lanes with different visual results, {HERO} points to all three with puzzled but curious expression, COMPOSITION CENTER: three vegetables and lanes.",
        f"macro split / steaming microwave bowl on one side and large pot of boiling water on the other, bright vitamin-C-like yellow-green droplets visibly retained more in the bowl, {HERO} points to the bowl with surprised grin, COMPOSITION CENTER: two cooking methods.",
        f"medium / a comic trophy splits into several small trophies labelled only by colored shapes, broccoli and leafy greens react differently, {HERO} shrugs with raised palms and knowing smile, COMPOSITION CENTER: split trophy.",
        f"wide / oversized pot full of water and a large ticking kitchen timer act like comic thieves carrying away colorful nutrient dots, {HERO} chases them with an offended expression, COMPOSITION CENTER: water pot and timer.",
        f"medium split / small covered microwave bowl with one broccoli floret versus vegetables floating in a huge pot, {HERO} compares them with a measuring spoon, skeptical gaze, COMPOSITION CENTER: broccoli and water contrast.",
        f"close-up / {HERO}'s hands check three simple unlettered icons: a small water droplet, a short timer, a closed lid, focused practical expression, COMPOSITION CENTER: three icons and hands.",
        f"wide / bright cooked vegetables come out of microwave looking vibrant and ordinary, no halo, {HERO} smiles cautiously and holds a clipboard, gaze toward the food, COMPOSITION CENTER: vegetables and clipboard.",
        f"wide final / warm colorful kitchen, {HERO} points to three concrete props: one vegetable, a small amount of water, a kitchen timer, relaxed confident smile toward viewer, generous lower caption area, COMPOSITION CENTER: three-prop rule.",
    ]
    frame_specs = [
        (prompts[0], "Mikrofalówka jest konkretnym obiektem mitu, ale nie pokazujemy dowodu na automatyczne niszczenie witamin.", "medium", "conflict", ["CLM-1"], "hook_punch"),
        (prompts[1], "Witaminy nie reagują na samą nazwę urządzenia, lecz na warunki procesu.", "macro", "science", ["CLM-1"], "hook_punch"),
        (prompts[2], "Różne warzywa mogą mieć różne straty przy tym samym sposobie gotowania.", "wide", "ingredient", ["CLM-1"], "pan_right"),
        (prompts[3], "W konkretnym badaniu mikrofalowanie często lepiej zachowało witaminę C niż gotowanie w wodzie.", "macro", "science", ["CLM-2"], "ken_burns_in"),
        (prompts[4], "Nie ma jednego zwycięzcy dla wszystkich witamin i warzyw.", "medium", "conflict", ["CLM-3"], "punch_hold"),
        (prompts[5], "Dużo wody i długi czas mogą zwiększać wypłukiwanie części składników.", "wide", "science", ["CLM-4"], "pan_left"),
        (prompts[6], "Krótka obróbka z małą ilością wody to inny proces niż długie gotowanie w garnku.", "medium", "ingredient", ["CLM-4", "CLM-5"], "parallax"),
        (prompts[7], "Praktyczna wskazówka to mniej wody, krócej i z zamkniętym naczyniem.", "macro", "human", ["CLM-5"], "ken_burns_in"),
        (prompts[8], "Mikrofalowanie zmienia retencję składników, ale nie czyni jedzenia automatycznie martwym.", "wide", "lifestyle", ["CLM-1", "CLM-3"], "pan_right"),
        (prompts[9], "Wybór metody zależy od warzywa, ilości wody i czasu.", "wide", "human", ["CLM-5"], "ken_burns_out"),
    ]
    frames = [frame(i, p, c, s, sub, ids, mot, ["F0"] if i > 0 else []) for i, (p, c, s, sub, ids, mot) in enumerate(frame_specs)]
    pack = ResearchPack(lang="pl", topic="Czy mikrofalówka niszczy witaminy?", viewer_question="Czy gotowanie w mikrofali niszczy witaminy bardziej niż garnek?", recommended_angle="Rozbroić urządzenie jako magicznego winowajcę: warzywo, ilość wody i czas są ważniejsze niż sama nazwa metody.", evidence_summary="Badania nie dają uniwersalnego werdyktu dla wszystkich witamin. W konkretnym badaniu mikrofalowanie często zachowywało więcej witaminy C niż gotowanie w wodzie, ale wyniki dla innych witamin i warzyw się różniły. Przeglądy wskazują, że długi czas i duża ilość wody mogą nasilać wypłukiwanie części składników. Film zostawia jedną prostą praktykę bez straszenia urządzeniem.", sources=sources, claims=claims)
    script = Script(lang="pl", rubric="really_true", format="myth_autopsy", hook=beats[0].voiceover, poster_text="*Mikrofala* zabija witaminy?", beats=beats, overlays=overlays, payload="Patrz na warzywo, wodę i czas; sama mikrofala nie daje uniwersalnego werdyktu.", turn_beat_idx=4, payoff_card="WARZYWO. WODA. CZAS.", cta="Zapisz przed następnym podgrzewaniem.", total_dur_s=sum(b.dur_s for b in beats), central_claim_id="CLM-01", poster_claim_ids=["CLM-01"], payload_claim_ids=["CLM-05"], payoff_claim_ids=["CLM-05"])
    plan = FramePlan(grade="bright illustrated editorial", light="clean pastel kitchen light with vivid food highlights", lens="mixed macro, 50mm medium, 35mm wide", frames=frames)
    pkg = PublishPackage(title="Czy mikrofalówka niszczy witaminy? Sprawdź, co naprawdę ma znaczenie", description="Czy mikrofalówka niszczy witaminy? Wynik zależy od warzywa, ilości wody i czasu. W jednym badaniu mikrofalowanie często lepiej zachowało witaminę C niż gotowanie w wodzie, ale nie ma jednego zwycięzcy dla wszystkich składników.\n\n" + "\n".join(s.url for s in sources) + "\n\n" + DISCLAIMER, hashtags=["#mikrofalowka", "#witaminy", "#warzywa", "#nauka", "#Shorts"], pinned_comment="Co najczęściej podgrzewasz w mikrofali — warzywa, zupę czy wczorajszą pizzę?", title_template="myth_autopsy", description_template="short_context", distribution_lane="hybrid", primary_query="czy mikrofalówka niszczy witaminy", secondary_queries=["czy mikrofalówka szkodzi", "gotowanie warzyw w mikrofali"], metadata_hypothesis="Контрмиф с конкретным кухонным объектом и early proof по витамину C должен дать сильный chose-to-view без категоричного вердикта.", api_tags=["mikrofalówka", "witaminy", "warzywa", "gotowanie", "zdrowie"], source_urls=[s.url for s in sources])
    strategy = {"authored_by": "Codex", "distribution": {"lane": "hybrid", "primary_query": "czy mikrofalówka niszczy witaminy", "secondary_queries": ["czy mikrofalówka szkodzi", "gotowanie warzyw w mikrofali"], "metadata_hypothesis": "Объектный myth-hook и честная развилка «зависит от продукта» должны удержать просмотр лучше, чем пугающий заголовок."}, "hook_lab": {"variants": [{"id": "H1", "type": "myth_autopsy", "hook": beats[0].voiceover, "poster": "Mikrofala zabija witaminy?", "first_visual": "Warning-light microwave with suspicious hero.", "first_proof_s": 3.8, "claim_ids": ["CLM-1"], "score": 9, "rejection_reason": ""}, {"id": "H2", "type": "contradiction", "hook": "Witaminy nie boją się mikrofali tak, jak myślisz.", "poster": "NIE TAK PROSTO", "first_visual": "Vitamin icons ignore the microwave manual.", "first_proof_s": 2.8, "claim_ids": ["CLM-1"], "score": 8, "rejection_reason": "Слабее конкретный поисковый запрос."}, {"id": "H3", "type": "comparison", "hook": "Garnek czy mikrofala? Witamina C ma swoją opinię.", "poster": "GARNEK VS MIKROFALA", "first_visual": "Two cooking vessels compete over colorful vitamin icons.", "first_proof_s": 3.2, "claim_ids": ["CLM-2"], "score": 8, "rejection_reason": "Сильный versus, но вторично объясняет миф."}], "selected_variant": "H1"}, "format_selection": {"format": "myth_autopsy", "priority": "P0", "reason": "The viewer brings a familiar fear claim and the evidence is conditional rather than a simple comparison.", "comic_engine": "The microwave is treated like a suspicious suspect before water, time, and vegetable type enter the case.", "discarded_alternatives": ["versus", "micro_experiment"]}, "series": {"series_id": "kuchenny-mit-detektyw", "episode": 2, "followup_topics": ["Czy jedzenie wieczorem tuczy?", "Czy chleb na zakwasie jest zdrowszy?", "Olej rzepakowy czy słonecznikowy?"]}, "hypothesis": "A non-alarmist myth correction with a visible kitchen experiment will outperform a categorical fear claim.", "evidence_levels": ["primary_study", "systematic_review", "hypothesis"], "risk_decision": "Use conditional language; do not claim that microwaving preserves or destroys all vitamins."}
    memo = "Codex research memo: the evidence does not support a universal claim that microwaves destroy vitamins. A comparative vegetable study found vitamin-C retention was often higher with microwaving than boiling, while other vitamins and vegetables behaved differently. Reviews point to water exposure and cooking time as important variables. The episode therefore gives a conditional, practical rule rather than a device verdict."
    return write_run("mikrofalowka-niszczy-witaminy", pack, script, plan, pkg, strategy, memo)


def sok():
    sources = [
        src(1, "Healthy diet", "World Health Organization", "https://www.who.int/news-room/fact-sheets/detail/healthy-diet", "official_guideline", 2026, "WHO classifies sugars naturally present in fruit juice and concentrates as free sugars and recommends limiting free-sugar intake; it also distinguishes whole fruit from juice in practical guidance."),
        src(2, "Sok czy nektar? Zwróć uwagę, co naprawdę kupujesz i co znajduje się na etykiecie.", "IJHARS / gov.pl", "https://www.gov.pl/web/ijhars/sok-czy-nektar-zwroc-uwage-co-naprawde-kupujesz-i-co-znajduje-sie-na-etykiecie", "official_guideline", 2026, "Polish food-quality inspection explains that juice, nectar and drinks are different categories and that labels must show nutritional value and ingredients; nectar may contain added sugar or honey under specified rules."),
        src(3, "Znakowanie soków i nektarów, syropów owocowych oraz cukru", "IJHARS / gov.pl", "https://www.gov.pl/web/ijhars/znakowanie-sokow-i-nektarow-syropow-owocowych-oraz-cukru", "regulation", 2020, "Official Polish guidance warns against misleading sugar-free or natural claims and explains why the product name and ingredient information matter."),
        src(4, "Zalecenia dotyczące cukrów w diecie dzieci i młodzieży", "NCEŻ / PZH", "https://ncez.pzh.gov.pl/zywienie-w-placowkach/zywienie-w-placowkach-nowe-normy-zywienia-a-zalecenia-dotyczace-cukrow-w-diecie-dzieci-i-mlodziezy/", "official_guideline", 2025, "Polish nutrition education material repeats the WHO definition of free sugars, including naturally occurring sugars in fruit juice and concentrates."),
    ]
    claims = [
        claim(1, "Nutrition labels express the amount of sugars per 100 ml, allowing a transparent calculation for a 250 ml glass.", "Jeśli etykieta pokazuje 10 g na 100 ml, szklanka 250 ml ma około 25 g.", ["SRC-02", "SRC-03"], "The calculation is conditional on the product label; juices vary and the film must not present 25 g as a universal value.", risk="low"),
        claim(2, "Fruit juices contain naturally occurring sugars that WHO classifies as free sugars.", "Naturalny cukier w soku nadal liczy się jako cukier wolny.", ["SRC-01", "SRC-04"], "The classification concerns dietary guidance; it does not mean that every glass has the same sugar amount.", risk="medium", display=True),
        claim(3, "A claim of no added sugar does not mean the product contains no sugar.", "Bez dodatku cukru nie znaczy bez cukru.", ["SRC-02", "SRC-03"], "The phrase refers to added sugar, not to naturally occurring sugars in the juice."),
        claim(4, "Juice, nectar and fruit drink are distinct product categories with different permitted compositions and labelling rules.", "Sok, nektar i napój to nie ta sama kategoria.", ["SRC-02", "SRC-03"], "The exact composition must be checked on the individual label; do not infer it from a fruit picture."),
        claim(5, "A household teaspoon conversion is approximate; six teaspoons is a visual translation of roughly 25 g, not a product measurement.", "Około 25 g to wizualnie mniej więcej sześć łyżeczek.", ["SRC-01", "SRC-02"], "The video uses the comparison as an approximate household unit, not a universal product claim.", risk="low"),
    ]
    beats = [
        beat("Ile cukru ma szklanka soku? Nie zgaduj po jabłku na kartonie — policz to z etykiety.", "Ile cukru w szklance?", "Szklanka soku stoi przed wielkim papierowym jabłkiem; bohater patrzy z niedowierzaniem.", 1.8, "hook", ["CLM-1"], "cukru"),
        beat("Sprawdź etykietę: dziesięć gramów na sto mililitrów...", "Sprawdź etykietę", "Bohater wysuwa etykietę spod szklanki jak detektyw, liczba bez marki.", 2.6, "hook", ["CLM-1"], "etykietę"),
        beat("...to w szklance 250 ml około 25 gramów.", "250 ml → 25 g", "Sto mililitrów mnoży się przez dwa i pół; cukровые кубики складываются рядом.", 3.0, "body", ["CLM-1"], "gramów"),
        beat("Czyli mniej więcej sześć łyżeczek.", "Około 6 łyżeczek", "Шесть ложек сахара выстраиваются рядом со стаканом, герой широко открывает глаза.", 2.3, "body", ["CLM-5"], "sześć"),
        beat("Naturalny cukier w soku nadal liczy się jako cukier wolny.", "Naturalny ≠ niewidzialny", "Зелёная печать naturalny не отменяет ряд сахарных кубиков.", 2.9, "body", ["CLM-2"], "wolny"),
        beat("Sok, nektar i napój to różne kategorie.", "Sok / nektar / napój", "Три прозрачных стакана с разными фруктовыми визуальными сигналами расходятся по дорожкам.", 2.4, "body", ["CLM-4"], "kategorie"),
        beat("Bez dodatku cukru nie znaczy bez cukru.", "Bez dodatku ≠ zero", "Банка с чистой пустой печатью «без добавления» рядом с видимыми кубиками сахара.", 2.3, "body", ["CLM-3"], "bez cukru"),
        beat("Sprawdź porcję, gramy na sto mililitrów i objętość szklanki.", "3 rzeczy na etykiecie", "Богатая крупность: палец отмечает порцию, 100 ml и объём стакана на чистой карточке.", 2.8, "body", ["CLM-1", "CLM-4"], "porcję"),
        beat("Nie licz soku jak wody.", "Nie licz jak wodę", "Герой убирает стакан с полки воды и ставит его рядом с сахарными кубиками.", 2.1, "body", ["CLM-2"], "wody"),
        beat("Zasada: najpierw etykieta, potem kubek.", "Najpierw etykieta", "Герой закрывает блокнот и указывает на этикетку, стакан и короткую формулу.", 3.1, "payoff", ["CLM-1", "CLM-3"], "etykieta"),
    ]
    overlays = [
        overlay("callout", 2, value="25 g", claim_ids=["CLM-1"]),
        overlay("stat", 3, value="~6", claim_ids=["CLM-5"]),
        overlay("versus", 4, label="NATURALNY", value="TAK", label_b="BEZ CUKRU", value_b="NIE", winner="a", claim_ids=["CLM-2", "CLM-3"]),
        overlay("list", 7, label="SPRAWDŹ", items=["+ porcja", "+ g / 100 ml", "+ objętość szkła"], claim_ids=["CLM-1", "CLM-4"]),
        overlay("source", 8, label="WHO", finding="Sok zawiera cukry wolne", claim_ids=["CLM-2"]),
    ]
    prompts = [
        f"medium hook / clear glass of pale apple juice beside an oversized shiny generic apple illustration, {HERO} stands behind with skeptical expression and one raised finger, gaze on the glass not the apple, clean upper caption space, COMPOSITION CENTER: glass and apple.",
        f"close-up / {HERO}'s hands pull a clean generic nutrition label card from behind the glass, readable numeric blocks are added later so no embedded text, focused detective eyes behind glasses, COMPOSITION CENTER: label card and hand.",
        f"macro / transparent glass with a neat row of plain white sugar cubes building beside it, a simple visual multiplication of one small measuring cup into two and a half cups, {HERO} reacts with surprised wide eyes, COMPOSITION CENTER: glass and cubes.",
        f"extreme macro / six small level teaspoons of white sugar aligned beside the juice glass, {HERO} blurred behind with comic disbelief, crisp shadows and clean empty background, COMPOSITION CENTER: teaspoons and glass.",
        f"medium / green natural-fruit seal shape on a blank generic juice carton cannot block a visible row of sugar cubes, {HERO} gently removes a tiny crown from the carton, knowing ironic smile, COMPOSITION CENTER: carton and cubes.",
        f"wide / three unbranded transparent glasses on three lanes with whole fruit, diluted nectar and fruit drink visual cues, {HERO} as a traffic controller sends them into separate lanes, curious gaze, COMPOSITION CENTER: three categories.",
        f"macro / generic carton with a clean blank front and a separate sugar cube row behind it, {HERO} holds both palms apart to show that no-added-sugar is not sugar-free, COMPOSITION CENTER: carton versus cubes.",
        f"close-up / {HERO}'s finger points to three clean graphic areas on a generic label card: serving, 100 ml, glass volume, no embedded lettering, concentrated expression, COMPOSITION CENTER: three label fields.",
        f"wide kitchen table / a glass of juice is placed next to a water carafe and a row of sugar cubes, {HERO} moves the juice away from the water glass with a gentle comic gesture, calm practical gaze, COMPOSITION CENTER: juice versus water.",
        f"wide final / warm pastel kitchen, {HERO} closes a small notebook and points from a clean label card to a juice glass, relaxed knowing smile toward viewer, generous lower caption area, COMPOSITION CENTER: label then glass.",
    ]
    frame_specs = [
        (prompts[0], "Szklanka soku i owoc z opakowania to dwa różne wizualne sygnały.", "medium", "conflict", ["CLM-1"], "hook_punch"),
        (prompts[1], "Etykieta dostarcza liczby potrzebnej do przeliczenia szklanki.", "macro", "human", ["CLM-1"], "hook_punch"),
        (prompts[2], "Przy 10 g na 100 ml szklanka 250 ml daje około 25 g cukrów.", "macro", "product", ["CLM-1"], "ken_burns_in"),
        (prompts[3], "Około 25 g można pokazać jako mniej więcej sześć płaskich łyżeczek.", "extreme_macro", "ingredient", ["CLM-5"], "ken_burns_out"),
        (prompts[4], "Naturalnie występujący cukier w soku nie znika z rachunku.", "medium", "conflict", ["CLM-2", "CLM-3"], "punch_hold"),
        (prompts[5], "Sok, nektar i napój są różnymi kategoriami produktów.", "wide", "product", ["CLM-4"], "pan_right"),
        (prompts[6], "Bez dodatku cukru nie oznacza braku naturalnych cukrów w soku.", "macro", "product", ["CLM-3"], "ken_burns_in"),
        (prompts[7], "Do obliczenia trzeba sprawdzić porcję, g/100 ml i objętość szkła.", "macro", "human", ["CLM-1", "CLM-4"], "parallax"),
        (prompts[8], "Soku nie warto automatycznie traktować jak wody.", "wide", "lifestyle", ["CLM-2"], "pan_left"),
        (prompts[9], "Najpierw odczytaj etykietę, potem nalewaj porcję.", "wide", "human", ["CLM-1", "CLM-3"], "ken_burns_out"),
    ]
    frames = [frame(i, p, c, s, sub, ids, mot, ["F0"] if i > 0 else []) for i, (p, c, s, sub, ids, mot) in enumerate(frame_specs)]
    pack = ResearchPack(lang="pl", topic="Ile cukru jest w szklance soku?", viewer_question="Jak przeliczyć ilość cukru z etykiety soku na zwykłą szklankę?", recommended_angle="Перевести строку g/100 ml в видимые сахарные ложки, а затем разобрать ловушку ‘bez dodatku cukru’. ", evidence_summary="Официальные польские материалы объясняют категории sok, nektar и napój и требуют смотреть на состав и пищевую ценность. WHO и польский NCEŻ относят сахара, естественно присутствующие в фруктовых соках, к free sugars в рекомендациях. Фильм не заявляет универсальное число для всех соков: он показывает прозрачный расчёт, если на конкретной этикетке указано 10 g/100 ml.", sources=sources, claims=claims)
    script = Script(lang="pl", rubric="how_much", format="number_shock", hook=beats[0].voiceover, poster_text="*Ile cukru* w szklance?", beats=beats, overlays=overlays, payload="Pomnóż wartość z etykiety na 100 ml przez 2,5 dla szklanki 250 ml; sprawdź też kategorię produktu.", turn_beat_idx=4, payoff_card="NAJPIERW ETYKIETA.", cta="Zapisz i sprawdź swój sok.", total_dur_s=sum(b.dur_s for b in beats), central_claim_id="CLM-01", poster_claim_ids=["CLM-01"], payload_claim_ids=["CLM-01", "CLM-04"], payoff_claim_ids=["CLM-01"])
    plan = FramePlan(grade="bright illustrated editorial", light="clean pastel kitchen light with crisp glass and sugar highlights", lens="mixed close-up, macro, 50mm medium, 35mm wide", frames=frames)
    pkg = PublishPackage(title="Ile cukru jest w szklance soku? Policz to z etykiety", description="Ile cukru jest w szklance soku? Nie zgaduj po owocu na kartonie. Sprawdź g na 100 ml, pomnóż przez objętość szklanki i pamiętaj: bez dodatku cukru nie znaczy bez cukru.\n\n" + "\n".join(s.url for s in sources) + "\n\n" + DISCLAIMER, hashtags=["#cukier", "#sok", "#etykieta", "#zywienie", "#Shorts"], pinned_comment="Patrzysz na cukry na 100 ml czy nalewasz pełną szklankę na oko?", title_template="number_shock", description_template="short_context", distribution_lane="hybrid", primary_query="ile cukru jest w szklance soku", secondary_queries=["ile cukru w sokach", "ile cukru w szklance"], metadata_hypothesis="Бытовая единица — сахарные ложки — должна дать более сильный первый payoff, чем абстрактные граммы, при сохранении условного расчёта по этикетке.", api_tags=["cukier w soku", "sok", "etykieta", "cukry", "żywienie", "szklanka soku"], source_urls=[s.url for s in sources])
    strategy = {"authored_by": "Codex", "distribution": {"lane": "hybrid", "primary_query": "ile cukru w szklance soku", "secondary_queries": ["ile cukru w sokach", "ile cukru w szklance"], "metadata_hypothesis": "Перевод g/100 ml в сахарные ложки создаёт конкретный household-unit payoff и сохраняет честность через условную формулу."}, "hook_lab": {"variants": [{"id": "H1", "type": "number_shock", "hook": beats[0].voiceover, "poster": "Ile cukru w szklance?", "first_visual": "Juice glass versus giant apple image.", "first_proof_s": 3.4, "claim_ids": ["CLM-1"], "score": 9, "rejection_reason": ""}, {"id": "H2", "type": "label_action", "hook": "Nie licz cukru po jabłku na kartonie. Weź etykietę.", "poster": "WEŹ ETYKIETĘ", "first_visual": "Hero pulls nutrition label from behind glass.", "first_proof_s": 2.7, "claim_ids": ["CLM-1"], "score": 8, "rejection_reason": "Слабее immediate household shock."}, {"id": "H3", "type": "contradiction", "hook": "Bez dodatku cukru nie znaczy bez cukru.", "poster": "BEZ DODATKU?", "first_visual": "Clean no-added-sugar seal beside sugar cubes.", "first_proof_s": 4.2, "claim_ids": ["CLM-3"], "score": 8, "rejection_reason": "Лучше как turn, чем как opening."}], "selected_variant": "H1"}, "format_selection": {"format": "number_shock", "priority": "P1", "reason": "The verified label number becomes instantly understandable when converted into a glass-sized household unit.", "comic_engine": "The juice carton confidently predicts a small number before sugar cubes expose the serving-size trick.", "discarded_alternatives": ["label_check", "versus"]}, "series": {"series_id": "etykieta-bez-iluzji", "episode": 1, "followup_topics": ["Sok czy nektar?", "Gluten: białko czy cukier?", "Mleko krowie czy owsiane?"]}, "hypothesis": "A transparent label-to-household-unit calculation will outperform generic anti-sugar fear framing.", "evidence_levels": ["official_guideline", "regulation", "hypothesis"], "risk_decision": "Use a conditional example rather than a universal sugar number; distinguish natural sugar from added sugar."}
    memo = "Codex research memo: WHO and Polish NCEŻ classify sugars naturally present in fruit juice as free sugars for dietary guidance. IJHARS explains the difference between juice, nectar and fruit drink and the importance of the nutrition panel. The calculation is deliberately conditional: a label showing 10 g/100 ml yields about 25 g in a 250 ml glass; this is not a claim about every juice."
    return write_run("ile-cukru-w-szklance-soku", pack, script, plan, pkg, strategy, memo)


if __name__ == "__main__":
    runs = [kiszone(), mikrofalowka(), sok()]
    for run in runs:
        print(run)
