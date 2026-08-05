#!/usr/bin/env python3
"""
assembly.py — сборка ролика: HTML-композиция hyperframes (кадры + Ken Burns + субтитры) → рендер
в немой MP4, затем мукс озвучки через ffmpeg. Слой сборки — hyperframes (ARCHITECTURE.md §4).

Тайминг ведёт озвучка: `durations[i]` = реальная длина i-го бита (из per-beat TTS), поэтому
кадры и субтитры идеально синхронны с голосом. Формат — вертикаль 1080×1920.
"""
from __future__ import annotations
import os
import json
import shutil
import subprocess
from pathlib import Path
from html import escape


def _node22_env() -> dict:
    """hyperframes CLI требует Node 20+ (util.styleText); системный default через nvm на этой
    машине — v18. До 2026-07-13 хелпер жил только в engine._transcribe_words, а `hyperframes
    render` здесь запускался с системным PATH — сборка падала, если оператор не положил Node 22
    в PATH руками (memory: build-media-needs-node22-path). v2: сборка сама находит любой
    установленный Node>=20 под nvm и подсовывает его в PATH только своим subprocess'ам."""
    env = os.environ.copy()
    nvm_dir = Path.home() / ".nvm" / "versions" / "node"
    if nvm_dir.is_dir():
        candidates = sorted(
            (p for p in nvm_dir.iterdir() if p.is_dir() and p.name.startswith("v")),
            key=lambda p: tuple(int(x) for x in p.name.lstrip("v").split(".")),
            reverse=True,
        )
        for c in candidates:
            major = int(c.name.lstrip("v").split(".")[0])
            if major >= 20 and (c / "bin" / "node").exists():
                env["PATH"] = f"{c / 'bin'}:{env.get('PATH', '')}"
                break
    return env

_HF_JSON = {
    "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
    "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
    "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
}

# Frame.motion -> GSAP fromTo (Ken Burns/пан/зум). Возвращает строку tween для таймлайна.
def _motion_tween(sel: str, motion: str, start: float, dur: float) -> str:
    # v3: hook_punch — «удар» первых полсекунды (jolt в ленте останавливает свайп: движение
    # заметно сразу, в отличие от вялого линейного Ken Burns), затем медленный дозум.
    punch = min(0.55, dur / 2)
    m = {
        "ken_burns_in":  f'tl.fromTo("{sel}",{{scale:1.0}},{{scale:1.10,duration:{dur},ease:"none"}},{start});',
        "ken_burns_out": f'tl.fromTo("{sel}",{{scale:1.10}},{{scale:1.0,duration:{dur},ease:"none"}},{start});',
        "pan_left":      f'tl.fromTo("{sel}",{{scale:1.08,xPercent:3}},{{xPercent:-3,duration:{dur},ease:"none"}},{start});',
        "pan_right":     f'tl.fromTo("{sel}",{{scale:1.08,xPercent:-3}},{{xPercent:3,duration:{dur},ease:"none"}},{start});',
        "parallax":      f'tl.fromTo("{sel}",{{scale:1.06,yPercent:2}},{{yPercent:-2,duration:{dur},ease:"none"}},{start});',
        "static_hold":   f'tl.fromTo("{sel}",{{scale:1.01}},{{scale:1.04,duration:{dur},ease:"none"}},{start});',
        "hook_punch":    (f'tl.fromTo("{sel}",{{scale:1.16}},{{scale:1.05,duration:{punch:.3f},ease:"power2.out"}},{start});'
                          f'tl.to("{sel}",{{scale:1.10,duration:{max(dur - punch, 0.1):.3f},ease:"none"}},{start + punch:.3f});'),
    }
    return m.get(motion, m["ken_burns_in"])


def _seq_clips(kind: str, items, durs, motions, total):
    """Раскладывает кадры последовательно по своей дорожке.
    Кадры и субтитры имеют НЕЗАВИСИМЫЕ тайминги, но обе дорожки покрывают один и тот же total."""
    clips, tweens = [], []
    t = 0.0  # накапливаем в полной точности...
    n = len(items)
    for i in range(n):
        d = float(durs[i]) if i < len(durs) else (total / n)
        t_r = round(t, 3)  # ...но раскладываем/сравниваем по округлённому — иначе независимое
        d_r = round(d, 3)  # округление start/duration соседних клипов даёт наложение в 1мс
        clips.append(
            f'<img id="f{i}" class="clip frame" src="assets/frame{i}.png" '
            f'data-start="{t_r:.3f}" data-duration="{d_r:.3f}" data-track-index="1"/>'
        )
        mo = motions[i] if i < len(motions) else "ken_burns_in"
        tweens.append(_motion_tween(f"#f{i}", mo, t_r, d_r))
        t = t_r + d_r
    return clips, tweens


def _chunk_words(words: list[dict], max_words: int, max_chars: int = 24):
    """Группирует пословные тайминги бита в чанки по `max_words` слов И не длиннее `max_chars`
    символов (с пробелами) — длинные слова (PL и др.) иначе переносят чанк на вторую строку
    (портировано 2026-07-05 из `../creative production scheme/autopilot_factory/engine.py:chunk_words`,
    аудит E4 там же). Одиночное слово длиннее max_chars всё равно кладём в свой чанк."""
    chunks: list[list[dict]] = []
    cur: list[dict] = []
    cur_chars = 0
    for w in words:
        token = w["text"]
        add = len(token) + (1 if cur else 0)  # +1 за пробел перед словом
        if cur and (len(cur) >= max_words or cur_chars + add > max_chars):
            chunks.append(cur)
            cur, cur_chars, add = [], 0, len(token)
        cur.append(w)
        cur_chars += add
    if cur:
        chunks.append(cur)
    return chunks


def _caption_clips(beat_words: list[list[dict]], fallback_captions: list[str],
                   beat_starts: list[float], beat_durs: list[float], cap_style,
                   on_props: str = 'color:"#FFDD00",scale:1.08',
                   off_props: str = 'color:"#ffffff",scale:1.0') -> tuple[list[str], list[str]]:
    """Строит субтитровую дорожку. Если для бита есть пословный тайминг (оценка по длине слова,
    см. `engine._estimate_word_timestamps` — без ASR) — режем на чанки по words_on_screen/max_chars
    с реальным началом/концом произнесения (караоке-подсветка по словам). Если тайминга нет —
    фолбэк: on_screen_text целиком на весь бит (старое поведение)."""
    clips, tweens = [], []
    cap_idx = 0
    prev_end = 0.0  # монотонный клэмп: соседние чанки не должны касаться/перекрываться
                     # (округление в _estimate_word_timestamps иногда даёт разницу <1мс)
    for i, words in enumerate(beat_words):
        if words:
            for chunk in _chunk_words(words, cap_style.words_on_screen, cap_style.max_chars):
                cs, ce = chunk[0]["start"], chunk[-1]["end"]
                cs = max(cs, prev_end)
                ce = max(ce, cs)
                cd = max(ce - cs, 0.3)
                prev_end = cs + cd
                word_spans = []
                for j, w in enumerate(chunk):
                    wid = f"c{cap_idx}_w{j}"
                    word_spans.append(f'<span id="{wid}" class="word">{escape(w["text"])}</span>')
                    if cap_style.karaoke:
                        ws, we = w["start"] - cs, w["end"] - cs
                        tweens.append(f'tl.to("#{wid}",{{{on_props},'
                                      f'duration:0.08,ease:"power1.out"}},{cs + max(ws, 0):.3f});')
                        tweens.append(f'tl.to("#{wid}",{{{off_props},'
                                      f'duration:0.12,ease:"power1.out"}},{cs + we:.3f});')
                clips.append(
                    f'<div id="cap{cap_idx}" class="clip cap" data-start="{cs:.3f}" '
                    f'data-duration="{cd:.3f}" data-track-index="2">{" ".join(word_spans)}</div>'
                )
                tweens.append(f'tl.from("#cap{cap_idx}",{{opacity:0,y:26,duration:0.25,'
                              f'ease:"power2.out"}},{cs:.3f});')
                cap_idx += 1
        else:
            cap = escape(fallback_captions[i] or "").strip()
            if cap:
                cs, cd = beat_starts[i] + 0.12, max(beat_durs[i] - 0.12, 0.3)
                cs = max(cs, prev_end)
                prev_end = cs + cd
                clips.append(
                    f'<div id="cap{cap_idx}" class="clip cap" data-start="{cs:.3f}" '
                    f'data-duration="{cd:.3f}" data-track-index="2">{cap}</div>'
                )
                tweens.append(f'tl.from("#cap{cap_idx}",{{opacity:0,y:26,duration:0.3,'
                              f'ease:"power2.out"}},{cs:.3f});')
                cap_idx += 1
    return clips, tweens


def _accent_html(text: str) -> str:
    """v3: разметка акцента в постере/плашке — «*слово*» подсвечивается фирменным жёлтым.
    Текст экранируется ДО подстановки span'ов (звёздочки не участвуют в escape)."""
    parts = text.split("*")
    if len(parts) < 3:
        return escape(text.replace("*", ""))
    out = []
    for i, p in enumerate(parts):
        if not p:
            continue
        out.append(f'<span class="hl">{escape(p)}</span>' if i % 2 == 1 else escape(p))
    return "".join(out)


def _headline_font_px(text: str) -> int:
    """v3: авторазмер постера от длины строки. Аудит 2026-07-15: 92px на 1920 — мелко для
    миниатюры ленты; топ-упаковка Shorts — крупный 2-строчный блок. Чем короче текст, тем крупнее."""
    n = len(text.replace("*", ""))
    if n <= 16:
        return 132
    if n <= 24:
        return 116
    if n <= 34:
        return 102
    return 92


def _headline_clip(text: str, dur: float, skin: str = "photo") -> tuple[list[str], list[str]]:
    """v2 (growth_plan_2026-07-13, этап 1): постер-заголовок первого кадра. Лента Shorts
    показывает кадр-0 как «обложку» — поэтому заголовок ПОЛНОСТЬЮ видим уже при t=0
    (никаких входных анимаций/fade-in: tween `from opacity:0` делает его невидимым в
    нулевом кадре). Уходит мягким fade-out в конце своего окна. Позиция — верхняя треть
    ниже UI-зоны платформ (~15% сверху), не пересекается с караоке-субтитрами (нижняя треть).
    v3: авторазмер, акцент-слово (*слово* → жёлтый), скрим-градиент под текстом — постер
    читается на кадре любой светлоты (аудит: белый текст без подложки тонул у окна)."""
    if not text.strip():
        return [], []
    dur = max(dur, 0.8)
    fade = min(0.3, dur / 3)
    if skin == "collage":
        # Коллаж: заголовок — рваная бумажная плашка поверх кадра, скрим не нужен (контраст
        # даёт сама бумага). Плашка видима с t=0 по тому же правилу, что и в photo-скине:
        # кадр-0 = обложка в ленте, входных анимаций у заголовка быть не должно.
        fs = min(_headline_font_px(text.strip()), 118)  # на бумаге с полями 132px переполняет
        clips = [(f'<div id="headline" class="clip headline paper" style="font-size:{fs}px" '
                  f'data-start="0.000" data-duration="{dur:.3f}" data-track-index="4">'
                  f'{_accent_html(text.strip())}</div>')]
        return clips, [f'tl.to("#headline",{{opacity:0,duration:{fade:.3f},'
                       f'ease:"power1.in"}},{dur - fade:.3f});']
    fs = _headline_font_px(text.strip())
    clips = [
        (f'<div id="hscrim" class="clip scrim" data-start="0.000" '
         f'data-duration="{dur:.3f}" data-track-index="3"></div>'),
        (f'<div id="headline" class="clip headline" style="font-size:{fs}px" data-start="0.000" '
         f'data-duration="{dur:.3f}" data-track-index="4">{_accent_html(text.strip())}</div>'),
    ]
    tweens = [
        f'tl.to("#headline",{{opacity:0,duration:{fade:.3f},ease:"power1.in"}},{dur - fade:.3f});',
        f'tl.to("#hscrim",{{opacity:0,duration:{fade:.3f},ease:"power1.in"}},{dur - fade:.3f});',
    ]
    return clips, tweens


def _cta_clip(text: str, start: float, total: float, skin: str = "photo") -> tuple[list[str], list[str]]:
    """v3: финальная CTA-плашка — короткий бинарный вопрос в верхней трети на последнем бите,
    тем же типографическим стилем, что постер (визуальная петля «конец = начало»), с быстрым
    входом-«поп». Живёт до конца ролика (луп: последний кадр перетекает в первый)."""
    if not text.strip() or start >= total - 0.4:
        return [], []
    dur = total - start
    fs = min(_headline_font_px(text.strip()), 104)
    cls = "clip ctaplate paper" if skin == "collage" else "clip ctaplate"
    clip = (f'<div id="ctaplate" class="{cls}" style="font-size:{fs}px" '
            f'data-start="{start:.3f}" data-duration="{dur:.3f}" data-track-index="5">'
            f'{_accent_html(text.strip())}</div>')
    if skin == "collage":
        # Наклон плашки задаём ТУТ, а не в CSS: этот твин пишет transform (scale/y), и CSS-ный
        # rotate() был бы им затёрт — плашка встала бы ровно. Знак противоположен постеру.
        tweens = [(f'tl.fromTo("#ctaplate",{{opacity:0,scale:0.92,y:-18,rotation:1.1}},'
                   f'{{opacity:1,scale:1,y:0,rotation:1.1,duration:0.24,'
                   f'ease:"back.out(1.6)"}},{start:.3f});')]
    else:
        tweens = [
            (f'tl.from("#ctaplate",{{opacity:0,scale:0.92,y:-18,duration:0.24,'
             f'ease:"back.out(1.6)"}},{start:.3f});'),
        ]
    return [clip], tweens


# --- v5-collage: печатный скин (эксперимент 2026-08-05) --------------------------
# Бумажный коллаж — не «фильтр поверх фото», а другая типографика + печатная фактура:
# заголовок/субтитры/CTA живут на РВАНОЙ БУМАЖНОЙ плашке (ink на cream), поверх всего лежат
# две статичные печатные подложки — растр (halftone) и зерно бумаги. Обе неподвижны: hyperframes
# рендерит с перемоткой по таймлайну, любая не-GSAP анимация была бы недетерминированной.
_TORN_TOP = ("polygon(0% 6%,4% 2%,9% 5%,14% 1%,21% 4%,27% 0%,34% 4%,41% 1%,48% 5%,55% 1%,"
             "62% 4%,69% 0%,76% 4%,83% 1%,90% 5%,96% 2%,100% 6%,"
             "100% 94%,96% 99%,90% 95%,83% 99%,76% 95%,69% 100%,62% 96%,55% 99%,48% 95%,"
             "41% 99%,34% 96%,27% 100%,21% 96%,14% 99%,9% 95%,4% 98%,0% 94%)")
_GRAIN_SVG = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' "
              "height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' "
              "baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E"
              "%3Crect width='300' height='300' filter='url(%23n)'/%3E%3C/svg%3E")

_COLLAGE_CSS = f"""
.cap{{position:absolute;left:0;right:0;bottom:320px;width:fit-content;max-width:940px;
margin:0 auto;text-align:center;color:#16202B;background:#F2EAD8;
padding:16px 30px 22px;clip-path:{_TORN_TOP};
font-size:58px;font-weight:800;line-height:1.12;letter-spacing:-0.5px;
box-shadow:10px 13px 0 rgba(9,14,22,.30)}}
.headline,.ctaplate{{position:absolute;left:52px;right:52px;top:280px;text-align:center;
color:#16202B;background:#F2EAD8;padding:24px 28px 34px;clip-path:{_TORN_TOP};
font-weight:900;line-height:1.02;letter-spacing:-1.5px;
box-shadow:14px 18px 0 rgba(9,14,22,.32)}}
/* лёгкий наклон в РАЗНЫЕ стороны у постера и финальной плашки: бумага положена рукой,
   а петля «конец = начало» остаётся читаемой (плашки не совпадают пиксель в пиксель) */
.headline{{transform:rotate(-1.3deg)}}
.hl{{color:#2A5C82;text-decoration:underline;text-decoration-color:#4CAF50;
text-decoration-thickness:10px;text-underline-offset:6px}}
.halftone{{position:absolute;inset:0;mix-blend-mode:multiply;opacity:.30;
background-image:radial-gradient(circle at 1px 1px,rgba(12,18,26,.55) 1px,transparent 1.7px);
background-size:5px 5px}}
.grain{{position:absolute;inset:0;mix-blend-mode:multiply;opacity:.16;
background-image:url("{_GRAIN_SVG}");background-size:300px 300px}}
.word{{display:inline-block;margin-right:0.26em;padding:0 .10em;border-radius:2px}}
.word:last-child{{margin-right:0}}
"""

_PHOTO_CSS = """
.cap{position:absolute;left:70px;right:70px;bottom:340px;text-align:center;color:#fff;
font-size:62px;font-weight:800;line-height:1.15;letter-spacing:-0.5px;
text-shadow:0 4px 26px rgba(0,0,0,.85),0 0 2px rgba(0,0,0,.9)}
.headline{position:absolute;left:54px;right:54px;top:300px;text-align:center;color:#fff;
font-weight:900;line-height:1.06;letter-spacing:-1px;text-transform:none;
text-shadow:0 6px 34px rgba(0,0,0,.9),0 2px 6px rgba(0,0,0,.95),0 0 3px rgba(0,0,0,.9)}
.scrim{position:absolute;left:0;right:0;top:0;height:760px;
background:linear-gradient(180deg,rgba(6,10,18,.66) 0%,rgba(6,10,18,.44) 52%,rgba(6,10,18,0) 100%)}
.ctaplate{position:absolute;left:54px;right:54px;top:300px;text-align:center;color:#fff;
font-weight:900;line-height:1.06;letter-spacing:-1px;
text-shadow:0 6px 34px rgba(0,0,0,.9),0 2px 6px rgba(0,0,0,.95),0 0 3px rgba(0,0,0,.9)}
.hl{color:#FFD400}
.word{display:inline-block;margin-right:0.26em}
.word:last-child{margin-right:0}
"""

# Караоке-подсветка по скину: (GSAP-пропсы «слово звучит», «слово отзвучало»).
# collage: цветом подсветить нельзя — на cream-бумаге и ink, и navy читаются почти одинаково
# тёмными (проверено рендером 2026-08-05). Поэтому подсветка — МАРКЕР: слово получает навёрстанный
# navy-блок и выворотку в cream. Это и заметнее, и родное для зина/коллажа.
_KARAOKE = {
    "photo": ('color:"#FFDD00",scale:1.08', 'color:"#ffffff",scale:1.0'),
    "collage": ('color:"#F2EAD8",backgroundColor:"#2A5C82",scale:1.06',
                'color:"#16202B",backgroundColor:"rgba(42,92,130,0)",scale:1.0'),
}


def _build_html(frame_durs, beat_words, fallback_captions, beat_starts, beat_durs,
               motions, cap_style, total: float, n_frames: int,
               headline: str = "", headline_dur: float = 0.0,
               cta_text: str = "", cta_start: float = 0.0, skin: str = "photo") -> str:
    on_props, off_props = _KARAOKE.get(skin, _KARAOKE["photo"])
    fc, ft = _seq_clips("frame", list(range(n_frames)), frame_durs, motions, total)
    cc, ct = _caption_clips(beat_words, fallback_captions, beat_starts, beat_durs, cap_style,
                            on_props=on_props, off_props=off_props)
    hc, ht = _headline_clip(headline, headline_dur, skin=skin)
    xc, xt = _cta_clip(cta_text, cta_start, total, skin=skin)
    # Печатные подложки лежат ПОВЕРХ всего (старшие треки): и кадр, и бумажные плашки должны
    # выглядеть напечатанными на одном листе — растр, обрывающийся на границе плашки, сразу
    # выдаёт цифровой оверлей. Текст от этого не страдает: multiply одинаково притемняет и
    # cream-подложку, и ink-буквы, контраст между ними сохраняется.
    overlay = []
    if skin == "collage":
        overlay = [f'<div id="halftone" class="clip halftone" data-start="0.000" '
                   f'data-duration="{total:.3f}" data-track-index="6"></div>',
                   f'<div id="grain" class="clip grain" data-start="0.000" '
                   f'data-duration="{total:.3f}" data-track-index="7"></div>']
    clips = fc + overlay + cc + hc + xc
    tweens = ft + ct + ht + xt
    css = _COLLAGE_CSS if skin == "collage" else _PHOTO_CSS
    return f"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:1080px;height:1920px;overflow:hidden;background:#000}}
body{{font-family:Inter,Arial,sans-serif}}
.frame{{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover}}{css}</style></head>
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


def build_and_render(frames, beat_words, fallback_captions, cap_durs, motions, cap_style,
                     voice_wav: Path, out_mp4: Path, work_dir: Path,
                     headline: str = "", cta_text: str = "",
                     bgm_wav: Path | None = None, bgm_gain_db: float = -21.0,
                     skin: str = "photo") -> Path:
    """Собирает и рендерит ролик.
    - beat_words — пословные тайминги (whisper) по одному списку на бит, абсолютное время;
      пустой список для бита → фолбэк на fallback_captions[i] на весь бит.
    - cap_durs — длительности битов (из per-beat TTS), сумма = длине озвучки.
    - frames — от visual_director. v2: при кадров == битов каждый кадр живёт РОВНО столько,
      сколько звучит его бит (кадр синхронен смыслу озвучки — контракт «frames[i] ↔ beats[i]»
      из authoring_guide; до 2026-07-13 кадры раскладывались равномерно и уезжали от голоса
      на неравных битах). При несовпадении числа — прежний фолбэк: равномерная раскладка.
    - headline — постер-заголовок первого кадра (v2): виден с t=0, живёт на первом бите.
    v3 (factory_audit_2026-07-15):
    - кадр-0 всегда получает motion `hook_punch` (jolt первых 0.5с — свайп-тест решается там);
    - cta_text — финальная плашка-вопрос на последнем бите (стиль постера, петля к началу);
    - bgm_wav — подложка канала: лупится под длину озвучки, тише голоса на |bgm_gain_db| дБ,
      fade in/out; голос не трогаем (amix normalize=0).
    v5-эксперимент (2026-08-05):
    - skin — типографический скин сборки: `photo` (продакшен, поведение не изменилось) или
      `collage` (бумажные плашки + печатная фактура, см. docs/experiments/2026-08-05_v5collage.md)."""
    work_dir = Path(work_dir); assets = work_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    n_frames = len(frames)
    for i in range(n_frames):
        shutil.copy(frames[i], assets / f"frame{i}.png")
    (work_dir / "hyperframes.json").write_text(json.dumps(_HF_JSON, indent=2), encoding="utf-8")
    (work_dir / "meta.json").write_text(json.dumps({"id": work_dir.name, "name": work_dir.name}), encoding="utf-8")

    total = sum(float(d) for d in cap_durs)               # длину ведёт озвучка
    if n_frames == len(cap_durs):
        frame_durs = [float(d) for d in cap_durs]         # v2: кадр ↔ бит, тайминг от TTS
    else:
        frame_durs = [total / n_frames] * n_frames        # фолбэк: равномерно на всю длину
    beat_starts = []
    t = 0.0
    for d in cap_durs:
        beat_starts.append(t)
        t += float(d)
    motions = list(motions)
    if motions:
        motions[0] = "hook_punch"                          # v3: удар кадра-0 — стандарт упаковки
    # окно постер-заголовка: первый бит + треть второго (успевает прочитаться), потолок 4с
    headline_dur = 0.0
    if headline.strip() and cap_durs:
        headline_dur = float(cap_durs[0])
        if len(cap_durs) > 1:
            headline_dur += float(cap_durs[1]) / 3
        headline_dur = min(headline_dur, 4.0)
    cta_start = beat_starts[-1] if beat_starts else 0.0    # v3: плашка живёт на последнем бите
    (work_dir / "index.html").write_text(
        _build_html(frame_durs, beat_words, fallback_captions, beat_starts, cap_durs,
                   motions, cap_style, total, n_frames,
                   headline=headline, headline_dur=headline_dur,
                   cta_text=cta_text, cta_start=cta_start, skin=skin), encoding="utf-8")

    subprocess.run(["npx", "--yes", "hyperframes", "render", "-o", "video.mp4"],
                   cwd=str(work_dir), check=True, env=_node22_env())

    out_mp4 = Path(out_mp4)
    if bgm_wav and Path(bgm_wav).exists():
        # v3: голос + BGM. stream_loop -1 крутит подложку бесконечно, atrim режет по голосу,
        # fade 0.6/0.9с; amix normalize=0 не приглушает голос (веса 1:1, BGM уже -21дБ).
        fade_out_start = max(total - 0.9, 0.0)
        fc = (f"[2:a]volume={bgm_gain_db}dB,atrim=0:{total:.3f},"
              f"afade=t=in:st=0:d=0.6,afade=t=out:st={fade_out_start:.3f}:d=0.9[bg];"
              f"[1:a][bg]amix=inputs=2:duration=first:normalize=0[a]")
        subprocess.run(["ffmpeg", "-y", "-i", str(work_dir / "video.mp4"), "-i", str(voice_wav),
                        "-stream_loop", "-1", "-i", str(bgm_wav),
                        "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-map_metadata", "-1", "-fflags", "+bitexact",
                        "-flags:a", "+bitexact",
                        str(out_mp4)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(["ffmpeg", "-y", "-i", str(work_dir / "video.mp4"), "-i", str(voice_wav),
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-map_metadata", "-1", "-fflags", "+bitexact",
                        "-flags:a", "+bitexact",
                        str(out_mp4)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_mp4
