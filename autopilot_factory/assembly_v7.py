#!/usr/bin/env python3
"""
assembly_v7.py — сборка ролика v7. Отличия от `assembly.py` (v1-v6) — по порядку важности:

1. **Слой информационной графики.** Семь видов оверлеев (stat/bar/versus/list/callout/stamp/
   timeline) рендерятся детерминированно в CSS+GSAP поверх кадра. Раньше в сборке жили ровно
   три текстовых объекта — постер, субтитр и CTA-плашка — и ни одной цифры (аудит §2.2).

2. **Звуковой дизайн.** SFX из бандла hyperframes-media (Pixabay Content License: коммерческое
   использование без атрибуции) на появление графики, смену кадра, бит-поворот и финал.
   Плюс ducking музыки под голос и обрыв музыки перед payoff. Раньше — голос + один трек
   на −21дБ и ни одного акцента (аудит §2.4).

3. **Кадр покрывает диапазон битов**, а не один бит. На границе бита внутри кадра ставится
   punch-in — визуальное событие без оплаты нового кадра.

4. **Payoff-карточка** вместо финального фото с вопросом: вывод ролика крупным текстом на
   бренд-фоне. Это кадр, ради которого ролик сохраняют.

Рендер остаётся детерминированным: одна пауза-таймлайн GSAP, никаких CSS-анимаций и
requestAnimationFrame — hyperframes перематывает таймлайн покадрово.
"""
from __future__ import annotations
import os
import json
import shutil
import subprocess
from html import escape
from pathlib import Path

# --- бренд-константы (VitalLogic) -----------------------------------------------
NAVY = "#2A5C82"
GREEN = "#4CAF50"
CREAM = "#F5F5F5"
YELLOW = "#FFDD00"
INK = "#0E1620"

# Safe-зоны 1080×1920. Консервативное пересечение источников (research/60 §5 + сверка
# 2026-08-12): сверху ≥200px под UI, снизу ≥380px под подпись канала и описание,
# справа ≥120px под колонку кнопок.
SAFE_TOP = 200
SAFE_BOTTOM = 380
SAFE_RIGHT = 120
# Боковой отступ для ЦЕНТРИРОВАННОГО контента — симметричный, равный самому жёсткому
# ограничению (правая колонка кнопок Shorts). Асимметричные отступы «слева 70, справа 140»
# уводят блок на 35px влево от центра кадра: сам по себе он центрирован внутри своей
# коробки, но коробка смещена. Замер 2026-08-12: постер и payoff-карточка (симметричные
# отступы) стояли ровно, субтитры и графика — на −35px. Разнобой заметнее самого сдвига,
# потому что постер и субтитр видны одновременно.
SAFE_SIDE = SAFE_RIGHT

_HF_JSON = {
    "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
    "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
    "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
}

# Бандл SFX едет со скиллом hyperframes-media. Копируем нужные файлы в рабочую папку прогона,
# чтобы сборка не зависела от наличия скилла в момент рендера.
SFX_SRC = Path.home() / ".claude" / "skills" / "hyperframes-media" / "assets" / "sfx"


def _node22_env() -> dict:
    """hyperframes CLI требует Node ≥20 (util.styleText). Ищем свежий Node в nvm, если
    системный старее. Портировано из assembly.py — поведение не меняем."""
    env = os.environ.copy()
    try:
        v = subprocess.run(["node", "-v"], capture_output=True, text=True, env=env).stdout.strip()
        if v.startswith("v") and int(v[1:].split(".")[0]) >= 20:
            return env
    except Exception:
        pass
    nvm = Path.home() / ".nvm" / "versions" / "node"
    if nvm.is_dir():
        best = None
        for d in nvm.iterdir():
            try:
                major = int(d.name.lstrip("v").split(".")[0])
            except ValueError:
                continue
            if major >= 20 and (best is None or major > best[0]):
                best = (major, d)
        if best:
            env["PATH"] = f"{best[1] / 'bin'}:{env.get('PATH', '')}"
    return env


# --- движение кадра -------------------------------------------------------------
def _motion_tween(sel: str, motion: str, start: float, dur: float) -> str:
    punch = min(0.55, dur / 2)
    m = {
        "ken_burns_in":  f'tl.fromTo("{sel}",{{scale:1.02}},{{scale:1.13,duration:{dur},ease:"none"}},{start});',
        "ken_burns_out": f'tl.fromTo("{sel}",{{scale:1.13}},{{scale:1.02,duration:{dur},ease:"none"}},{start});',
        "pan_left":      f'tl.fromTo("{sel}",{{scale:1.10,xPercent:3}},{{xPercent:-3,duration:{dur},ease:"none"}},{start});',
        "pan_right":     f'tl.fromTo("{sel}",{{scale:1.10,xPercent:-3}},{{xPercent:3,duration:{dur},ease:"none"}},{start});',
        "parallax":      f'tl.fromTo("{sel}",{{scale:1.08,yPercent:2}},{{yPercent:-2,duration:{dur},ease:"none"}},{start});',
        # v7: punch_hold — кадр «дышит» медленно, чтобы не спорить с графикой поверх него
        "punch_hold":    f'tl.fromTo("{sel}",{{scale:1.04}},{{scale:1.08,duration:{dur},ease:"none"}},{start});',
        "hook_punch":    (f'tl.fromTo("{sel}",{{scale:1.18}},{{scale:1.06,duration:{punch:.3f},ease:"power3.out"}},{start});'
                          f'tl.to("{sel}",{{scale:1.12,duration:{max(dur - punch, 0.1):.3f},ease:"none"}},{start + punch:.3f});'),
    }
    return m.get(motion, m["ken_burns_in"])


def _frame_clips(frame_spans, motions, beat_starts, beat_durs, total):
    """Кадр покрывает диапазон битов (v7). Возвращает клипы, твины движения и — отдельно —
    моменты внутренних границ битов, куда сборка ставит punch-in: визуальное событие
    посреди длинного кадра, чтобы план не «застывал» (research/01: план ≤2.5с)."""
    clips, tweens, punches = [], [], []
    # Границы кадров — по округлённым значениям, длительность = разница соседних границ.
    # Независимое округление start и duration давало наложение соседних клипов в 1 мс
    # (линтер: overlapping_clips_same_track, поймано 2026-08-12).
    bounds = [round(beat_starts[bf], 3) for bf, _ in frame_spans]
    bounds.append(round(beat_starts[frame_spans[-1][1]] + beat_durs[frame_spans[-1][1]], 3))
    for i, (b_from, b_to) in enumerate(frame_spans):
        start = bounds[i]
        dur = max(round(bounds[i + 1] - bounds[i], 3), 0.4)
        # Кадр живёт в обёртке: основное движение анимирует <img>, толчок на границе бита —
        # ОБЁРТКУ. Раньше и то и другое писало `scale` одного элемента, причём толчок
        # относительными значениями (`+=0.035`). Относительный твин берёт базу в момент
        # инициализации, а рендер идёт несколькими воркерами — холодный воркер стартовал с
        # другого состояния, и один и тот же кадр выходил в двух разных положениях (рывок на
        # стыке чанков). Поймано линтером hyperframes 2026-08-12: gsap_relative_value_second_writer.
        clips.append(
            f'<div id="fw{i}" class="clip fwrap" data-start="{start:.3f}" '
            f'data-duration="{dur:.3f}" data-track-index="1">'
            f'<img id="f{i}" class="frame" src="assets/frame{i}.png"/></div>'
        )
        mo = motions[i] if i < len(motions) else "ken_burns_in"
        tweens.append(_motion_tween(f"#f{i}", mo, start, dur))
        # Границы битов внутри кадра остаются точками для ЗВУКА, но визуального толчка
        # на них больше нет. Толчок «вверх и обратно» на каждой границе читался как
        # регулярная пульсация картинки (владелец, 2026-08-12): для появления кадра такое
        # уместно, в середине плана — нет. Ритм в середине держат появления графики и
        # субтитры, а сам кадр едет непрерывным Ken Burns без рывков.
        punches.extend(beat_starts[b] for b in range(b_from + 1, b_to + 1))
    return clips, tweens, punches


# --- субтитры -------------------------------------------------------------------
def _chunk_words(words: list[dict], max_words: int, max_chars: int = 24):
    chunks: list[list[dict]] = []
    cur: list[dict] = []
    cur_chars = 0
    for w in words:
        token = w["text"]
        add = len(token) + (1 if cur else 0)
        if cur and (len(cur) >= max_words or cur_chars + add > max_chars):
            chunks.append(cur)
            cur, cur_chars, add = [], 0, len(token)
        cur.append(w)
        cur_chars += add
    if cur:
        chunks.append(cur)
    return chunks


def _norm(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


def _caption_clips(beat_words, fallback_captions, beat_starts, beat_durs,
                   emphases: list[str], max_words: int = 3, max_chars: int = 24):
    """Караоке-субтитры. v7: слово из `Beat.emphasis` получает не только подсветку, но и
    увеличенный кегль — ударное слово должно быть видно как ударное, а не как соседнее."""
    clips, tweens = [], []
    cap_idx = 0
    prev_end = 0.0
    for i, words in enumerate(beat_words):
        emph = _norm(emphases[i]) if i < len(emphases) else ""
        if words:
            for chunk in _chunk_words(words, max_words, max_chars):
                cs, ce = chunk[0]["start"], chunk[-1]["end"]
                cs = max(cs, prev_end)
                ce = max(ce, cs)
                cd = max(ce - cs, 0.3)
                prev_end = cs + cd
                spans = []
                for j, w in enumerate(chunk):
                    wid = f"c{cap_idx}_w{j}"
                    is_emph = bool(emph) and _norm(w["text"]).startswith(emph[:max(len(emph) - 2, 3)])
                    cls = "word emph" if is_emph else "word"
                    spans.append(f'<span id="{wid}" class="{cls}">{escape(w["text"])}</span>')
                    ws, we = w["start"] - cs, w["end"] - cs
                    on = (f'color:"{YELLOW}",scale:1.16' if is_emph else f'color:"{YELLOW}",scale:1.07')
                    tweens.append(f'tl.to("#{wid}",{{{on},duration:0.07,ease:"power1.out"}},'
                                  f'{cs + max(ws, 0):.3f});')
                    tweens.append(f'tl.to("#{wid}",{{color:"#ffffff",scale:1.0,duration:0.12,'
                                  f'ease:"power1.out"}},{cs + we:.3f});')
                clips.append(
                    f'<div id="cap{cap_idx}" class="clip cap" data-start="{cs:.3f}" '
                    f'data-duration="{cd:.3f}" data-track-index="8">{" ".join(spans)}</div>'
                )
                tweens.append(f'tl.from("#cap{cap_idx}",{{opacity:0,y:22,duration:0.2,'
                              f'ease:"power2.out"}},{cs:.3f});')
                cap_idx += 1
        else:
            cap = escape(fallback_captions[i] or "").strip()
            if cap:
                cs, cd = beat_starts[i] + 0.1, max(beat_durs[i] - 0.1, 0.3)
                cs = max(cs, prev_end)
                prev_end = cs + cd
                clips.append(
                    f'<div id="cap{cap_idx}" class="clip cap" data-start="{cs:.3f}" '
                    f'data-duration="{cd:.3f}" data-track-index="8">{cap}</div>'
                )
                tweens.append(f'tl.from("#cap{cap_idx}",{{opacity:0,y:22,duration:0.25,'
                              f'ease:"power2.out"}},{cs:.3f});')
                cap_idx += 1
    return clips, tweens


# --- слой графики ---------------------------------------------------------------
def _accent_html(text: str) -> str:
    parts = text.split("*")
    if len(parts) < 3:
        return escape(text.replace("*", ""))
    return "".join(f'<span class="hl">{escape(p)}</span>' if i % 2 == 1 else escape(p)
                   for i, p in enumerate(parts) if p)


def _num_prefix(value: str) -> tuple[float | None, str, str]:
    """Разбирает «400 mg» / «12%» / «2×» на (число, префикс, суффикс) — чтобы GSAP мог
    докрутить счётчик от нуля, сохранив единицы измерения."""
    v = value.strip()
    i = 0
    while i < len(v) and (v[i].isdigit() or v[i] in ".,"):
        i += 1
    if i == 0:
        return None, "", v
    try:
        num = float(v[:i].replace(",", "."))
    except ValueError:
        return None, "", v
    return num, "", v[i:]


def _overlay_clips(overlays, beat_starts, beat_durs, n_beats):
    """Рендерит графику. Каждый оверлей живёт от своего бита до конца следующего (или до
    конца ролика, если бит последний) — чтобы успел прочитаться, но не залёживался."""
    clips, tweens, sfx_marks = [], [], []
    ordered = sorted(overlays, key=lambda o: o.beat_idx)
    # Окно графики привязано к СВОЕМУ биту плюс короткий хвост.
    #
    # До 2026-08-12 правило было «живи до конца СЛЕДУЮЩЕГО бита, но уступи следующему
    # оверлею за 0.08с» — и ошибалось в обе стороны сразу (владелец: «элементы пропадают
    # не тогда, когда нужно»):
    #   · графика плотная → оверлей гас РАНЬШЕ конца своей же фразы (9 случаев из 21
    #     по трём роликам), причём 0.2с фейда съедали ещё и остаток;
    #   · графика редкая → оверлей висел на чужих битах (versus жил 5.9с при своём бите 3.2с).
    # Плюс пол `max(..., 0.9)` мог перебить ограничение и вернуть наложение.
    TAIL = 0.35          # столько графика висит после конца своей фразы
    MIN_DUR = 0.7        # ниже этого элемент не успевает прочитаться
    GAP = 0.05           # зазор до следующего оверлея (1.5 кадра — глазом не видно)

    next_start = {}
    for i, o in enumerate(ordered[:-1]):
        nb = max(0, min(int(ordered[i + 1].beat_idx), n_beats - 1))
        next_start[id(o)] = beat_starts[nb]

    for k, ov in enumerate(ordered):
        bi = max(0, min(int(ov.beat_idx), n_beats - 1))
        start = beat_starts[bi]
        end = beat_starts[bi] + beat_durs[bi] + TAIL      # свой бит + хвост
        limit = next_start.get(id(ov))
        capped = False
        if limit is not None and limit - GAP < end:
            # уступаем следующему оверлею, но не раньше минимума — иначе элемент мигает
            end = max(limit - GAP, start + MIN_DUR)
            capped = True
        end = min(end, sum(beat_durs))                    # не выезжаем за конец ролика
        dur = max(end - start, MIN_DUR)
        oid = f"ov{k}"
        kind = ov.kind
        body = ""
        if kind == "stat":
            num, _, suffix = _num_prefix(ov.value)
            if num is not None:
                body = (f'<div class="statnum"><span id="{oid}_n">0</span>'
                        f'<span class="unit">{escape(suffix)}</span></div>')
                tweens.append(
                    f'(function(){{const o={{v:0}};tl.to(o,{{v:{num},duration:0.7,'
                    f'ease:"power2.out",onUpdate:function(){{const e=document.getElementById'
                    f'("{oid}_n");if(e)e.textContent=(({num}%1)?o.v.toFixed(1):Math.round(o.v));}}}},'
                    f'{start + 0.12:.3f});}})();')
            else:
                body = f'<div class="statnum">{escape(ov.value)}</div>'
            if ov.label:
                body += f'<div class="statlab">{_accent_html(ov.label)}</div>'
        elif kind == "bar":
            pct = ov.percent if ov.percent is not None else 0
            body = (f'<div class="barlab">{_accent_html(ov.label)}'
                    f'<span class="barval">{escape(ov.value or f"{pct}%")}</span></div>'
                    f'<div class="bartrack"><div id="{oid}_f" class="barfill"></div></div>')
            tweens.append(f'tl.fromTo("#{oid}_f",{{width:"0%"}},{{width:"{pct}%",duration:0.65,'
                          f'ease:"power2.out"}},{start + 0.14:.3f});')
        elif kind == "versus":
            wa = "win" if ov.winner == "a" else ""
            wb = "win" if ov.winner == "b" else ""
            body = (f'<div class="vs">'
                    f'<div class="vscol {wa}"><div class="vsval">{escape(ov.value)}</div>'
                    f'<div class="vslab">{escape(ov.label)}</div></div>'
                    f'<div class="vsmid">vs</div>'
                    f'<div class="vscol {wb}"><div class="vsval">{escape(ov.value_b)}</div>'
                    f'<div class="vslab">{escape(ov.label_b)}</div></div></div>')
        elif kind == "list":
            rows = []
            for j, it in enumerate(ov.items[:4]):
                mark, txt = "•", it
                if it.startswith("+"):
                    mark, txt = "✓", it[1:].strip()
                elif it.startswith("-"):
                    mark, txt = "✕", it[1:].strip()
                cls = "ok" if mark == "✓" else ("no" if mark == "✕" else "")
                rows.append(f'<div id="{oid}_r{j}" class="lrow {cls}">'
                            f'<span class="lmark">{mark}</span>{escape(txt)}</div>')
                tweens.append(f'tl.from("#{oid}_r{j}",{{opacity:0,x:-28,duration:0.22,'
                              f'ease:"power2.out"}},{start + 0.12 + j * 0.22:.3f});')
            head = f'<div class="lhead">{_accent_html(ov.label)}</div>' if ov.label else ""
            body = head + "".join(rows)
        elif kind == "callout":
            body = f'<div class="cotext">{_accent_html(ov.label or ov.value)}</div>'
        elif kind == "stamp":
            # Кегль от длины: «NIE» и «MIEJSCE 3» — разной ширины, фиксированные 112px
            # обрезали длинный вариант об правый край (поймано на прогоне 2026-08-12).
            txt = (ov.value or ov.label).strip()
            sfs = 112 if len(txt) <= 5 else (88 if len(txt) <= 9 else 68)
            body = f'<div class="stamptext" style="font-size:{sfs}px">{escape(txt)}</div>'
            tweens.append(f'tl.set("#{oid}",{{opacity:0}},0);'
                          f'tl.fromTo("#{oid}",{{scale:2.1,opacity:0,rotation:-14}},'
                          f'{{scale:1,opacity:1,rotation:-9,duration:0.26,ease:"power4.out"}},'
                          f'{start + 0.06:.3f});')
        elif kind == "source":
            body = f'<div class="srctext">{escape(ov.label or ov.value)}</div>'
        elif kind == "timeline":
            n = max(len(ov.items), 1)
            marks = []
            for j, it in enumerate(ov.items[:4]):
                left = (j / max(n - 1, 1)) * 100 if n > 1 else 50
                marks.append(f'<div id="{oid}_m{j}" class="tlmark" style="left:{left:.1f}%">'
                             f'<span class="tldot"></span>'
                             f'<span class="tllab">{escape(it)}</span></div>')
                tweens.append(f'tl.from("#{oid}_m{j}",{{opacity:0,scale:0.5,duration:0.2,'
                              f'ease:"back.out(2)"}},{start + 0.12 + j * 0.24:.3f});')
            head = f'<div class="lhead">{_accent_html(ov.label)}</div>' if ov.label else ""
            body = head + f'<div class="tlwrap"><div class="tlline"></div>{"".join(marks)}</div>'

        clips.append(f'<div id="{oid}" class="clip ov ov-{kind}" data-start="{start:.3f}" '
                     f'data-duration="{dur:.3f}" data-track-index="{5 + (k % 2)}">{body}</div>')
        # Каждый оверлей начинает таймлайн погашенным и входит через `fromTo`, а не `from`.
        # `from` оставляет элемент видимым в DOM до инициализации твина: при перемотке
        # (а hyperframes рендерит именно перемоткой) элемент мог мелькнуть до своего окна.
        tweens.append(f'tl.set("#{oid}",{{opacity:0}},0);')
        if kind == "stamp":
            pass                                   # у штампа свой вход (slam), задан выше
        elif kind == "source":
            tweens.append(f'tl.fromTo("#{oid}",{{opacity:0}},{{opacity:1,duration:0.2,'
                          f'ease:"power1.out"}},{start + 0.05:.3f});')
        else:
            tweens.append(f'tl.fromTo("#{oid}",{{opacity:0,y:34,scale:0.94}},'
                          f'{{opacity:1,y:0,scale:1,duration:0.24,'
                          f'ease:"back.out(1.4)"}},{start + 0.05:.3f});')
        # После фейда — явный `tl.set`: перемотка может встать ПОСЛЕ окна твина, и без
        # жёсткого гашения элемент остаётся видимым (линтер: gsap_exit_missing_hard_kill).
        # Длина гашения зависит от того, свободен ли хвост.
        # Если окно поджато следующим оверлеем (`capped`), фраза договаривается ровно в
        # момент смены — долгий фейд тогда съедает конец собственной реплики и читается как
        # «элемент пропал раньше времени». В этом случае гасим быстро; когда хвост свободен —
        # гасим мягко, уже после того, как фраза закончилась.
        fade = 0.10 if capped else min(0.22, max(dur * 0.15, 0.10))
        tweens.append(f'tl.to("#{oid}",{{opacity:0,duration:{fade:.3f},ease:"power1.in"}},'
                      f'{start + dur - fade:.3f});'
                      f'tl.set("#{oid}",{{opacity:0}},{start + dur + 0.02:.3f});')
        if kind != "source":                       # атрибуция появляется беззвучно
            sfx_marks.append((start + 0.05, f"overlay:{kind}"))
    return clips, tweens, sfx_marks


def _headline_clip(text: str, dur: float):
    """Постер кадра-0: виден ПОЛНОСТЬЮ с t=0 (лента показывает нулевой кадр как обложку —
    любая входная анимация делает его пустым именно в этот момент)."""
    if not text.strip():
        return [], []
    dur = max(dur, 0.8)
    fade = min(0.3, dur / 3)
    n = len(text.replace("*", ""))
    fs = 138 if n <= 16 else (120 if n <= 24 else (106 if n <= 34 else 94))
    clips = [f'<div id="hscrim" class="clip scrim" data-start="0.000" data-duration="{dur:.3f}" '
             f'data-track-index="3"></div>',
             f'<div id="headline" class="clip headline" style="font-size:{fs}px" data-start="0.000" '
             f'data-duration="{dur:.3f}" data-track-index="4">{_accent_html(text.strip())}</div>']
    tweens = [f'tl.to("#headline",{{opacity:0,duration:{fade:.3f},ease:"power1.in"}},{dur - fade:.3f});',
              f'tl.set("#headline",{{opacity:0}},{dur:.3f});',
              f'tl.to("#hscrim",{{opacity:0,duration:{fade:.3f},ease:"power1.in"}},{dur - fade:.3f});',
              f'tl.set("#hscrim",{{opacity:0}},{dur:.3f});']
    return clips, tweens


def _payoff_clip(text: str, start: float, total: float):
    """v7: финальная карточка с ВЫВОДОМ (не с вопросом) — кадр, ради которого ролик сохраняют.

    Правка владельца 2026-08-12: под текстом лежит КАДР 0. Раньше карточка была глухой
    бренд-плашкой, и финал висел в пустоте. Возврат первого кадра закрывает визуальную петлю
    «конец = начало»: в ленте ролик уходит на повтор без визуального шва, а первый кадр —
    единственный, который зритель уже точно видел, поэтому узнаётся мгновенно.
    Читаемость текста держит затемняющий скрим поверх кадра, а не заливка."""
    if not text.strip() or start >= total - 0.5:
        return [], []
    dur = total - start
    n = len(text.replace("*", ""))
    fs = 112 if n <= 24 else (96 if n <= 40 else (82 if n <= 60 else 70))
    # ВАЖНО: текст оборачивается во внутренний блок. `.potext` — flex-контейнер, и без обёртки
    # каждый <span> акцента становится отдельным flex-элементом в строке — текст не переносится
    # и уезжает за края кадра (поймано на тестовом рендере 2026-08-12).
    clips = [
        f'<img id="poframe" class="clip poframe" src="assets/frame0.png" '
        f'data-start="{start:.3f}" data-duration="{dur:.3f}" data-track-index="9"/>',
        f'<div id="pocard" class="clip pocard" data-start="{start:.3f}" '
        f'data-duration="{dur:.3f}" data-track-index="10"></div>',
        f'<div id="potext" class="clip potext" data-start="{start:.3f}" '
        f'data-duration="{dur:.3f}" data-track-index="11">'
        f'<div class="poinner" style="font-size:{fs}px">{_accent_html(text.strip())}</div></div>']
    # `tl.from` оставляет элемент видимым в DOM до инициализации твина: при перемотке
    # полноэкранная карточка накрывала кадры ДО своего окна (линтер:
    # gsap_fullscreen_overlay_starts_visible). Поэтому явный `tl.set` в нуле таймлайна,
    # а вход — через `tl.to`.
    tweens = [
        f'tl.set("#poframe",{{opacity:0}},0); tl.set("#pocard",{{opacity:0}},0); '
        f'tl.set("#potext",{{opacity:0}},0);',
        # медленный отъезд: кадр «выдыхает», а не замирает картинкой под текстом
        f'tl.fromTo("#poframe",{{scale:1.12}},{{scale:1.02,duration:{dur:.3f},ease:"none"}},{start:.3f});',
        f'tl.to("#poframe",{{opacity:1,duration:0.2,ease:"power2.out"}},{start:.3f});',
        f'tl.to("#pocard",{{opacity:1,duration:0.24,ease:"power2.out"}},{start:.3f});',
        f'tl.fromTo("#potext",{{opacity:0,y:40,scale:0.94}},{{opacity:1,y:0,scale:1,'
        f'duration:0.3,ease:"back.out(1.5)"}},{start + 0.08:.3f});']
    return clips, tweens


# --- CSS ------------------------------------------------------------------------
_GRAIN_SVG = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='260' "
              "height='260'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' "
              "baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E"
              "%3Crect width='260' height='260' filter='url(%23n)'/%3E%3C/svg%3E")

_CSS = f"""
:root{{--navy:{NAVY};--green:{GREEN};--cream:{CREAM};--yellow:{YELLOW};--ink:{INK}}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#000}}
body{{font-family:Montserrat,Inter,"Helvetica Neue",Arial,sans-serif;
-webkit-font-smoothing:antialiased}}
.fwrap{{position:absolute;inset:0;overflow:hidden}}
.frame{{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover}}
.grain{{position:absolute;inset:0;mix-blend-mode:overlay;opacity:.10;
background-image:url("{_GRAIN_SVG}");background-size:260px 260px}}
.vig{{position:absolute;inset:0;
background:radial-gradient(120% 78% at 50% 42%,rgba(0,0,0,0) 44%,rgba(4,8,14,.52) 100%)}}

/* субтитры: safe-зона снизу {SAFE_BOTTOM}px */
.cap{{position:absolute;left:{SAFE_SIDE}px;right:{SAFE_SIDE}px;bottom:{SAFE_BOTTOM}px;text-align:center;
color:#fff;font-size:67px;font-weight:800;line-height:1.14;letter-spacing:-0.5px;
text-shadow:0 4px 24px rgba(0,0,0,.85),0 0 2px rgba(0,0,0,.9)}}
.word{{display:inline-block;margin-right:.34em}}
/* transform:scale ударного слова не занимает места в потоке и наезжает на соседнее —
   компенсируем боковыми полями (поймано на прогоне 2026-08-12: «problemyżołądkowe») */
.word.emph{{font-weight:900;padding:0 .10em;margin-right:.42em}}
/* Обнуление правого поля идёт ПОСЛЕ .word.emph: у них одинаковая специфичность, и при
   обратном порядке ударное слово в конце строки сохраняло хвостовое поле — строка
   уезжала влево на его величину. */
.word:last-child,.word.emph:last-child{{margin-right:0}}

/* постер кадра-0 */
.headline{{position:absolute;left:56px;right:56px;top:{SAFE_TOP + 60}px;text-align:center;color:#fff;
font-weight:900;line-height:1.05;letter-spacing:-1.5px;
text-shadow:0 6px 34px rgba(0,0,0,.92),0 2px 6px rgba(0,0,0,.95)}}
.scrim{{position:absolute;left:0;right:0;top:0;height:820px;
background:linear-gradient(180deg,rgba(5,9,16,.72) 0%,rgba(5,9,16,.46) 54%,rgba(5,9,16,0) 100%)}}
.hl{{color:var(--yellow)}}

/* ---- слой информационной графики ---- */
.ov{{position:absolute;left:{SAFE_SIDE + 20}px;right:{SAFE_SIDE + 20}px;top:820px;
color:#fff;text-align:center}}
.ov-stat .statnum{{font-size:232px;font-weight:900;line-height:.95;letter-spacing:-6px;
color:var(--yellow);text-shadow:0 10px 40px rgba(0,0,0,.75)}}
.ov-stat .unit{{font-size:100px;margin-left:10px;letter-spacing:-2px}}
.ov-stat .statlab{{margin-top:16px;font-size:56px;font-weight:800;color:#fff;
text-shadow:0 4px 20px rgba(0,0,0,.85)}}

.ov-bar{{padding:0 10px}}
.barlab{{display:flex;justify-content:space-between;align-items:baseline;font-size:48px;
font-weight:800;margin-bottom:16px;text-shadow:0 4px 18px rgba(0,0,0,.85)}}
.barval{{color:var(--yellow);font-size:60px;font-weight:900}}
.bartrack{{height:46px;background:rgba(10,16,24,.72);border-radius:23px;overflow:hidden;
box-shadow:0 6px 26px rgba(0,0,0,.5)}}
.barfill{{height:100%;background:linear-gradient(90deg,var(--green),#8BD98F);border-radius:23px}}

.vs{{display:flex;align-items:stretch;gap:18px}}
.vscol{{flex:1;background:rgba(10,18,28,.80);border-radius:22px;padding:26px 14px 22px;
border:5px solid rgba(255,255,255,.14)}}
.vscol.win{{border-color:var(--green);background:rgba(18,52,32,.84)}}
.vsval{{font-size:72px;font-weight:900;color:var(--yellow);line-height:1}}
.vscol.win .vsval{{color:#8BD98F}}
.vslab{{font-size:38px;font-weight:700;margin-top:10px;line-height:1.15;color:#EAF0F6}}
.vsmid{{align-self:center;font-size:44px;font-weight:900;opacity:.85}}

.lhead{{font-size:50px;font-weight:900;margin-bottom:18px;
text-shadow:0 4px 18px rgba(0,0,0,.85)}}
.lrow{{display:flex;align-items:center;gap:18px;text-align:left;
background:rgba(10,18,28,.78);border-radius:18px;padding:18px 26px;margin-bottom:14px;
font-size:46px;font-weight:800;line-height:1.1}}
.lrow .lmark{{font-size:52px;font-weight:900;min-width:52px;text-align:center}}
.lrow.ok .lmark{{color:var(--green)}}
.lrow.no .lmark{{color:#FF6B5A}}

.ov-callout .cotext{{display:inline-block;background:var(--yellow);color:var(--ink);
font-size:58px;font-weight:900;line-height:1.12;padding:20px 34px;border-radius:16px;
box-shadow:0 14px 40px rgba(0,0,0,.55);letter-spacing:-1px}}
.ov-callout .hl{{color:var(--navy)}}

.ov-stamp{{top:700px}}
.ov-stamp .stamptext{{display:inline-block;border:11px solid #FF5B47;color:#FF5B47;
font-weight:900;letter-spacing:4px;padding:14px 36px;border-radius:14px;max-width:100%;
text-transform:uppercase;background:rgba(8,12,20,.34);
text-shadow:0 4px 18px rgba(0,0,0,.7)}}

.tlwrap{{position:relative;height:150px;margin-top:26px}}
.tlline{{position:absolute;left:4%;right:4%;top:26px;height:8px;border-radius:4px;
background:rgba(255,255,255,.35)}}
.tlmark{{position:absolute;top:0;transform:translateX(-50%);width:210px;text-align:center}}
.tldot{{display:block;width:34px;height:34px;border-radius:50%;background:var(--yellow);
margin:13px auto 0;box-shadow:0 0 0 8px rgba(42,92,130,.55)}}
.tllab{{display:block;margin-top:12px;font-size:36px;font-weight:800;line-height:1.1;
text-shadow:0 3px 14px rgba(0,0,0,.85)}}

/* атрибуция: маленькая, намеренно незаметная — сигнал доверия, а не элемент дизайна */
.ov-source{{top:1225px}}
.ov-source .srctext{{display:inline-block;background:rgba(8,14,22,.66);color:#CBD8E4;
font-size:30px;font-weight:600;letter-spacing:.4px;padding:9px 20px;border-radius:8px;
border-left:6px solid var(--green)}}

/* payoff-карточка: кадр 0 + затемнение, поверх — вывод (петля «конец = начало») */
.poframe{{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover}}
/* затемнение подобрано так, чтобы кадр читался как кадр, а не как фон под текстом:
   узнаваемость первого кадра — половина смысла петли. Читаемость держит тень текста. */
.pocard{{position:absolute;inset:0;
background:linear-gradient(165deg,rgba(20,44,66,.58) 0%,rgba(12,30,46,.70) 52%,
rgba(8,20,32,.80) 100%)}}
.potext{{position:absolute;left:80px;right:80px;top:{SAFE_TOP}px;bottom:{SAFE_BOTTOM - 40}px;
display:flex;align-items:center;justify-content:center}}
.poinner{{width:100%;text-align:center;color:#fff;font-weight:900;line-height:1.12;
letter-spacing:-1.5px;overflow-wrap:break-word;
text-shadow:0 6px 32px rgba(0,0,0,.92),0 2px 8px rgba(0,0,0,.95),0 0 3px rgba(0,0,0,.9)}}
.potext .hl{{color:#8BD98F}}
"""


def _build_html(frame_spans, motions, beat_words, fallback_captions, beat_starts, beat_durs,
                overlays, total, headline, headline_dur, payoff_text, payoff_start,
                emphases) -> tuple[str, list]:
    fc, ft, punches = _frame_clips(frame_spans, motions, beat_starts, beat_durs, total)
    oc, ot, ov_sfx = _overlay_clips(overlays, beat_starts, beat_durs, len(beat_starts))
    cc, ct = _caption_clips(beat_words, fallback_captions, beat_starts, beat_durs, emphases)
    hc, ht = _headline_clip(headline, headline_dur)
    pc, pt = _payoff_clip(payoff_text, payoff_start, total)
    texture = [f'<div id="vig" class="clip vig" data-start="0.000" data-duration="{total:.3f}" '
               f'data-track-index="2"></div>',
               f'<div id="grain" class="clip grain" data-start="0.000" data-duration="{total:.3f}" '
               f'data-track-index="12"></div>']
    clips = fc + texture[:1] + oc + cc + hc + pc + texture[1:]
    tweens = ft + ot + ct + ht + pt
    html = f"""<!doctype html>
<html lang="pl"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{_CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}"
     data-width="1080" data-height="1920">
{chr(10).join('  ' + c for c in clips)}
</div>
<script>
window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
{chr(10).join(tweens)}
window.__timelines["main"]=tl;
</script></body></html>
"""
    return html, (punches, ov_sfx)


# --- звук -----------------------------------------------------------------------
# Карта SFX → файл бандла. Уровни — из research/62 §1, приглушены на 3-4дБ под спокойный
# тон канала (там ориентир на «энергичный» монтаж, у нас wellness).
SFX_PROFILES: dict[str, dict] = {
    # Профиль решает ДВА вопроса: на какие события ставить звук и насколько громко.
    #
    # ⚠️ Значение — не «приглушить на N дБ», а **целевой пик в готовом миксе (dBFS)**.
    # Так пришлось сделать после 2026-08-12: сэмплы бандла лежат на РАЗНЫХ уровнях
    # (у `impact-bass-1` пик −0.4 дБ, у `ping` средний −34.7 дБ), и одинаковое
    # приглушение давало то удар в лицо, то полную тишину. Владелец услышал второе:
    # «звуков вообще не было». Теперь каждый сэмпл сначала измеряется, а потом
    # приводится к целевому пику — цифра в таблице означает одно и то же для всех файлов.
    #
    # Ориентир (откалиброван на слух 2026-08-12 по колокольчику payoff — единственному
    # звуку, который владелец слышал отчётливо; он был на −17, но звучал в обрыве музыки,
    # где ему ничто не мешает. Всё, что конкурирует с речью и музыкой, должно быть громче):
    #   −19 — фактура, слышно, но не отвлекает
    #   −15 — заметный акцент под речью
    #   −11 — удар, который слышно как удар
    "none": {},

    "minimal": {
        "turn":   ("impact-bass-1.mp3", -11.0),
        "payoff": ("chime.mp3", -10.0),
    },

    "soft": {
        "overlay:*":     ("click-soft.mp3", -16.0),
        "overlay:stamp": ("impact-bass-2.mp3", -14.0),
        "turn":          ("impact-bass-1.mp3", -14.0),
        "payoff":        ("chime.mp3", -12.0),
    },

    "data": {
        # У профиля ОБЯЗАН быть фолбэк `overlay:*`, иначе часть графики появляется молча.
        # Так и было до 2026-08-12: в ролике про железо звучали 4 события из 15 — три
        # callout и два list не имели звука вовсе, и это владелец услышал как «звуков нет».
        #
        # Уровни выровнены между собой: тихие сэмплы (ping, chime) звучат короче и мягче
        # ударов, поэтому при равной цифре в dBFS слышны заметно слабее. Замер 2026-08-12
        # показал, что ping на −15 и chime на −14 тонули в речи, пока удары на −11/−12
        # читались отчётливо, — подтянуты к тому же уровню.
        "overlay:*":      ("click-soft.mp3", -14.0),
        "overlay:stat":   ("ping.mp3", -10.0),
        "overlay:bar":    ("ping.mp3", -11.0),
        "overlay:versus": ("ping.mp3", -11.0),
        "overlay:stamp":  ("impact-bass-2.mp3", -12.0),
        "turn":           ("impact-bass-1.mp3", -11.0),
        "payoff":         ("chime.mp3", -10.0),
    },

    "dense": {
        "frame_cut":     ("whoosh-short.mp3", -18.0),
        "overlay:*":     ("pop.mp3", -15.0),
        "overlay:stamp": ("impact-bass-2.mp3", -11.0),
        "turn":          ("impact-bass-1.mp3", -9.0),
        "payoff":        ("chime.mp3", -13.0),
    },
}
DEFAULT_SFX_PROFILE = "data"


_PEAK_CACHE: dict[str, float] = {}


def _peak_dbfs(path: Path) -> float:
    """Пиковый уровень файла. Нужен, чтобы привести разношёрстные сэмплы бандла к одному
    целевому уровню в миксе. Измеряем один раз на файл за процесс."""
    key = str(path)
    if key in _PEAK_CACHE:
        return _PEAK_CACHE[key]
    proc = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
                           "-af", "volumedetect", "-f", "null", "-"],
                          capture_output=True, text=True)
    peak = 0.0
    for line in proc.stderr.splitlines():
        if "max_volume:" in line:
            try:
                peak = float(line.split("max_volume:")[1].strip().split()[0])
            except (IndexError, ValueError):
                peak = 0.0
    _PEAK_CACHE[key] = peak
    return peak


def _sfx_plan(profile: str, events: list[tuple[float, str]]) -> list[tuple[float, str, float]]:
    """Семантические события → (время, файл, ЦЕЛЕВОЙ ПИК в dBFS) по выбранному профилю.
    `overlay:*` — фолбэк для видов графики, у которых нет отдельной записи."""
    table = SFX_PROFILES.get(profile, SFX_PROFILES[DEFAULT_SFX_PROFILE])
    out = []
    for t, ev in events:
        hit = table.get(ev)
        if hit is None and ev.startswith("overlay:"):
            hit = table.get("overlay:*")
        if hit:
            out.append((t, hit[0], hit[1]))
    return out


def _stage_sfx(work_dir: Path, filenames: set[str]) -> dict[str, Path]:
    """Копирует нужные SFX из бандла скилла в папку прогона. Если бандла нет — возвращает
    то, что удалось найти; сборка просто соберётся без этих акцентов."""
    out: dict[str, Path] = {}
    dest = work_dir / "sfx"
    dest.mkdir(parents=True, exist_ok=True)
    for fname in filenames:
        src = SFX_SRC / fname
        if src.exists():
            dst = dest / fname
            if not dst.exists():
                shutil.copy2(src, dst)
            out[fname] = dst
    return out


def _mix_audio(video_mp4: Path, voice_wav: Path, out_mp4: Path, total: float,
               sfx_plan: list[tuple[float, str, float]], bgm_wav: Path | None,
               work_dir: Path, duck_from: float | None) -> None:
    """Микс: голос (доминанта) + BGM с ducking'ом + SFX по меткам времени.
    `duck_from` — момент «music stop» перед payoff: музыка уходит в ноль, чтобы вывод
    прозвучал в тишине (research/62 §5), и возвращается на финальной карточке."""
    files = _stage_sfx(work_dir, {f for _, f, _ in sfx_plan})
    events = [(t, f, g) for t, f, g in sfx_plan if f in files]

    # inputs: 0=video, 1=voice, [2=bgm], далее по одному входу на каждый SFX
    inputs = ["-i", str(video_mp4), "-i", str(voice_wav)]
    parts: list[str] = []
    mix_labels: list[str] = []

    has_bgm = bool(bgm_wav and Path(bgm_wav).exists())

    # Голос — доминанта, но нормализуем его НИЖЕ финальной цели, чтобы в миксе остался
    # запас под SFX. До 2026-08-12 голос шёл сразу на −14 LUFS / −1.5 dBTP, впритык к
    # потолку лимитера: любой звук, попавший на громкую фразу, лимитер съедал целиком.
    # Снаружи это выглядело как «часть звуков не слышно» — тихие места звучали, громкие нет.
    # Финальную громкость набирает уже вся сумма (см. конец функции).
    # asplit нужен потому, что голос используется дважды: в миксе и как сайдчейн для ducking'а.
    voice_chain = ("[1:a]acompressor=threshold=-18dB:ratio=3:attack=8:release=140,"
                   "loudnorm=I=-17:TP=-4:LRA=11")
    parts.append(voice_chain + ("[vsplit]" if has_bgm else "[voc]"))
    if has_bgm:
        parts.append("[vsplit]asplit=2[voc][vocsc]")
    mix_labels.append("[voc]")

    idx = 2
    if has_bgm:
        inputs += ["-stream_loop", "-1", "-i", str(bgm_wav)]
        vol = "volume=-23dB"
        if duck_from is not None and duck_from > 1.0:
            # music stop перед payoff: музыка почти в ноль, вывод звучит в тишине (research/62 §5)
            vol += (f",volume=enable='between(t,{duck_from:.2f},{duck_from + 1.6:.2f})'"
                    f":volume=0.03")
        fade_out = max(total - 0.9, 0.0)
        parts.append(f"[{idx}:a]{vol},atrim=0:{total:.3f},asetpts=N/SR/TB,"
                     f"afade=t=in:st=0:d=0.8,afade=t=out:st={fade_out:.3f}:d=0.9[bgraw]")
        # ducking: музыка проседает ровно на время речи и возвращается в паузах
        parts.append("[bgraw][vocsc]sidechaincompress=threshold=0.045:ratio=7:"
                     "attack=12:release=340[bgd]")
        mix_labels.append("[bgd]")
        idx += 1

    for n, (t, fname, target_dbfs) in enumerate(events):
        src = files[fname]
        inputs += ["-i", str(src)]
        delay_ms = int(max(t, 0.0) * 1000)
        # приводим сэмпл к целевому пику: сколько не хватает до него от измеренного
        gain = target_dbfs - _peak_dbfs(src)
        parts.append(f"[{idx}:a]volume={gain:.1f}dB,aresample=48000,"
                     f"adelay={delay_ms}|{delay_ms},atrim=0:{total:.3f}[s{n}]")
        mix_labels.append(f"[s{n}]")
        idx += 1

    parts.append(f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:duration=first:"
                 f"normalize=0[aout]")
    fc = ";".join(parts)

    # --- проход 1: сводим звук как есть, БЕЗ нормализации ---------------------------
    # Однопроходный `loudnorm` ведёт усиление динамически и по-разному в разных вариантах
    # микса: в замерах 2026-08-12 он локально ГАСИЛ отдельные SFX, из-за чего казалось,
    # что часть звуков не попала в сборку (на деле слой SFX был полным). Двухпроходная
    # схема — измерили сумму, применили ПОСТОЯННЫЙ gain — и от этого артефакта избавляет,
    # и делает громкость воспроизводимой от прогона к прогону.
    raw = Path(work_dir) / "mix_raw.wav"
    p1 = subprocess.run(["ffmpeg", "-y"] + inputs + [
        "-filter_complex", fc, "-map", "[aout]", "-c:a", "pcm_s16le", str(raw)],
        capture_output=True, text=True)
    if p1.returncode != 0:
        print(f"[WARN] микс со звуковым дизайном не собрался, фолбэк на голос.\n"
              f"{p1.stderr.strip()[-700:]}")
        subprocess.run(["ffmpeg", "-y", "-i", str(video_mp4), "-i", str(voice_wav),
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact",
                        str(out_mp4)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return

    # --- проход 2: измеряем сумму и добираем громкость постоянным усилением ----------
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(raw),
                           "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
    lufs = None
    for line in meas.stderr.splitlines():
        t = line.strip()
        if t.startswith("I:") and "LUFS" in t:
            try:
                lufs = float(t.split()[1])
            except (IndexError, ValueError):
                pass
    gain_db = 0.0 if lufs is None else max(min(-14.0 - lufs, 12.0), -12.0)
    cmd = ["ffmpeg", "-y", "-i", str(video_mp4), "-i", str(raw),
           # level=0 обязателен: по умолчанию alimiter САМ подтягивает сигнал к потолку,
           # и понижение limit делало микс громче, а не тише. 0.89 ≈ −1 dBFS — таргет
           # True Peak платформ плюс запас на овершут AAC.
           "-af", f"volume={gain_db:.2f}dB,alimiter=limit=0.89:level=0",
           "-map", "0:v", "-map", "1:a",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
           "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact",
           str(out_mp4)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        # звук не должен ронять прогон: падаем на простой мукс голоса
        print(f"[WARN] микс со звуковым дизайном не собрался, фолбэк на голос.\n"
              f"{proc.stderr.strip()[-700:]}")
        subprocess.run(["ffmpeg", "-y", "-i", str(video_mp4), "-i", str(voice_wav),
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact",
                        str(out_mp4)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def build_and_render(frames: list[Path], frame_spans, motions, beat_words, fallback_captions,
                     beat_durs, overlays, emphases, voice_wav: Path, out_mp4: Path,
                     work_dir: Path, headline: str = "", payoff_text: str = "",
                     turn_beat_idx: int | None = None, bgm_wav: Path | None = None,
                     sfx_profile: str = DEFAULT_SFX_PROFILE) -> Path:
    """Собирает HTML, рендерит через hyperframes и микширует звук.

    frame_spans — [(beat_from, beat_to), ...] по одному на кадр; длина == len(frames).
    beat_durs   — фактические длительности битов из TTS (они ведут всю шкалу времени).
    overlays    — объекты schemas_v7.Overlay.
    """
    work_dir = Path(work_dir)
    assets = work_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for i, p in enumerate(frames):
        shutil.copy(p, assets / f"frame{i}.png")
    (work_dir / "hyperframes.json").write_text(json.dumps(_HF_JSON, indent=2), encoding="utf-8")
    (work_dir / "meta.json").write_text(
        json.dumps({"id": work_dir.name, "name": work_dir.name}), encoding="utf-8")

    beat_durs = [float(d) for d in beat_durs]
    total = sum(beat_durs)
    beat_starts, t = [], 0.0
    for d in beat_durs:
        beat_starts.append(t)
        t += d

    motions = list(motions)
    if motions:
        motions[0] = "hook_punch"

    headline_dur = 0.0
    if headline.strip() and beat_durs:
        headline_dur = beat_durs[0] + (beat_durs[1] if len(beat_durs) > 1 else 0)
        if len(beat_durs) > 2:
            headline_dur += beat_durs[2] / 2
        headline_dur = min(headline_dur, 4.2)

    # payoff-карточка занимает последний бит (и предпоследний, если он короткий)
    payoff_start = beat_starts[-1] if beat_starts else 0.0
    if len(beat_durs) >= 2 and beat_durs[-1] < 1.6:
        payoff_start = beat_starts[-2]

    html, (punches, ov_sfx) = _build_html(
        frame_spans, motions, beat_words, fallback_captions, beat_starts, beat_durs,
        overlays, total, headline, headline_dur, payoff_text, payoff_start, emphases)
    (work_dir / "index.html").write_text(html, encoding="utf-8")

    subprocess.run(["npx", "--yes", "hyperframes", "render", "-o", "video.mp4"],
                   cwd=str(work_dir), check=True, env=_node22_env())

    # --- звуковые события (семантические; в файлы их превращает профиль) ---
    events = sfx_events(frame_spans, beat_starts, ov_sfx, turn_beat_idx, payoff_start)
    (work_dir / "sfx_events.json").write_text(
        json.dumps({"total": total, "payoff_start": payoff_start, "events": events},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    mix(work_dir / "video.mp4", voice_wav, Path(out_mp4), total, events, bgm_wav, work_dir,
        payoff_start, profile=sfx_profile)
    return Path(out_mp4)


def sfx_events(frame_spans, beat_starts, ov_sfx, turn_beat_idx, payoff_start
               ) -> list[tuple[float, str]]:
    """Семантические звуковые события ролика — БЕЗ привязки к конкретным файлам.
    Разделение нужно, чтобы одну и ту же сборку можно было переозвучить другим профилем,
    не перерисовывая видео (`mix` на готовом `hf/video.mp4`)."""
    ev: list[tuple[float, str]] = []
    for i, (b_from, _) in enumerate(frame_spans):
        if i:
            ev.append((max(beat_starts[b_from] - 0.06, 0.0), "frame_cut"))
    ev += [(t, k) for t, k in ov_sfx]
    if turn_beat_idx is not None and 0 <= turn_beat_idx < len(beat_starts):
        ev.append((beat_starts[turn_beat_idx] - 0.05, "turn"))
    if payoff_start > 1.0:
        ev.append((payoff_start, "payoff"))
    return [(round(max(t, 0.0), 3), k) for t, k in ev]


def mix(video_mp4: Path, voice_wav: Path, out_mp4: Path, total: float,
        events: list[tuple[float, str]], bgm_wav: Path | None, work_dir: Path,
        payoff_start: float, profile: str = DEFAULT_SFX_PROFILE) -> Path:
    """Собирает звук поверх УЖЕ отрендеренного видео. Отдельная функция, чтобы менять
    звуковой профиль стоило секунды, а не полного повторного рендера."""
    plan = _sfx_plan(profile, events)
    # «Music stop» перед выводом имеет смысл только когда музыка вообще есть.
    duck = (payoff_start - 0.5) if (bgm_wav and payoff_start > 1.0) else None
    _mix_audio(video_mp4, voice_wav, Path(out_mp4), total, plan, bgm_wav, work_dir, duck)
    return Path(out_mp4)
