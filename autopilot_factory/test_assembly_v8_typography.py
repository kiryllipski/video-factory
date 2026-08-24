"""Regression checks for word-safe viewer text in the HyperFrames renderer."""
from __future__ import annotations

import unittest

import assembly_v8 as A


class WordSafeTypographyTests(unittest.TestCase):
    def test_caption_words_are_atomic_and_fit_enabled(self):
        clips, _ = A._caption_clips(
            [[{"text": "najdłuższe", "start": 0.0, "end": 0.4}]],
            [""], [0.0], [0.5], [""],
        )
        self.assertIn('data-fit-min="28"', clips[0])
        self.assertIn('data-word-safe-fit="true"', clips[0])
        self.assertIn('<span id="c0_w0" class="word">najdłuższe</span>', clips[0])

    def test_fallback_caption_words_are_atomic_and_fit_enabled(self):
        clips, _ = A._caption_clips([[]], ["bardzo długie słowo"], [0.0], [1.0], [""])
        self.assertIn('data-word-safe-fit="true"', clips[0])
        self.assertIn('<span class="word">bardzo</span>', clips[0])
        self.assertIn('<span class="word">długie</span>', clips[0])

    def test_renderer_does_not_force_break_word_for_critical_text(self):
        self.assertIn('[data-word-safe-fit]', A._CSS)
        self.assertNotIn('overflow-wrap:break-word', A._CSS)

    def test_generated_html_reduces_font_size_for_whole_word_overflow(self):
        html, _ = A._build_html(
            [(0, 0)], ["ken_burns_in"], [[]], [""], [0.0], [1.0], [],
            1.0, "", 0.0, "", 0.0, [""],
        )
        self.assertIn('const tooLarge=function()', html)
        self.assertIn('data-word-safe-fit', html)
        self.assertIn('size-=2', html)


if __name__ == "__main__":
    unittest.main()
