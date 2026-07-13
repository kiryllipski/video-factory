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
    m = {
        "ken_burns_in":  f'tl.fromTo("{sel}",{{scale:1.0}},{{scale:1.10,duration:{dur},ease:"none"}},{start});',
        "ken_burns_out": f'tl.fromTo("{sel}",{{scale:1.10}},{{scale:1.0,duration:{dur},ease:"none"}},{start});',
        "pan_left":      f'tl.fromTo("{sel}",{{scale:1.08,xPercent:3}},{{xPercent:-3,duration:{dur},ease:"none"}},{start});',
        "pan_right":     f'tl.fromTo("{sel}",{{scale:1.08,xPercent:-3}},{{xPercent:3,duration:{dur},ease:"none"}},{start});',
        "parallax":      f'tl.fromTo("{sel}",{{scale:1.06,yPercent:2}},{{yPercent:-2,duration:{dur},ease:"none"}},{start});',
        "static_hold":   f'tl.fromTo("{sel}",{{scale:1.01}},{{scale:1.04,duration:{dur},ease:"none"}},{start});',
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
                   beat_starts: list[float], beat_durs: list[float], cap_style) -> tuple[list[str], list[str]]:
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
                        tweens.append(f'tl.to("#{wid}",{{color:"#FFDD00",scale:1.08,'
                                      f'duration:0.08,ease:"power1.out"}},{cs + max(ws, 0):.3f});')
                        tweens.append(f'tl.to("#{wid}",{{color:"#ffffff",scale:1.0,'
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


def _headline_clip(text: str, dur: float) -> tuple[list[str], list[str]]:
    """v2 (growth_plan_2026-07-13, этап 1): постер-заголовок первого кадра. Лента Shorts
    показывает кадр-0 как «обложку» — поэтому заголовок ПОЛНОСТЬЮ видим уже при t=0
    (никаких входных анимаций/fade-in: tween `from opacity:0` делает его невидимым в
    нулевом кадре). Уходит мягким fade-out в конце своего окна. Позиция — верхняя треть
    ниже UI-зоны платформ (~15% сверху), не пересекается с караоке-субтитрами (нижняя треть)."""
    if not text.strip():
        return [], []
    dur = max(dur, 0.8)
    clip = (f'<div id="headline" class="clip headline" data-start="0.000" '
            f'data-duration="{dur:.3f}" data-track-index="3">{escape(text.strip())}</div>')
    fade = min(0.3, dur / 3)
    tween = (f'tl.to("#headline",{{opacity:0,duration:{fade:.3f},ease:"power1.in"}},'
             f'{dur - fade:.3f});')
    return [clip], [tween]


def _build_html(frame_durs, beat_words, fallback_captions, beat_starts, beat_durs,
               motions, cap_style, total: float, n_frames: int,
               headline: str = "", headline_dur: float = 0.0) -> str:
    fc, ft = _seq_clips("frame", list(range(n_frames)), frame_durs, motions, total)
    cc, ct = _caption_clips(beat_words, fallback_captions, beat_starts, beat_durs, cap_style)
    hc, ht = _headline_clip(headline, headline_dur)
    clips = fc + cc + hc
    tweens = ft + ct + ht
    return f"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:1080px;height:1920px;overflow:hidden;background:#000}}
body{{font-family:Inter,Arial,sans-serif}}
.frame{{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover}}
.cap{{position:absolute;left:70px;right:70px;bottom:340px;text-align:center;color:#fff;
font-size:62px;font-weight:800;line-height:1.15;letter-spacing:-0.5px;
text-shadow:0 4px 26px rgba(0,0,0,.85),0 0 2px rgba(0,0,0,.9)}}
.headline{{position:absolute;left:60px;right:60px;top:320px;text-align:center;color:#fff;
font-size:92px;font-weight:900;line-height:1.08;letter-spacing:-1px;text-transform:none;
text-shadow:0 6px 34px rgba(0,0,0,.9),0 2px 6px rgba(0,0,0,.95),0 0 3px rgba(0,0,0,.9)}}
.word{{display:inline-block;margin-right:0.26em}}
.word:last-child{{margin-right:0}}
</style></head>
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
                     headline: str = "") -> Path:
    """Собирает и рендерит ролик.
    - beat_words — пословные тайминги (whisper) по одному списку на бит, абсолютное время;
      пустой список для бита → фолбэк на fallback_captions[i] на весь бит.
    - cap_durs — длительности битов (из per-beat TTS), сумма = длине озвучки.
    - frames — от visual_director. v2: при кадров == битов каждый кадр живёт РОВНО столько,
      сколько звучит его бит (кадр синхронен смыслу озвучки — контракт «frames[i] ↔ beats[i]»
      из authoring_guide; до 2026-07-13 кадры раскладывались равномерно и уезжали от голоса
      на неравных битах). При несовпадении числа — прежний фолбэк: равномерная раскладка.
    - headline — постер-заголовок первого кадра (v2): виден с t=0, живёт на первом бите."""
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
    # окно постер-заголовка: первый бит + треть второго (успевает прочитаться), потолок 4с
    headline_dur = 0.0
    if headline.strip() and cap_durs:
        headline_dur = float(cap_durs[0])
        if len(cap_durs) > 1:
            headline_dur += float(cap_durs[1]) / 3
        headline_dur = min(headline_dur, 4.0)
    (work_dir / "index.html").write_text(
        _build_html(frame_durs, beat_words, fallback_captions, beat_starts, cap_durs,
                   motions, cap_style, total, n_frames,
                   headline=headline, headline_dur=headline_dur), encoding="utf-8")

    subprocess.run(["npx", "--yes", "hyperframes", "render", "-o", "video.mp4"],
                   cwd=str(work_dir), check=True, env=_node22_env())

    out_mp4 = Path(out_mp4)
    subprocess.run(["ffmpeg", "-y", "-i", str(work_dir / "video.mp4"), "-i", str(voice_wav),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    str(out_mp4)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_mp4
