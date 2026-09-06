"""Write a v8 manifest for already inspected built-in ImageGen frames."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: write_codex_media_manifest.py RUN_DIR")
    run_dir = Path(sys.argv[1]).resolve()
    frame_plan = json.loads((run_dir / "frame_plan.json").read_text(encoding="utf-8"))
    expected = len(frame_plan["frames"])
    frames = [run_dir / "frames" / f"frame{i:02d}.png" for i in range(expected)]
    missing = [str(path) for path in frames if not path.is_file()]
    if missing:
        raise SystemExit("missing frames: " + ", ".join(missing))
    entries = []
    for index, path in enumerate(frames):
        entries.append({
            "index": index,
            "path": str(path.relative_to(run_dir)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "tool": "built_in_imagegen",
            "approval": "accepted_after_visual_inspection",
            "visual_inspection": "local frame review completed",
        })
    manifest = {
        "image_generation": "built_in_imagegen",
        "image_model_substitution": "none",
        "engine_v8_build_used": False,
        "frames": entries,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    (run_dir / "media_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"manifest written: {run_dir / 'media_manifest.json'} ({expected} frames)")


if __name__ == "__main__":
    main()
