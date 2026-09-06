#!/usr/bin/env python3
"""Build one local dialogue-format experiment from an existing VitalLogic run.

This is intentionally an experiment adapter, not a replacement for the canonical
v9 pipeline.  It reuses approved frames from the evening-training courtroom run,
generates alternating Gemini TTS lines, and renders through the existing assembly
without invoking the v9 timing/release/vision gates.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORCH = ROOT.parent / "orchestration"
SOURCE_RUN = ROOT / "runs" / "vitallogic_bad_pl" / "2026-08-29_v9-wieczorny-trening-sen-courtroom"
RUN = ROOT / "runs" / "vitallogic_bad_pl" / "2026-08-29_dialogue-trening-wieczorem"

sys.path.insert(0, str(ORCH))
sys.path.insert(0, str(ROOT))

from audio_agent import generate_speech  # noqa: E402
from runtime_support_v8 import _estimate_word_timestamps, _trim_silence, _wav_dur  # noqa: E402
import assembly_v8 as A  # noqa: E402
import schemas_v8 as S  # noqa: E402


LINES = [
    {"speaker": "female", "voice": "Aoede", "text": "Trening wieczorem psuje sen?", "caption": "TRENING WIECZOREM?", "emphasis": "Trening"},
    {"speaker": "male", "voice": "Charon", "text": "Tak mówi oskarżenie. Ale zawsze?", "caption": "ALE ZAWSZE?", "emphasis": "zawsze"},
    {"speaker": "female", "voice": "Aoede", "text": "Brzmi jak prosty wyrok.", "caption": "PROSTY WYROK?", "emphasis": "wyrok"},
    {"speaker": "male", "voice": "Charon", "text": "Tylko że przegląd z 2025 roku nie znalazł średnio istotnej różnicy w śnie.", "caption": "META-ANALIZA 2025", "emphasis": "przegląd"},
    {"speaker": "female", "voice": "Aoede", "text": "Czyli wieczorna pora jest bez znaczenia?", "caption": "BEZ ZNACZENIA?", "emphasis": "bez znaczenia"},
    {"speaker": "male", "voice": "Charon", "text": "Nie tak szybko. Drugi przegląd też nie dał automatycznego wyroku.", "caption": "DRUGI PRZEGLĄD", "emphasis": "automatycznego"},
    {"speaker": "female", "voice": "Aoede", "text": "A intensywność treningu?", "caption": "INTENSYWNOŚĆ?", "emphasis": "intensywność"},
    {"speaker": "male", "voice": "Charon", "text": "Badania są różne, więc reakcja zależy od kontekstu.", "caption": "KONTEKST", "emphasis": "kontekstu"},
    {"speaker": "female", "voice": "Aoede", "text": "Czyli jedna gorsza noc nie znaczy: zakaz?", "caption": "NIE ZAKAZ", "emphasis": "zakaz"},
    {"speaker": "male", "voice": "Charon", "text": "Dokładnie. Średnio nie ma automatu, ale obserwuj własną reakcję.", "caption": "BRAK AUTOMATU", "emphasis": "automatu"},
    {"speaker": "female", "voice": "Aoede", "text": "A jeśli problemy powtarzają się regularnie?", "caption": "POWTARZA SIĘ?", "emphasis": "regularnie"},
    {"speaker": "male", "voice": "Charon", "text": "Wtedy warto porozmawiać z lekarzem.", "caption": "POROZMAWIAJ Z LEKARZEM", "emphasis": "lekarzem"},
]

STYLES = {
    "female": "warm, quick, witty Polish female dialogue voice; curious, natural, lightly skeptical, clear articulation, playful timing",
    "male": "warm, quick, witty Polish male dialogue voice; concise, evidence-led, lightly ironic, clear articulation, playful timing",
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def signature(line: dict) -> str:
    payload = {"text": line["text"], "voice": line["voice"], "style": STYLES[line["speaker"]], "speed": 1.06}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def synthesize_dialogue() -> tuple[Path, list[float], list[list[dict]]]:
    audio_dir = RUN / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    pieces: list[Path] = []
    durations: list[float] = []
    words: list[list[dict]] = []
    cumulative = 0.0

    for index, line in enumerate(LINES):
        wav = audio_dir / f"line{index:02d}-{line['speaker']}.wav"
        meta = wav.with_suffix(".json")
        sig = signature(line)
        cached = ""
        if meta.exists():
            try:
                cached = json.loads(meta.read_text(encoding="utf-8")).get("signature", "")
            except (OSError, json.JSONDecodeError):
                cached = ""
        if not (wav.exists() and wav.stat().st_size > 1000 and cached == sig):
            generate_speech(
                line["text"],
                voice=line["voice"],
                style=STYLES[line["speaker"]],
                model="tts",
                out=str(wav),
                speed=1.06,
            )
            _trim_silence(wav)
            write_json(meta, {"signature": sig, "speaker": line["speaker"], "voice": line["voice"]})
        duration = _wav_dur(wav)
        if duration <= 0:
            raise RuntimeError(f"bad dialogue WAV duration: {wav}")
        durations.append(duration)
        words.append(_estimate_word_timestamps(line["text"], duration, cumulative))
        pieces.append(wav)
        cumulative += duration

        if index < len(LINES) - 1:
            pause = 0.18 if line["speaker"] != LINES[index + 1]["speaker"] else 0.10
            if index == 9:
                pause = 0.30
            pause_path = audio_dir / f"pause{index:02d}.wav"
            subprocess.run(
                ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(pause), "-c:a", "pcm_s16le", str(pause_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            pieces.append(pause_path)
            durations[-1] += pause
            cumulative += pause

    concat = audio_dir / "dialogue-concat.txt"
    concat.write_text("".join(f"file '{path.name}'\n" for path in pieces), encoding="utf-8")
    voice_wav = audio_dir / "dialogue.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(voice_wav)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return voice_wav, durations, words


def make_overlays() -> tuple[list[S.Overlay], dict[int, dict[str, str]]]:
    original_cards = json.loads((SOURCE_RUN / "source_cards.json").read_text(encoding="utf-8"))
    cards = {3: original_cards["2"], 5: original_cards["3"]}
    overlays = [
        S.Overlay(kind="source", beat_idx=3, claim_ids=["CLM-01"]),
        S.Overlay(kind="source", beat_idx=5, claim_ids=["CLM-02"]),
        S.Overlay(kind="timeline", beat_idx=7, label="KONTEKST", items=["Badania", "Intensywność", "Reakcja osoby", "Werdykt"]),
        S.Overlay(kind="stamp", beat_idx=8, label="WERDYKT", value="NIE ZAKAZ", claim_ids=["CLM-05"]),
    ]
    return overlays, cards


def main() -> None:
    if not SOURCE_RUN.is_dir():
        raise SystemExit(f"source run not found: {SOURCE_RUN}")
    RUN.mkdir(parents=True, exist_ok=True)
    os.environ["RUN_COST_DIR"] = str(RUN)

    frame_dir = RUN / "frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    for index in range(8):
        source = SOURCE_RUN / "frames" / f"frame{index:02d}.png"
        if not source.is_file():
            raise SystemExit(f"source frame not found: {source}")
        shutil.copy2(source, frame_dir / f"frame{index}.png")

    voice_wav, beat_durations, beat_words = synthesize_dialogue()
    overlays, source_cards = make_overlays()
    frame_spans = [(0, 1), (2, 2), (3, 3), (4, 5), (6, 7), (8, 9), (10, 10), (11, 11)]
    motions = ["hook_punch", "punch_hold", "ken_burns_in", "pan_right", "ken_burns_in", "pan_left", "punch_hold", "ken_burns_out"]
    frames = [frame_dir / f"frame{index}.png" for index in range(8)]

    dialogue_script = {
        "format": "offscreen_dialogue",
        "language": "pl",
        "topic": "Trening wieczorem a sen",
        "voice_design": {"female": "Aoede", "male": "Charon", "turn_taking": "alternating lines"},
        "lines": LINES,
        "strict_qa": False,
        "publication_authorized": False,
        "source_run": SOURCE_RUN.name,
    }
    write_json(RUN / "dialogue_script.json", dialogue_script)
    write_json(RUN / "format_experiment.json", {
        "format": "offscreen_dialogue",
        "brief": "Два закадровых голоса спорят о бытовом утверждении; женский голос задаёт вопросы, мужской приносит доказательства и нюанс.",
        "qa_gate": "skipped_by_user_request",
        "duration_policy": "up_to_60_seconds",
        "hard_duration_gate": False,
        "frames": "reused_from_existing_approved_courtroom_run",
    })

    A.build_and_render(
        frames,
        frame_spans,
        motions,
        beat_words,
        [line["caption"] for line in LINES],
        beat_durations,
        overlays,
        [line["emphasis"] for line in LINES],
        voice_wav,
        RUN / "out.mp4",
        RUN / "hf",
        headline="TRENING WIECZOREM?",
        payoff_text="NIE AUTOMATYCZNIE",
        turn_beat_idx=8,
        bgm_wav=None,
        sfx_profile="soft",
        payoff_frame=frames[-1],
        headline_until_first_cut=True,
        lang="pl",
        layout_gate=False,
        source_cards=source_cards,
    )

    probe = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(RUN / "out.mp4")],
        text=True,
    )
    media = json.loads(probe)
    video = next(stream for stream in media["streams"] if stream.get("codec_type") == "video")
    audio = next(stream for stream in media["streams"] if stream.get("codec_type") == "audio")
    duration = round(float(media["format"]["duration"]), 3)
    write_json(RUN / "run_meta.json", {
        "pipeline_version": "dialogue-experiment-0.1",
        "format": "offscreen_dialogue",
        "topic": dialogue_script["topic"],
        "duration_s": duration,
        "narration_duration_s": round(sum(beat_durations), 3),
        "width": video.get("width"),
        "height": video.get("height"),
        "video_codec": video.get("codec_name"),
        "audio_codec": audio.get("codec_name"),
        "voices": {"female": "Aoede", "male": "Charon"},
        "strict_qa": False,
        "publication_authorized": False,
    })
    print(f"[dialogue] done · {duration:.2f}s · {RUN / 'out.mp4'}")


if __name__ == "__main__":
    main()
