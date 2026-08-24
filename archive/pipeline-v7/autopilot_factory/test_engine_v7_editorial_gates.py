"""Regression tests for the editorial rules promoted from the v8 review into Polish v7."""
from __future__ import annotations

import unittest
from types import SimpleNamespace

import engine_v7 as V7
import schemas_v7 as S


class EditorialGateTests(unittest.TestCase):
    def test_numeric_callout_must_be_value_only(self):
        overlay = S.Overlay(kind="callout", beat_idx=2, label="Zabija patogeny", value="74°C")
        self.assertFalse(overlay.label == "")
        self.assertTrue(V7._compact_numeric_value(overlay.value))

    def test_source_card_requires_traceable_metadata(self):
        partial = S.Overlay(kind="source", beat_idx=3, label="USDA")
        cards = V7.source_cards_from_script(SimpleNamespace(overlays=[partial]))
        self.assertEqual(cards, {})

        complete = S.Overlay(
            kind="source", beat_idx=3, label="USDA", source_finding="Sok i cola mają podobną ilość cukru",
            source_title="FoodData Central", source_publisher="USDA", source_year="2025",
            source_reference="fdc.nal.usda.gov",
        )
        cards = V7.source_cards_from_script(SimpleNamespace(overlays=[complete]))
        self.assertEqual(cards[3]["reference_label"], "Źródło")
        self.assertEqual(cards[3]["title"], "FoodData Central")

    def test_comparison_values_must_be_short_and_different(self):
        self.assertTrue(V7._compact_comparison_value("27 g"))
        self.assertFalse(V7._compact_comparison_value("taka sama zawartość cukru w porcji"))
        self.assertEqual(V7._overlay_norm("26 g"), V7._overlay_norm("26 g"))


if __name__ == "__main__":
    unittest.main()
