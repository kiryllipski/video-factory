#!/usr/bin/env python3
"""Render the 2026-09-04 two-character cold-shower dialogue experiment.

This intentionally uses the established v8 assembly layer, not v9.  It is a
small isolated dialogue format: alternating Polish voices plus approved
ImageGen frames, with only lightweight package checks before publication.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORCH = ROOT.parent / "orchestration"
RUN = ROOT / "runs" / "vitallogic_bad_pl" / "2026-09-04_dialogue-zimny-prysznic"
sys.path.insert(0, str(ORCH))
sys.path.insert(0, str(ROOT))

from audio_agent import generate_speech  # noqa: E402
from runtime_support_v8 import _estimate_word_timestamps, _trim_silence, _wav_dur  # noqa: E402
import assembly_v8 as A  # noqa: E402
import schemas_v8 as S  # noqa: E402


LINES = [
    {"speaker": "female", "voice": "Aoede", "text": "Zimny prysznic naprawdę budzi?", "caption": "ZIMNY PRYSZNIC BUDZI?", "emphasis": "budzi"},
    {"speaker": "male", "voice": "Charon", "text": "Na chwilę może. Zimno uruchamia reakcję alarmową.", "caption": "REAKCJA ALARMOWA", "emphasis": "alarmową"},
    {"speaker": "female", "voice": "Aoede", "text": "Czyli mam poranny superpower?", "caption": "SUPERPOWER?", "emphasis": "superpower"},
    {"speaker": "male", "voice": "Charon", "text": "Raczej krótki zastrzyk czujności, nie energia na cały dzień.", "caption": "CZUJNOŚĆ ≠ ENERGIA", "emphasis": "czujności"},
    {"speaker": "female", "voice": "Aoede", "text": "Ale po nim czuję się jak rakieta.", "caption": "JAK RAKIETA", "emphasis": "rakieta"},
    {"speaker": "male", "voice": "Charon", "text": "To wrażenie może być prawdziwe. Tylko nie jest testem jakości snu.", "caption": "TO NIE TEST SNU", "emphasis": "nie jest"},
    {"speaker": "female", "voice": "Aoede", "text": "Czyli lodowa bohaterka nie wygrywa?", "caption": "KTO WYGRYWA?", "emphasis": "wygrywa"},
    {"speaker": "male", "voice": "Charon", "text": "Wygrywa rytuał, który jesteś w stanie powtarzać bez kary.", "caption": "RUTYNA BEZ KARY", "emphasis": "powtarzać"},
    {"speaker": "female", "voice": "Aoede", "text": "A jeśli nienawidzę zimna?", "caption": "NIENAWIDZISZ ZIMNA?", "emphasis": "nienawidzę"},
    {"speaker": "male", "voice": "Charon", "text": "Nie musisz go polubić. Spacer, światło i woda też robią poranny sygnał.", "caption": "SĄ INNE SYGNAŁY", "emphasis": "inne"},
    {"speaker": "female", "voice": "Aoede", "text": "Czyli prysznic to efekt, nie magia?", "caption": "EFEKT, NIE MAGIA", "emphasis": "nie magia"},
    {"speaker": "male", "voice": "Charon", "text": "Dokładnie. Wybierz wersję poranka, którą powtórzysz jutro.", "caption": "POWTÓRZ JUTRO", "emphasis": "jutro"},
]

STYLES = {
    "female": "warm, quick, witty Polish female dialogue voice; curious, lively, playful timing, clear articulation",
    "male": "warm, quick, witty Polish male dialogue voice; concise, calm, lightly ironic, clear articulation",
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _signature(line: dict) -> str:
    value = {"text": line["text"], "voice": line["voice"], "style": STYLES[line["speaker"]], "speed": 1.06}
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def synthesize_dialogue() -> tuple[Path, list[float], list[list[dict]]]:
    audio_dir = RUN / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    pieces, beat_durations, beat_words = [], [], []
    cumulative = 0.0
    for index, line in enumerate(LINES):
        wav = audio_dir / f"line{index:02d}-{line['speaker']}.wav"
        meta = wav.with_suffix(".json")
        cached = ""
        if meta.exists():
            try:
                cached = json.loads(meta.read_text(encoding="utf-8")).get("signature", "")
            except (OSError, json.JSONDecodeError):
                pass
        if not (wav.exists() and wav.stat().st_size > 1000 and cached == _signature(line)):
            generate_speech(line["text"], voice=line["voice"], style=STYLES[line["speaker"]], model="tts", out=str(wav), speed=1.06)
            _trim_silence(wav)
            write_json(meta, {"signature": _signature(line), "speaker": line["speaker"], "voice": line["voice"]})
        duration = _wav_dur(wav)
        if duration <= 0:
            raise RuntimeError(f"bad dialogue WAV duration: {wav}")
        beat_durations.append(duration)
        beat_words.append(_estimate_word_timestamps(line["text"], duration, cumulative))
        pieces.append(wav)
        cumulative += duration
        if index < len(LINES) - 1:
            pause = 0.18 if line["speaker"] != LINES[index + 1]["speaker"] else 0.10
            pause_path = audio_dir / f"pause{index:02d}.wav"
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", str(pause), "-c:a", "pcm_s16le", str(pause_path)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            pieces.append(pause_path)
            beat_durations[-1] += pause
            cumulative += pause
    (audio_dir / "dialogue-concat.txt").write_text("".join(f"file '{path.name}'\n" for path in pieces), encoding="utf-8")
    voice_wav = audio_dir / "dialogue.wav"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(audio_dir / "dialogue-concat.txt"), "-c", "copy", str(voice_wav)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return voice_wav, beat_durations, beat_words


def main() -> None:
    if not all((RUN / "frames" / f"frame{i}.png").is_file() for i in range(8)):
        raise SystemExit("Eight approved ImageGen frames are required before rendering.")
    os.environ["RUN_COST_DIR"] = str(RUN)
    voice_wav, durations, words = synthesize_dialogue()
    write_json(RUN / "dialogue_script.json", {"format": "offscreen_dialogue", "language": "pl", "topic": "Czy zimny prysznic naprawdę budzi?", "characters": [{"role": "Królowa Lodowego Prysznica", "voice": "Aoede"}, {"role": "Spokojny narrator naukowy", "voice": "Charon"}], "lines": LINES, "strict_qa": False, "publication_authorized": True})
    write_json(RUN / "format_experiment.json", {"format": "offscreen_dialogue", "pipeline_base": "v8 assembly", "v9_used": False, "qa_gate": "skipped_for_lightweight_entertainment_experiment", "visuals": "three original ImageGen scenes reused as paced crops", "duration_policy": "under 60 seconds"})
    overlays = [
        S.Overlay(kind="versus", beat_idx=3, label="CZUJNOŚĆ", value="TERAZ", label_b="ENERGIA", value_b="CAŁY DZIEŃ", winner="none"),
        S.Overlay(kind="timeline", beat_idx=7, label="PORANNY SYGNAŁ", items=["Światło", "Spacer", "Woda", "Rytuał"]),
        S.Overlay(kind="stamp", beat_idx=10, label="WERDYKT", value="EFEKT ≠ MAGIA"),
    ]
    frames = [RUN / "frames" / f"frame{i}.png" for i in range(8)]
    A.build_and_render(frames, [(0, 1), (2, 2), (3, 4), (5, 5), (6, 7), (8, 8), (9, 10), (11, 11)], ["hook_punch", "punch_hold", "ken_burns_in", "pan_right", "ken_burns_in", "pan_left", "punch_hold", "ken_burns_out"], words, [line["caption"] for line in LINES], durations, overlays, [line["emphasis"] for line in LINES], voice_wav, RUN / "out.mp4", RUN / "hf", headline="ZIMNY PRYSZNIC?", payoff_text="EFEKT, NIE MAGIA", turn_beat_idx=7, bgm_wav=None, sfx_profile="soft", payoff_frame=frames[-1], headline_until_first_cut=True, lang="pl", layout_gate=False)
    media = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(RUN / "out.mp4")], text=True))
    video = next(item for item in media["streams"] if item.get("codec_type") == "video")
    audio = next(item for item in media["streams"] if item.get("codec_type") == "audio")
    write_json(RUN / "run_meta.json", {"pipeline_version": "dialogue-v8-experiment-0.2", "format": "offscreen_dialogue", "topic": "Czy zimny prysznic naprawdę budzi?", "duration_s": round(float(media["format"]["duration"]), 3), "width": video.get("width"), "height": video.get("height"), "video_codec": video.get("codec_name"), "audio_codec": audio.get("codec_name"), "voices": {"female": "Aoede", "male": "Charon"}, "strict_qa": False, "publication_authorized": True})
    write_json(RUN / "publish_package.json", {"title": "Zimny prysznic budzi? Efekt, nie magia", "description": "Zimny prysznic może dać krótki sygnał pobudzenia, ale nie zastępuje snu ani porannej rutyny. W tym krótkim dialogu zderzamy lodowy rytuał z prostym pytaniem: co naprawdę da się powtórzyć jutro?\n\nMateriał ma charakter edukacyjny i nie zastępuje porady lekarza.\n\n#zimnyprysznic #poranek #nawyki #sen #Shorts", "tags": ["zimny prysznic", "cold shower", "poranna rutyna", "nawyki", "sen", "pobudzenie"], "category": "27", "lang": "pl"})
    print(f"[dialogue-v8] done · {media['format']['duration']}s · {RUN / 'out.mp4'}")


if __name__ == "__main__":
    main()
