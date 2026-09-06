#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import assembly_v9 as A9
import engine_v8 as E8
import engine_v9 as E9
import schemas_v9 as S9
from publishers import prepublisher


def _plan(**overrides) -> S9.RetentionPlan:
    value = {
        "version": "9.0-retention",
        "duration_lane": "core",
        "target_duration_s": 20.4,
        "first_proof_beat": 1,
        "turn_beat": 3,
        "payoff_beat": 6,
        "spoken_cta": False,
        "cadence": {
            "publications_today": 4,
            "slot_index": 2,
            "minimum_gap_hours": 4.0,
        },
        "creative_fingerprint": {
            "hook_family": "direct object proof",
            "protagonist_mode": "topic object",
            "story_engine": "comment answer",
            "proof_device": "household comparison",
            "environment": "kitchen macro",
            "edit_grammar": "proof then state changes",
            "payoff_device": "single practical rule",
            "tts_delivery": "lively conversational",
            "compared_runs": [f"run-{idx}" for idx in range(8)],
            "changed_axes": ["hook_family", "proof_device", "environment"],
        },
    }
    value.update(overrides)
    return S9.RetentionPlan(**value)


def _script(marker: str = ""):
    lines = [
        "Osiem szklanek brzmi jak prosty rozkaz",
        "Zupa też wnosi wodę do całego dnia",
        "Liczy się płyn z napojów oraz jedzenia",
        "Ruch i upał zmieniają twoją potrzebę",
        "Jedna liczba nie opisuje każdego dnia",
        "Spójrz na pragnienie oraz warunki dnia",
        "Miej wodę pod ręką podczas pracy",
        "Dostosuj picie do ruchu i temperatury",
    ]
    if marker:
        lines[4] = marker
    acts = ["hook", "hook", "body", "body", "body", "body", "payoff", "payoff"]
    durs = [1.5, 1.4, 2.5, 3.0, 3.0, 3.0, 3.0, 3.0]
    beats = [
        SimpleNamespace(voiceover=text, act=act, dur_s=dur)
        for text, act, dur in zip(lines, acts, durs)
    ]
    return SimpleNamespace(beats=beats)


class TimingReportTests(unittest.TestCase):
    def test_core_report_passes_measured_contract(self):
        script = _script()
        durs = [beat.dur_s for beat in script.beats]
        report = A9.build_timing_report(script, _plan(), durs)
        self.assertTrue(report.passed)
        self.assertLessEqual(report.first_proof_s, 3.0)
        self.assertEqual(report.word_count, 50)

    def test_deep_lane_hard_cap_is_35_seconds(self):
        self.assertTrue(A9.duration_in_lane("deep", 35.0))
        self.assertFalse(A9.duration_in_lane("deep", 35.001))

    def test_template_marker_fails(self):
        script = _script("I tu zwrot: jedna liczba nie wystarcza")
        report = A9.build_timing_report(
            script, _plan(), [beat.dur_s for beat in script.beats]
        )
        failed = {item.name for item in report.checks if not item.passed}
        self.assertIn("template_markers", failed)

    def test_spoken_cta_text_fails_even_when_declared_false(self):
        script = _script("Daj znać w komentarzu, którą opcję wybierasz")
        report = A9.build_timing_report(
            script, _plan(), [beat.dur_s for beat in script.beats]
        )
        failed = {item.name for item in report.checks if not item.passed}
        self.assertIn("spoken_cta", failed)

    def test_cadence_slot_cannot_exceed_daily_count(self):
        with self.assertRaises(ValueError):
            _plan(cadence={
                "publications_today": 1,
                "slot_index": 2,
                "minimum_gap_hours": 4.0,
            })

    def test_creative_comparison_rejects_duplicate_runs(self):
        fingerprint = _plan().creative_fingerprint.model_dump()
        fingerprint["compared_runs"] = ["same-run"] * 8
        with self.assertRaises(ValueError):
            S9.CreativeFingerprint(**fingerprint)

    def test_v9_script_filter_does_not_recurse_when_installed_on_v8(self):
        original = E8.script_errors
        try:
            E8.script_errors = E9.v9_script_errors
            with mock.patch.object(
                E9,
                "V8_SCRIPT_ERRORS",
                return_value=[
                    "плановый хронометраж 20.0с вне 22–36с",
                    "слов в озвучке 42 вне диапазона 80–150",
                    "unsupported claim",
                ],
            ):
                self.assertEqual(E9.v9_script_errors(object(), object()), ["unsupported claim"])
        finally:
            E8.script_errors = original


class PublisherGateTests(unittest.TestCase):
    def test_failed_release_gate_blocks_modern_run(self):
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder)
            (run / "run_meta.json").write_text(
                json.dumps({"pipeline_version": "9.0-retention"}), encoding="utf-8"
            )
            (run / "release_gate.json").write_text(
                json.dumps({
                    "passed": False,
                    "checks": [{"name": "v9_mp4_duration", "passed": False}],
                }),
                encoding="utf-8",
            )
            (run / "publish_package.json").write_text(
                json.dumps({"title": "Test", "description": "Test", "hashtags": []}),
                encoding="utf-8",
            )
            report = prepublisher.inspect_run(run, lang="pl")
            codes = {item["code"] for item in report["issues"]}
            self.assertTrue(report["blocks_publication"])
            self.assertIn("release_gate_failed", codes)


if __name__ == "__main__":
    unittest.main()
