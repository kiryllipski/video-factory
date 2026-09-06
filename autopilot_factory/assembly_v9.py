#!/usr/bin/env python3
"""Pure timing and retention gates for v9; rendering remains in assembly_v8."""
from __future__ import annotations

from typing import Iterable

import schemas_v9 as S9


TEMPLATE_MARKERS = (
    "i tu zwrot",
    "werdykt:",
)

SPOKEN_CTA_MARKERS = (
    "daj znać w komentarzu",
    "napisz w komentarzu",
    "zostaw komentarz",
    "subskrybuj",
    "zostaw łapkę",
    "zaobserwuj",
    "kliknij obserwuj",
)


def _check(name: str, passed: bool, detail: str = "") -> S9.TimingCheck:
    return S9.TimingCheck(name=name, passed=passed, detail=detail)


def _word_count(script) -> int:
    return len(" ".join(beat.voiceover for beat in script.beats).split())


def duration_tolerance(target: float) -> float:
    return max(2.0, target * 0.08)


def duration_in_lane(lane: str, duration_s: float) -> bool:
    if lane == "core":
        return 18.0 <= duration_s <= 26.0
    return 27.0 <= duration_s <= S9.MAX_V9_ACTUAL_DURATION_S


def build_timing_report(script, plan: S9.RetentionPlan,
                        beat_durations: Iterable[float]) -> S9.RetentionTimingReport:
    durs = [float(value) for value in beat_durations]
    if len(durs) != len(script.beats):
        raise ValueError("beat duration count must match script beats")
    if max(plan.first_proof_beat, plan.turn_beat, plan.payoff_beat) >= len(durs):
        raise ValueError("retention beat index is outside script")

    timings: list[S9.BeatTiming] = []
    cursor = 0.0
    for idx, (beat, dur) in enumerate(zip(script.beats, durs)):
        timings.append(S9.BeatTiming(
            beat_idx=idx,
            start_s=round(cursor, 3),
            end_s=round(cursor + dur, 3),
            duration_s=round(dur, 3),
            act=beat.act,
        ))
        cursor += dur

    actual = round(cursor, 3)
    planned = round(sum(float(beat.dur_s) for beat in script.beats), 3)
    words = _word_count(script)
    proof_s = timings[plan.first_proof_beat].start_s
    turn_s = timings[plan.turn_beat].start_s
    payoff_s = timings[plan.payoff_beat].start_s
    hook_indices = [idx for idx, beat in enumerate(script.beats) if beat.act == "hook"]
    hook_end = timings[max(hook_indices)].end_s if hook_indices else actual
    max_beat = max(durs) if durs else 0.0
    narration = " ".join(beat.voiceover.casefold() for beat in script.beats)

    # Natural Polish TTS is materially slower than the retired atempo path. Deep
    # stories need a second evidence event, not an inflated word count.
    lane_word_min, lane_word_max = ((32, 60) if plan.duration_lane == "core" else (30, 60))
    lane_max_beat = 4.2 if plan.duration_lane == "core" else 5.0
    tolerance = duration_tolerance(plan.target_duration_s)
    checks = [
        _check(
            "planned_target",
            abs(planned - plan.target_duration_s) <= tolerance,
            f"planned={planned:.3f}s target={plan.target_duration_s:.3f}s tolerance={tolerance:.3f}s",
        ),
        _check(
            "actual_target",
            abs(actual - plan.target_duration_s) <= tolerance,
            f"actual={actual:.3f}s target={plan.target_duration_s:.3f}s tolerance={tolerance:.3f}s",
        ),
        _check(
            "duration_lane",
            duration_in_lane(plan.duration_lane, actual),
            f"lane={plan.duration_lane} actual={actual:.3f}s",
        ),
        _check(
            "word_budget",
            lane_word_min <= words <= lane_word_max,
            f"lane={plan.duration_lane} words={words} allowed={lane_word_min}-{lane_word_max}",
        ),
        _check("hook_end", hook_end <= 3.2, f"hook_end={hook_end:.3f}s ceiling=3.200s"),
        _check("first_proof", proof_s <= 3.0, f"first_proof={proof_s:.3f}s ceiling=3.000s"),
        _check(
            "turn_position",
            turn_s <= actual * 0.45,
            f"turn={turn_s:.3f}s ceiling={actual * 0.45:.3f}s",
        ),
        _check(
            "payoff_position",
            payoff_s <= actual * 0.78,
            f"payoff={payoff_s:.3f}s ceiling={actual * 0.78:.3f}s",
        ),
        _check(
            "max_beat_duration",
            max_beat <= lane_max_beat,
            f"max_beat={max_beat:.3f}s ceiling={lane_max_beat:.3f}s",
        ),
        _check(
            "template_markers",
            not any(marker in narration for marker in TEMPLATE_MARKERS),
            "forbidden=" + ", ".join(marker for marker in TEMPLATE_MARKERS if marker in narration),
        ),
        _check(
            "spoken_cta",
            not plan.spoken_cta and not any(marker in narration for marker in SPOKEN_CTA_MARKERS),
            "declared=" + str(plan.spoken_cta) + "; detected="
            + ", ".join(marker for marker in SPOKEN_CTA_MARKERS if marker in narration),
        ),
    ]

    return S9.RetentionTimingReport(
        passed=all(item.passed for item in checks),
        lane=plan.duration_lane,
        target_duration_s=plan.target_duration_s,
        planned_duration_s=planned,
        actual_narration_s=actual,
        word_count=words,
        first_proof_s=proof_s,
        turn_s=turn_s,
        payoff_s=payoff_s,
        beats=timings,
        checks=checks,
    )


def mp4_duration_check(plan: S9.RetentionPlan, actual_s: float) -> S9.TimingCheck:
    tolerance = duration_tolerance(plan.target_duration_s)
    passed = (
        duration_in_lane(plan.duration_lane, actual_s)
        and abs(actual_s - plan.target_duration_s) <= tolerance
    )
    return _check(
        "v9_mp4_duration",
        passed,
        f"lane={plan.duration_lane} actual={actual_s:.3f}s "
        f"target={plan.target_duration_s:.3f}s tolerance={tolerance:.3f}s",
    )
