#!/usr/bin/env python3
"""assembly_layers.py — сборка «живого коллажа»: вырезки как отдельные слои (T2, v6-layers).

Отличие от `autopilot_factory/assembly.py`: там один `<img>` на бит и движение = Ken Burns
всего кадра. Здесь у бита ПЛОСКИЙ бумажный фон + несколько вырезок-слоёв, и движется каждая
вырезка отдельно — влёт, «шлепок», оседание, покачивание, параллакс. Видео-модель не нужна:
всё рисует тот же GSAP в той же HTML-композиции hyperframes.

Файл АДДИТИВНЫЙ: `assembly.py` не правится. Типографику (плашки, караоке-маркер, растр/зерно)
переиспользуем импортом из него — дублировать 200 строк CSS было бы источником расхождения.

Кейфрейм-словарь портирован из vox-director (`motion.py`): fly_in / slap / drop / pop_settle
плюс «дыхание» осевших элементов. Единственное изменение — `repeat` конечный, а не `-1`:
hyperframes рендерит перемоткой по таймлайну, и бесконечный повтор — лишний риск
недетерминизма (см. ARCHITECTURE §5).
"""
from __future__ import annotations
import json
import math
import shutil
import subprocess
from pathlib import Path

import assembly as _a   # прод-модуль; только читаем из него, не меняем

W, H = 1080, 1920

# Порядок слоёв. hyperframes раскладывает клипы по трекам, но стек мы задаём z-index'ом сами —
# так поведение не зависит от того, как CLI трактует track-index.
_Z = {"bg": 1, "scrap": 4, "el": 10, "cap": 30, "headline": 40, "cta": 50,
      "halftone": 60, "grain": 70}
_TRACK = {"bg": 1, "cap": 2, "headline": 4, "cta": 5, "halftone": 6, "grain": 7, "scrap": 8}
_EL_TRACK0 = 10          # у каждого слота вырезки свой трек: внутри бита они звучат ОДНОВРЕМЕННО

# --- процедурная «бумажная мебель» ------------------------------------------------
# Без неё вырезки висят островками на плоском цвете и читаются как клипарт, а не коллаж
# (рендер-проверка 2026-08-05). Обрывки цветной бумаги, газетные полосы и полоски скотча
# рисуются CSS'ом — это $0, в отличие от того, чтобы просить их у модели на каждом кадре.
# Раскладка детерминирована индексом бита: повторный рендер даёт тот же кадр (ARCHITECTURE §5).
_SCRAP_COLORS = ["#4CAF50", "#4CAF50", "#E8A33D", "#F2EAD8"]
_SCRAP_SHAPE = "polygon(2% 8%,38% 0%,72% 6%,100% 2%,96% 62%,100% 96%,54% 100%,18% 94%,0% 98%)"
_TAPE_COLOR = "rgba(238,230,208,.82)"


def _lcg(seed: int):
    """Мини-ГПСЧ: одинаковый бит → одинаковая раскладка, без зависимости от random.seed()."""
    x = (seed * 1103515245 + 12345) & 0x7FFFFFFF

    def nxt(lo: float, hi: float) -> float:
        nonlocal x
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        return lo + (hi - lo) * (x / 0x7FFFFFFF)
    return nxt


def _furniture(i: int, t0: float, d: float, count: int) -> tuple[list[str], list[str]]:
    """Обрывки + газетные полосы + скотч для бита i. Держим их ВЫШЕ зоны субтитров
    (нижние ~22% холста) — иначе бумажный мусор лезет под плашку и мешает читать.
    Возвращает (клипы, твины): совсем неподвижные обрывки выдают статичную подложку, поэтому
    каждому даётся медленный дрейф с индивидуальным периодом."""
    if count <= 0:
        return [], []
    rnd = _lcg(i * 977 + 13)
    out: list[str] = []
    tw: list[str] = []
    for k in range(count):
        w = rnd(90, 230)
        h = w * rnd(0.35, 0.95)
        x = rnd(-40, W - 60)
        y = rnd(60, H * 0.72)
        rot = rnd(-28, 28)
        col = _SCRAP_COLORS[int(rnd(0, len(_SCRAP_COLORS) - 0.001))]
        out.append(
            f'<div id="s{i}_{k}" class="clip scrap" style="width:{w:.0f}px;height:{h:.0f}px;'
            f'left:{x:.0f}px;top:{y:.0f}px;background:{col};rotate:{rot:.1f}deg" '
            f'data-start="{t0:.3f}" data-duration="{d:.3f}" '
            f'data-track-index="{_TRACK["scrap"]}"></div>')
    # одна газетная полоса на бит: полоски «строк» рисуются градиентом, читаемых слов нет
    nw, nh = rnd(150, 300), rnd(60, 130)
    out.append(
        f'<div id="n{i}" class="clip newsprint" style="width:{nw:.0f}px;height:{nh:.0f}px;'
        f'left:{rnd(-30, W - 120):.0f}px;top:{rnd(80, H * 0.68):.0f}px;'
        f'rotate:{rnd(-20, 20):.1f}deg" data-start="{t0:.3f}" data-duration="{d:.3f}" '
        f'data-track-index="{_TRACK["scrap"]}"></div>')
    # две полоски скотча — они и «крепят» коллаж к листу
    for k in range(2):
        out.append(
            f'<div id="tp{i}_{k}" class="clip tape" style="width:{rnd(90, 170):.0f}px;'
            f'height:{rnd(26, 40):.0f}px;left:{rnd(0, W - 140):.0f}px;'
            f'top:{rnd(100, H * 0.70):.0f}px;rotate:{rnd(-45, 45):.1f}deg" '
            f'data-start="{t0:.3f}" data-duration="{d:.3f}" '
            f'data-track-index="{_TRACK["scrap"]}"></div>')
    # дрейф: у каждого куска свой период, иначе вся «мебель» качается одним слоем
    for sel in ([f"#s{i}_{k}" for k in range(count)] + [f"#n{i}"]
                + [f"#tp{i}_{k}" for k in range(2)]):
        period = rnd(2.4, 4.2)
        cycles = max(int(math.ceil(d / period)), 1)
        tw.append(f'tl.to("{sel}",{{xPercent:{rnd(-7, 7):.1f},yPercent:{rnd(-7, 7):.1f},'
                  f'duration:{period:.2f},ease:"sine.inOut",repeat:{cycles},yoyo:true}},{t0:.3f});')
    return out, tw


def _enter_tween(sel: str, t0: float, kind: str, rot: float) -> str:
    """Вход элемента. Всё — от края холста или «в фокус», без морфинга: бумага жёсткая."""
    if kind == "none":
        return ""
    if kind == "pop":       # появление в фокусе: крупнее → на место. Не уезжает за кадр.
        return (f'tl.fromTo("{sel}",{{opacity:0,scale:1.35,rotation:{rot + 6:.1f}}},'
                f'{{opacity:1,scale:1,rotation:{rot:.1f},duration:0.42,ease:"power3.out"}},{t0:.3f});')
    if kind == "slap":      # резкий «шлепок» — под акцентный бит
        return (f'tl.fromTo("{sel}",{{opacity:0,scale:1.6,rotation:{rot:.1f}}},'
                f'{{opacity:1,scale:1,rotation:{rot:.1f},duration:0.22,ease:"back.out(2.2)"}},{t0:.3f});')
    if kind == "drop":      # падение сверху с отскоком
        return (f'tl.fromTo("{sel}",{{opacity:1,yPercent:-260,rotation:{rot - 8:.1f}}},'
                f'{{yPercent:0,rotation:{rot:.1f},duration:0.72,ease:"bounce.out"}},{t0:.3f});')
    axis = {"fly_in_left": ("xPercent", -420), "fly_in_right": ("xPercent", 420),
            "fly_in_top": ("yPercent", -420), "fly_in_bottom": ("yPercent", 420)}
    prop, off = axis.get(kind, ("xPercent", -420))
    return (f'tl.fromTo("{sel}",{{opacity:1,{prop}:{off},rotation:{rot - 10:.1f}}},'
            f'{{{prop}:0,rotation:{rot:.1f},duration:0.62,ease:"back.out(1.4)"}},{t0:.3f});')


# Длительность каждого входа — покачивание обязано стартовать ПОСЛЕ него. Иначе снос по
# xPercent/yPercent наложится на fly_in/drop, которые анимируют те же свойства, и на стыке
# будет рывок: при наложении GSAP отдаёт свойство более позднему твину.
_ENTER_DUR = {"none": 0.0, "pop": 0.42, "slap": 0.22, "drop": 0.72,
              "fly_in_left": 0.62, "fly_in_right": 0.62, "fly_in_top": 0.62,
              "fly_in_bottom": 0.62}


def _breathe_tween(sel: str, start: float, dur: float, seed: int, rot: float) -> list[str]:
    """Осевшая вырезка не должна быть мёртвой: покачивание + снос + «дыхание» масштаба.

    Амплитуды подняты по замечанию владельца 2026-08-05 («объекты не должны находиться в
    статике»): в первой версии крен был 0.9–1.6°, чего на глаз практически не видно.
    Сейчас 2.2–4.0° плюс снос на ±1.5–3% — движение читается, но остаётся «бумажным»,
    без ощущения плавающего в воде объекта.

    Три оси намеренно имеют РАЗНЫЕ периоды (крен / снос / масштаб): при совпадающих периодах
    движение выглядит механическим маятником, при несовпадающих — живым дрейфом бумаги."""
    if dur < 0.8:
        return []
    period = 2.0 + (seed % 5) * 0.31
    amp = 2.2 + (seed % 4) * 0.6
    dx = 1.5 + (seed % 3) * 0.75
    dy = 1.5 + ((seed + 2) % 3) * 0.75
    sign = 1 if seed % 2 == 0 else -1

    def cycles(p: float) -> int:
        return max(int(math.ceil(dur / p)), 1)

    p2, p3 = period * 1.37, period * 1.71
    return [
        (f'tl.to("{sel}",{{rotation:{rot + sign * amp:.2f},duration:{period:.2f},'
         f'ease:"sine.inOut",repeat:{cycles(period)},yoyo:true}},{start:.3f});'),
        (f'tl.to("{sel}",{{xPercent:{sign * dx:.2f},yPercent:{-sign * dy:.2f},'
         f'duration:{p2:.2f},ease:"sine.inOut",repeat:{cycles(p2)},yoyo:true}},{start:.3f});'),
        (f'tl.to("{sel}",{{scale:1.03,duration:{p3:.2f},'
         f'ease:"sine.inOut",repeat:{cycles(p3)},yoyo:true}},{start:.3f});'),
    ]


def _beat_clips(beats: list[dict], elem_paths: dict[str, str], starts: list[float],
                durs: list[float]) -> tuple[list[str], list[str], int]:
    """Фон + вырезки каждого бита. Возвращает (клипы, твины, макс. число вырезок на бит)."""
    clips, tweens = [], []
    max_el = 0
    for i, beat in enumerate(beats):
        t0, d = starts[i], durs[i]
        bg = beat.get("bg_color", "#2A5C82")
        clips.append(f'<div id="bg{i}" class="clip bg" style="background:{bg}" '
                     f'data-start="{t0:.3f}" data-duration="{d:.3f}" '
                     f'data-track-index="{_TRACK["bg"]}"></div>')
        if beat.get("backdrop"):
            clips.append(f'<img id="bd{i}" class="clip backdrop" src="assets/{beat["backdrop"]}" '
                         f'data-start="{t0:.3f}" data-duration="{d:.3f}" '
                         f'data-track-index="{_TRACK["bg"]}"/>')
            tweens.append(f'tl.fromTo("#bd{i}",{{scale:1.0}},{{scale:1.06,duration:{d:.3f},'
                          f'ease:"none"}},{t0:.3f});')

        fclips, ftweens = _furniture(i, t0, d, int(beat.get("scraps", 4)))
        clips += fclips
        tweens += ftweens

        els = beat.get("elements", [])
        max_el = max(max_el, len(els))
        # Ни один бит не имеет права начинаться с пустого холста. Влетающие входы (drop,
        # fly_in_*) прячут элемент за кадром на 0.6–0.7с: если ВСЕ элементы бита влетают, зритель
        # эти доли секунды смотрит на голый фон (рендер-проверка 2026-08-05, бит 3 на t=5.0).
        # Поэтому хотя бы один элемент бита обязан присутствовать с его первого кадра.
        _IN_PLACE = {"none", "pop", "slap"}
        present = [e for e in els
                   if e.get("enter", "pop") in _IN_PLACE and float(e.get("enter_at", 0.0)) <= 0.001]
        if els and not present:
            anchor = min(els, key=lambda e: float(e.get("enter_at", 0.0)))
            # у кадра-0 (обложка в ленте Shorts) даже мгновенного проявления быть не должно
            anchor["enter"] = "none" if i == 0 else "pop"
            anchor["enter_at"] = 0.0
        for j, el in enumerate(els):
            name = el["name"]
            src = elem_paths.get(name)
            if src is None:
                raise SystemExit(f"[layers] бит {i}: нет вырезки «{name}» — проверь sheets в плане")
            sel = f"#e{i}_{j}"
            wpx = int(float(el.get("w", 0.4)) * W)
            left = float(el["x"]) * W
            top = float(el["y"]) * H
            rot = float(el.get("rot", 0.0))
            z = _Z["el"] + int(el.get("z", j))
            # height:auto — ИНЛАЙНОМ, не классом: у `.clip` из hyperframes своя высота, и
            # правило в нашем <style> её не перебивало — вырезки растягивались по вертикали
            # (рендер-проверка 2026-08-05). Инлайн-стиль выигрывает у любого правила таблицы.
            clips.append(
                f'<img id="e{i}_{j}" class="clip el" src="assets/{Path(src).name}" '
                f'style="width:{wpx}px;height:auto;left:{left:.0f}px;top:{top:.0f}px;'
                f'z-index:{z}" data-start="{t0:.3f}" data-duration="{d:.3f}" '
                f'data-track-index="{_EL_TRACK0 + j}"/>')
            offset = float(el.get("enter_at", 0.0))
            enter_at = t0 + offset
            kind = el.get("enter", "pop")
            # Кадр-0 — обложка ролика в ленте Shorts: на t=0 он не имеет права быть пустым,
            # а `pop`/`slap` стартуют с opacity:0. Для остальных битов проявление за 0.2–0.4с
            # допустимо — там всё равно стык, — и якорь бита уже гарантирован проверкой выше.
            if i == 0 and offset <= 0.001 and kind != "none":
                kind = "none"
            tw = _enter_tween(sel, enter_at, kind, rot)
            if tw:
                tweens.append(tw)
            else:
                tweens.append(f'tl.set("{sel}",{{rotation:{rot:.1f}}},{t0:.3f});')
            if el.get("breathe", True):
                settled = enter_at + _ENTER_DUR.get(kind, 0.62) + 0.02
                tweens += _breathe_tween(sel, settled, max(t0 + d - settled, 0.0),
                                         seed=i * 7 + j, rot=rot)
    return clips, tweens, max_el


_LAYER_CSS = f"""
.bg{{position:absolute;inset:0;z-index:{_Z['bg']}}}
.backdrop{{position:absolute;inset:0;width:{W}px;height:{H}px;object-fit:cover;z-index:{_Z['bg']}}}
/* центрирование вырезки — отдельным свойством `translate`, а НЕ через transform:
   GSAP пишет свои твины в transform и затёр бы translate(-50%,-50%); индивидуальные
   свойства применяются до transform и потому с ним composable */
.el{{position:absolute;transform-origin:50% 50%;
translate:-50% -50%;filter:drop-shadow(9px 13px 0 rgba(9,14,22,.28))}}
.scrap{{position:absolute;z-index:{_Z['scrap']};clip-path:{_SCRAP_SHAPE};
box-shadow:6px 8px 0 rgba(9,14,22,.22)}}
.newsprint{{position:absolute;z-index:{_Z['scrap']};background:#EFE9DA;
background-image:repeating-linear-gradient(180deg,rgba(20,26,34,.42) 0 3px,transparent 3px 9px);
clip-path:{_SCRAP_SHAPE};box-shadow:6px 8px 0 rgba(9,14,22,.20)}}
.tape{{position:absolute;z-index:{_Z['scrap']};background:{_TAPE_COLOR};
box-shadow:3px 4px 0 rgba(9,14,22,.14)}}
.cap{{z-index:{_Z['cap']}}}
.headline{{z-index:{_Z['headline']}}}
.ctaplate{{z-index:{_Z['cta']}}}
.halftone{{z-index:{_Z['halftone']}}}
.grain{{z-index:{_Z['grain']}}}
"""


def build_html(beats: list[dict], elem_paths: dict[str, str], beat_words, fallback_captions,
               durs: list[float], cap_style, headline: str, headline_dur: float,
               cta_text: str, cta_start: float, total: float) -> str:
    starts, t = [], 0.0
    for d in durs:
        starts.append(t)
        t += float(d)
    bc, bt, _ = _beat_clips(beats, elem_paths, starts, durs)
    on_props, off_props = _a._KARAOKE["collage"]
    cc, ct = _a._caption_clips(beat_words, fallback_captions, starts, durs, cap_style,
                               on_props=on_props, off_props=off_props)
    hc, ht = _a._headline_clip(headline, headline_dur, skin="collage")
    xc, xt = _a._cta_clip(cta_text, cta_start, total, skin="collage")
    overlay = [f'<div id="halftone" class="clip halftone" data-start="0.000" '
               f'data-duration="{total:.3f}" data-track-index="{_TRACK["halftone"]}"></div>',
               f'<div id="grain" class="clip grain" data-start="0.000" '
               f'data-duration="{total:.3f}" data-track-index="{_TRACK["grain"]}"></div>']
    clips = bc + cc + hc + xc + overlay
    tweens = bt + ct + ht + xt
    return f"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width={W}, height={H}"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:{W}px;height:{H}px;overflow:hidden;background:#000}}
body{{font-family:Inter,Arial,sans-serif}}{_a._COLLAGE_CSS}{_LAYER_CSS}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}"
     data-width="{W}" data-height="{H}">
{chr(10).join('  ' + c for c in clips)}
</div>
<script>
window.__timelines=window.__timelines||{{}};
const tl=gsap.timeline({{paused:true}});
{chr(10).join(tweens)}
window.__timelines["main"]=tl;
</script></body></html>
"""


def build_and_render(beats, elem_paths, beat_words, fallback_captions, durs, cap_style,
                     voice_wav: Path, out_mp4: Path, work_dir: Path,
                     headline: str = "", cta_text: str = "",
                     bgm_wav: Path | None = None, bgm_gain_db: float = -21.0,
                     backdrops: dict[str, Path] | None = None) -> Path:
    work_dir = Path(work_dir)
    assets = work_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for src in elem_paths.values():
        shutil.copy(src, assets / Path(src).name)
    for name, src in (backdrops or {}).items():
        shutil.copy(src, assets / name)
    (work_dir / "hyperframes.json").write_text(json.dumps(_a._HF_JSON, indent=2), encoding="utf-8")
    (work_dir / "meta.json").write_text(
        json.dumps({"id": work_dir.name, "name": work_dir.name}), encoding="utf-8")

    total = sum(float(d) for d in durs)
    headline_dur = 0.0
    if headline.strip() and durs:
        headline_dur = float(durs[0]) + (float(durs[1]) / 3 if len(durs) > 1 else 0.0)
        headline_dur = min(headline_dur, 4.0)
    starts, t = [], 0.0
    for d in durs:
        starts.append(t)
        t += float(d)
    cta_start = starts[-1] if starts else 0.0

    (work_dir / "index.html").write_text(
        build_html(beats, elem_paths, beat_words, fallback_captions, durs, cap_style,
                   headline, headline_dur, cta_text, cta_start, total), encoding="utf-8")

    subprocess.run(["npx", "--yes", "hyperframes", "render", "-o", "video.mp4"],
                   cwd=str(work_dir), check=True, env=_a._node22_env())

    out_mp4 = Path(out_mp4)
    if bgm_wav and Path(bgm_wav).exists():
        fade_out_start = max(total - 0.9, 0.0)
        fc = (f"[2:a]volume={bgm_gain_db}dB,atrim=0:{total:.3f},"
              f"afade=t=in:st=0:d=0.6,afade=t=out:st={fade_out_start:.3f}:d=0.9[bg];"
              f"[1:a][bg]amix=inputs=2:duration=first:normalize=0[a]")
        subprocess.run(["ffmpeg", "-y", "-i", str(work_dir / "video.mp4"), "-i", str(voice_wav),
                        "-stream_loop", "-1", "-i", str(bgm_wav),
                        "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact",
                        str(out_mp4)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(["ffmpeg", "-y", "-i", str(work_dir / "video.mp4"), "-i", str(voice_wav),
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact",
                        str(out_mp4)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_mp4
