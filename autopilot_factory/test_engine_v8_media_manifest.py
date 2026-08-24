"""Pure tests for the v8 approved-frame manifest gate."""
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import engine_v8 as E
import schemas_v8 as S


def minimal_plan() -> S.FramePlan:
    frames = [
        S.Frame(
            prompt=f"approved frame {index}",
            claim="A concrete visual claim is shown.",
            shot="macro" if index % 2 else "wide",
            subject="product",
            beat_from=index,
            beat_to=index,
        )
        for index in range(8)
    ]
    return S.FramePlan(grade="clean", light="soft", lens="editorial", frames=frames)


class MediaManifestTests(unittest.TestCase):
    def write_manifest(self, root: Path) -> None:
        entries = []
        for index in range(8):
            path = root / "frames" / f"frame{index:02d}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"frame-{index}".encode())
            entries.append({
                "index": index,
                "path": str(path.relative_to(root)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "approval": "accepted_after_visual_inspection",
            })
        (root / "media_manifest.json").write_text(json.dumps({
            "image_generation": "built_in_imagegen",
            "image_model_substitution": "none",
            "frames": entries,
        }), encoding="utf-8")

    def test_manifest_returns_exact_approved_order(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_manifest(root)
            result = E.approved_codex_frames(root, minimal_plan())
            self.assertEqual([path.name for path in result], [f"frame{i:02d}.png" for i in range(8)])

    def test_hash_mismatch_is_a_hard_stop(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_manifest(root)
            manifest_path = root / "media_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["frames"][3]["sha256"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(SystemExit):
                E.approved_codex_frames(root, minimal_plan())

    def test_missing_manifest_is_a_hard_stop(self):
        with TemporaryDirectory() as directory:
            with self.assertRaises(SystemExit):
                E.approved_codex_frames(Path(directory), minimal_plan())


if __name__ == "__main__":
    unittest.main()
