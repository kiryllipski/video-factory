#!/usr/bin/env python3
"""Pure contract tests for v8 gates; no API or media calls."""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import engine_v8 as E
import schemas_v8 as S


def pack() -> S.ResearchPack:
    sources = [
        S.ResearchSource(
            id=f"SRC-{i:02d}",
            title=f"Authoritative source number {i}",
            publisher="Official Publisher",
            url=f"https://example.org/source-{i}",
            source_type="official_guideline",
            year=2025,
            evidence_summary="Источник прямо поддерживает ограниченное утверждение для теста.",
        )
        for i in range(1, 4)
    ]
    claims = [
        S.ResearchClaim(
            id="CLM-01",
            neutral_claim="Проверяемое центральное утверждение в заданных условиях.",
            verdict="supported",
            confidence="high",
            source_ids=["SRC-01", "SRC-02"],
            allowed_wording="В заданных условиях наблюдается проверяемый эффект.",
            forbidden_wording=["гарантирует всем"],
            limitations="Вывод относится только к описанным условиям.",
            risk_level="high",
            display_source=True,
        ),
        S.ResearchClaim(
            id="CLM-02",
            neutral_claim="Второе подтверждённое утверждение для сценария.",
            verdict="supported",
            confidence="high",
            source_ids=["SRC-02"],
            allowed_wording="Второй факт можно сформулировать без усиления.",
            limitations="Не переносить на другие продукты.",
            risk_level="medium",
        ),
        S.ResearchClaim(
            id="CLM-03",
            neutral_claim="Третье условное утверждение для сценария.",
            verdict="conditional",
            confidence="medium",
            source_ids=["SRC-03"],
            allowed_wording="Эффект возможен при указанном условии.",
            limitations="Условие обязательно должно остаться в формулировке.",
            risk_level="medium",
        ),
        S.ResearchClaim(
            id="CLM-04",
            neutral_claim="Популярная, но отвергнутая версия объяснения.",
            verdict="rejected",
            confidence="high",
            source_ids=["SRC-01"],
            allowed_wording="Эту версию нельзя использовать как установленный факт.",
            forbidden_wording=["это доказано"],
            limitations="Claim сохранён только как запрет.",
            risk_level="low",
        ),
    ]
    return S.ResearchPack(
        topic="Тестовая бытовая тема",
        viewer_question="Что на самом деле происходит в бытовой ситуации?",
        recommended_angle="Проверить одно убеждение через наблюдаемый механизм.",
        evidence_summary="Три авторитетных источника задают узкие границы допустимого вывода.",
        sources=sources,
        claims=claims,
    )


def script() -> S.Script:
    beats = [
        S.Beat(voiceover="Ты делаешь это каждый день.", on_screen_text="Каждый день",
               visual_cue="бытовой контекст", dur_s=1.3, act="hook", emphasis="день"),
        S.Beat(voiceover="Но привычное объяснение неверно.", on_screen_text="Объяснение неверно",
               visual_cue="контраст", dur_s=1.3, act="hook", emphasis="неверно"),
        S.Beat(voiceover="В заданных условиях наблюдается проверяемый эффект.",
               on_screen_text="Проверяемый эффект", visual_cue="доказательство", dur_s=2.7,
               act="body", emphasis="эффект", claim_ids=["CLM-01"]),
        S.Beat(voiceover="Источник описывает границы вывода.", on_screen_text="Есть границы",
               visual_cue="источник", dur_s=2.5, act="body", emphasis="границы",
               claim_ids=["CLM-01"]),
        S.Beat(voiceover="Второй факт можно сформулировать без усиления.",
               on_screen_text="Без усиления", visual_cue="вторая улика", dur_s=2.6,
               act="body", emphasis="усиления", claim_ids=["CLM-02"]),
        S.Beat(voiceover="И вот здесь меняется вывод.", on_screen_text="Меняем вывод",
               visual_cue="поворот", dur_s=2.1, act="body", emphasis="меняется"),
        S.Beat(voiceover="Эффект возможен только при указанном условии.",
               on_screen_text="Важно условие", visual_cue="условие", dur_s=2.8,
               act="body", emphasis="условии", claim_ids=["CLM-03"]),
        S.Beat(voiceover="Поэтому не переносим его на другие случаи.",
               on_screen_text="Не универсально", visual_cue="граница", dur_s=2.5,
               act="body", emphasis="другие", claim_ids=["CLM-03"]),
        S.Beat(voiceover="Сначала проверь условия, потом делай вывод.",
               on_screen_text="Сначала условия", visual_cue="действие", dur_s=2.6,
               act="payoff", emphasis="условия", claim_ids=["CLM-01"]),
        S.Beat(voiceover="Так факт остаётся фактом.", on_screen_text="Факт без мифа",
               visual_cue="финал", dur_s=2.2, act="payoff", emphasis="факт",
               claim_ids=["CLM-01"]),
    ]
    return S.Script(
        rubric="really_true",
        format="myth_autopsy",
        hook="Ты делаешь это каждый день. Но привычное объяснение неверно.",
        poster_text="*Факт* или миф",
        beats=beats,
        overlays=[
            S.Overlay(kind="source", beat_idx=3, label="Official Publisher",
                      source_finding="Источник подтверждает границы вывода",
                      claim_ids=["CLM-01"]),
            S.Overlay(kind="stamp", beat_idx=5, label="ПОВОРОТ",
                      claim_ids=["CLM-02"]),
            S.Overlay(kind="callout", beat_idx=7, label="Только при условии",
                      claim_ids=["CLM-03"]),
        ],
        payload="Сначала проверь условия, потом делай вывод.",
        turn_beat_idx=5,
        payoff_card="Сначала условия — потом вывод",
        cta="",
        total_dur_s=22.6,
        central_claim_id="CLM-01",
        payload_claim_ids=["CLM-01"],
        payoff_claim_ids=["CLM-01"],
    )


def frame_plan(value: S.Script) -> S.FramePlan:
    shots = ["macro", "wide", "medium", "extreme_macro"]
    subjects = ["product", "lifestyle", "science", "ingredient"]
    frames = []
    for i, _beat in enumerate(value.beats):
        frames.append(S.Frame(
            prompt=f"Editorial evidence frame {i}, vertical documentary photography",
            claim="Кадр показывает проверяемую часть общего вывода",
            shot=shots[i % len(shots)],
            subject=subjects[i % len(subjects)],
            beat_from=i,
            beat_to=i,
            motion="ken_burns_in",
            claim_ids=["CLM-01"] if i == 2 else [],
        ))
    return S.FramePlan(grade="clean navy", light="soft daylight", lens="50mm", frames=frames)


class GateTests(unittest.TestCase):
    def test_valid_research_pack(self):
        self.assertEqual(E.research_errors(pack()), [])

    def test_rejected_claim_is_blocked(self):
        value = script()
        value.beats[2].claim_ids = ["CLM-04"]
        self.assertTrue(any("rejected" in x for x in E.script_errors(value, pack())))

    def test_number_without_claim_is_blocked(self):
        value = script()
        value.beats[1].voiceover = "Но привычное объяснение ошибается в 2 раза."
        self.assertTrue(any("число без claim_id" in x for x in E.script_errors(value, pack())))

    def test_high_risk_needs_two_sources(self):
        value = pack()
        value.claims[0].source_ids = ["SRC-01"]
        self.assertTrue(any("двумя источниками" in x for x in E.research_errors(value)))

    def test_absolute_health_wording_is_blocked(self):
        value = script()
        value.beats[2].voiceover = "Эти продукты вызывают абсолютно идентичный ответ."
        self.assertTrue(any("абсолютная формулировка" in x for x in E.script_errors(value, pack())))

    def test_frame_plan_is_one_frame_per_beat(self):
        value = script()
        plan = frame_plan(value)
        self.assertEqual(E.plan_errors(plan, value, pack()), [])
        plan.frames[3].beat_from = 2
        self.assertTrue(any("должны быть 3/3" in x for x in E.plan_errors(plan, value, pack())))

    def test_overlay_label_must_not_duplicate_caption(self):
        value = script()
        value.overlays[2].label = value.beats[7].on_screen_text
        self.assertTrue(any("дублирует субтитр" in x for x in E.script_errors(value, pack())))

    def test_generic_metric_label_is_blocked(self):
        value = script()
        value.overlays[1].kind = "bar"
        value.overlays[1].label = "Энергия"
        value.overlays[1].value = "4500 ккал"
        value.overlays[1].percent = 100
        self.assertTrue(any("общая подпись" in x for x in E.script_errors(value, pack())))

    def test_versus_cannot_compare_same_or_verbose_text(self):
        value = script()
        value.overlays[1].kind = "versus"
        value.overlays[1].label = "Свежие"
        value.overlays[1].value = "Минералы в норме"
        value.overlays[1].label_b = "Заморозка"
        value.overlays[1].value_b = "Минералы в норме"
        errors = E.script_errors(value, pack())
        self.assertTrue(any("одинаковые значения" in x for x in errors))
        self.assertTrue(any("короткие числа" in x for x in errors))

    def test_numeric_callout_is_value_only(self):
        value = script()
        value.overlays[2].kind = "callout"
        value.overlays[2].label = "Уничтожает патогены"
        value.overlays[2].value = "Нагрев до 74°C"
        errors = E.script_errors(value, pack())
        self.assertTrue(any("не должен иметь вторую" in x for x in errors))
        self.assertTrue(any("только число и единицу" in x for x in errors))

    def test_payoff_card_is_short_enough_for_three_lines(self):
        value = script()
        value.payoff_card = "Это слишком длинная финальная карточка и она не поместится в три строки"
        self.assertTrue(any("payoff_card длиннее" in x for x in E.script_errors(value, pack())))

    def test_source_card_title_is_shortened_before_layout(self):
        value = pack()
        value.sources[0].title = "A very long authoritative scientific title that should remain readable on a small vertical source card without being cropped by the renderer"
        cards = E.source_cards(script(), value)
        self.assertLessEqual(len(cards[3]["title"]), 76)
        self.assertTrue(cards[3]["title"].endswith("…"))

    def test_source_card_needs_short_finding(self):
        value = script()
        value.overlays[0].source_finding = ""
        self.assertTrue(any("source_finding" in x for x in E.script_errors(value, pack())))

    def test_source_card_uses_research_pack_metadata(self):
        value = script()
        cards = E.source_cards(value, pack())
        self.assertEqual(cards[3]["source_id"], "SRC-01")
        self.assertEqual(cards[3]["publisher"], "Official Publisher")
        self.assertEqual(cards[3]["year"], "2025")
        self.assertEqual(cards[3]["reference"], "example.org")
        self.assertEqual(cards[3]["finding"], "Источник подтверждает границы вывода")

    def test_source_card_markup_has_seek_safe_entrance(self):
        value = script()
        starts = [i * 2.5 for i in range(len(value.beats))]
        clips, tweens, _ = E.A._overlay_clips(
            value.overlays, starts, [2.5] * len(value.beats), len(value.beats),
            source_cards=E.source_cards(value, pack()),
        )
        html = "".join(clips)
        motion = "".join(tweens)
        self.assertIn("source-card-mode", html)
        self.assertIn("source-finding", html)
        self.assertIn("Official Publisher · 2025", html)
        self.assertIn('class="source-reference">example.org</div>', html)
        self.assertNotIn("Источник: example.org", html)
        self.assertNotIn("Źródło: example.org", html)
        self.assertIn('ease:"power3.out"', motion)
        self.assertIn("scaleX:0", motion)

    def test_headline_ends_on_first_visual_cut(self):
        self.assertEqual(E.A._headline_duration([1.2, 1.4, 2.0], [(0, 0)], True), 1.2)
        self.assertAlmostEqual(E.A._headline_duration([1.2, 1.4, 2.0], [(0, 1)], True), 2.6)

    def test_release_report_records_duration_mismatch_without_rejecting(self):
        value = script()
        package = S.PublishPackage(
            title="Test title",
            description="Context",
            hashtags=["#test", "#zdrowie", "#short"],
            source_urls=[source.url for source in pack().sources],
        )
        compliance = S.ComplianceVerdict(passed=True, cleaned_script=value)
        fact = S.FactReview(passed=True)
        qa = S.QAReport(passed=True, checks=[])
        with TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "out.mp4").touch()
            report = E.release_report(
                run_dir, E._revision(pack(), value), pack(), value, compliance, fact,
                frame_plan(value), qa, package,
                media_meta={"duration_s": 40.0, "width": 1080, "height": 1920, "audio_codec": "aac"},
                visual_qa=[{"passed": True}, {"passed": True}, {"passed": True}],
                require_media=True,
            )
        checks = {check.name: check for check in report.checks}
        self.assertIn("duration_observed", checks)
        self.assertTrue(checks["duration_observed"].passed)


if __name__ == "__main__":
    unittest.main()
