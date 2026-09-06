#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import unittest

import youtube as Y


class WarsawCadenceTests(unittest.TestCase):
    def test_summer_slots_are_converted_from_warsaw_to_utc(self):
        start = dt.datetime(2026, 8, 27, 3, 0, tzinfo=dt.timezone.utc)
        self.assertEqual(Y._next_free_slot_utc(set(), start), "2026-08-27T04:00:00Z")

    def test_next_same_day_slot_is_used_after_morning(self):
        start = dt.datetime(2026, 8, 27, 4, 1, tzinfo=dt.timezone.utc)
        self.assertEqual(Y._next_free_slot_utc(set(), start), "2026-08-27T09:00:00Z")

    def test_occupied_slots_advance_within_same_day(self):
        start = dt.datetime(2026, 8, 27, 3, 0, tzinfo=dt.timezone.utc)
        occupied = {"2026-08-27T04:00:00Z", "2026-08-27T09:00:00Z"}
        self.assertEqual(Y._next_free_slot_utc(occupied, start), "2026-08-27T14:00:00Z")

    def test_winter_keeps_six_am_warsaw(self):
        start = dt.datetime(2026, 12, 10, 4, 0, tzinfo=dt.timezone.utc)
        self.assertEqual(Y._next_free_slot_utc(set(), start), "2026-12-10T05:00:00Z")


if __name__ == "__main__":
    unittest.main()
