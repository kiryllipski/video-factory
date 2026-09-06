#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import audio_agent as A


class _Models:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = 0

    def generate_content(self, **_kwargs):
        self.calls += 1
        return next(self.responses)


def _empty_response():
    return SimpleNamespace(candidates=None, prompt_feedback=None, usage_metadata=None)


def _audio_response(payload: bytes):
    part = SimpleNamespace(inline_data=SimpleNamespace(data=payload))
    content = SimpleNamespace(parts=[part])
    candidate = SimpleNamespace(content=content, finish_reason="STOP")
    return SimpleNamespace(candidates=[candidate], prompt_feedback=None, usage_metadata=None)


class AudioRetryTests(unittest.TestCase):
    def test_empty_responses_are_retried_before_wav_write(self):
        models = _Models([_empty_response(), _empty_response(), _audio_response(b"\x00\x00" * 24)])
        previous_client = A._client
        previous_cost = A._cost
        A._client = SimpleNamespace(models=models)
        A._cost = None
        try:
            with tempfile.TemporaryDirectory() as folder, mock.patch.object(A.time, "sleep"):
                out = Path(folder) / "voice.wav"
                result = A.generate_speech("Cześć", out=str(out))
                self.assertTrue(out.is_file())
                self.assertTrue(result.startswith(b"RIFF"))
                self.assertEqual(models.calls, 3)
        finally:
            A._client = previous_client
            A._cost = previous_cost


if __name__ == "__main__":
    unittest.main()
