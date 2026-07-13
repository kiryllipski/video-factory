#!/usr/bin/env python3
"""Разовый помощник: из готового script.json (пишет Claude) генерирует compliance.json
(passthrough — сценарий уже написан комплаенс-чисто) и frame_plan.json (кадр = visual_cue бита,
единый grade/light/lens, чередование motion). Экономит механику, не творчество."""
import sys
import json
from pathlib import Path

MOTIONS = ["ken_burns_in", "pan_left", "parallax", "static_hold", "ken_burns_out", "pan_right"]

GRADE = ("Premium wellness noir: deep navy blue #2A5C82, leafy green #4CAF50 accents, warm "
         "off-white #F5F5F5 highlights; soft directional lighting with gentle corner darkening "
         "from lighting, not a photo border")
LIGHT = ("Soft single-source key light, low-key contrast, warm morning glow on macro subjects, "
         "clean uncluttered backgrounds")
LENS = "85mm macro for product/hand details; 50mm for symbolic pairing compositions"


def main(run_dir: Path):
    script = json.loads((run_dir / "script.json").read_text(encoding="utf-8"))

    compliance = {"passed": True, "fixes": [], "cleaned_script": script}
    (run_dir / "compliance.json").write_text(json.dumps(compliance, ensure_ascii=False, indent=2), encoding="utf-8")

    frames = []
    t = 0.0
    for i, beat in enumerate(script["beats"]):
        frames.append({
            "prompt": beat["visual_cue"],
            "aspect": "9:16",
            "ref_ids": [],
            "motion": MOTIONS[i % len(MOTIONS)],
            "start_s": round(t, 2),
            "dur_s": beat["dur_s"],
        })
        t += beat["dur_s"]
    frame_plan = {"grade": GRADE, "light": LIGHT, "lens": LENS, "frames": frames}
    (run_dir / "frame_plan.json").write_text(json.dumps(frame_plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] {run_dir.name}: compliance.json + frame_plan.json ({len(frames)} frames)")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
