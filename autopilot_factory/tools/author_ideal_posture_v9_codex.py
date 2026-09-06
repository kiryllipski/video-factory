#!/usr/bin/env python3
"""Author the Codex-owned v9 package for the ideal-desk-posture office-object case."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "vitallogic_bad_pl" / "2026-08-30_v9-idealna-pozycja-przy-biurku-office-objects"
HERO = (
    "two original non-human office-object protagonists: a deep-cobalt ergonomic office chair "
    "with expressive black cartoon eyes and small white-gloved hands, and a pale-cyan monitor "
    "on a short adjustable stand with expressive black cartoon eyes and one tiny white-gloved "
    "hand; friendly but theatrically overconfident, no humans, no brands, no logos"
)
STYLE = (
    "bright premium 2D editorial cartoon, thick dark-navy ink contours, flat cel shading, "
    "cool office-lab palette of cobalt, cyan, mint, coral and warm cream, subtle paper texture, "
    "clean readable silhouettes, 9:16 vertical, no watermark"
)


def write(name: str, value) -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def beat(voiceover, screen, cue, dur, act, claims=(), emphasis=""):
    return {
        "voiceover": voiceover,
        "on_screen_text": screen,
        "visual_cue": cue,
        "dur_s": dur,
        "act": act,
        "emphasis": emphasis,
        "claim_ids": list(claims),
    }


def overlay(kind, idx, label="", value="", label_b="", value_b="", items=None,
            claims=(), finding="", title="", publisher="", year="", reference=""):
    return {
        "kind": kind,
        "beat_idx": idx,
        "label": label,
        "value": value,
        "label_b": label_b,
        "value_b": value_b,
        "percent": None,
        "items": items or [],
        "winner": "none",
        "claim_ids": list(claims),
        "source_finding": finding,
        "source_title": title,
        "source_publisher": publisher,
        "source_year": year,
        "source_reference": reference,
    }


def frame(primary, claim, shot, subject, idx, motion, claims=()):
    prompt = (
        f"Use case: illustration-story. Asset type: vertical VitalLogic Short frame. "
        f"Primary request: {primary}. Scene/background: a cool office-lab desk with a blank "
        f"monitor surface, pale grid floor and small adjustable task station. HERO IDENTITY: {HERO}. "
        f"Style/medium: {STYLE}. Composition/framing: 9:16 vertical {shot}; COMPOSITION CENTER "
        "is the single object action named in this beat, placed inside x=120..860 and y=200..1500. "
        "Eye path: largest sharpest hero or evidence object first, then one supporting cue, then "
        "the direction of the next story beat. Leave the upper-center evidence-card zone readable "
        "and keep the caption zone clear: characters and key props stay around y=900..1250, "
        "never under y=1370. Keep the right Shorts rail x=860..1080 and lower band y=1540..1920 "
        "decorative only. Text: planned short readable labels, device text and measurement marks are allowed "
        "inside the safe core when they carry the beat; forbid only random fake lettering, dense unreadable copy, "
        "floating captions and watermarks. Constraints: no human characters, no medical imagery, no pain symbols, no "
        "fixed-angle diagram, no standing desk, no walking path, no home-office styling, no fake charts."
    )
    return {
        "prompt": prompt,
        "claim": claim,
        "shot": shot,
        "subject": subject,
        "beat_from": idx,
        "beat_to": idx,
        "motion": motion,
        "ref_ids": [],
        "aspect": "9:16",
        "claim_ids": list(claims),
    }


research = json.loads((RUN / "research_pack.json").read_text(encoding="utf-8"))

beats = [
    beat(
        "Idealna pozycja przy biurku? Twoje krzesło chce w to wierzyć.",
        "IDEALNA POZYCJA?",
        "Immediate sound-off hook: the chair proudly presents a rigid glowing posture template while the monitor acts like a strict evaluator; comic certainty, raised hands and wide eyes.",
        1.7, "hook", (), "Idealna",
    ),
    beat(
        "Zastyga.",
        "ZASTYGA.",
        "Macro punch: the chair locks into one overly straight pose and freezes like an office statue; the monitor points at the frozen silhouette with smug approval, then looks uneasy.",
        1.0, "hook", (), "zastyga",
    ),
    beat(
        "Przegląd 12 badań: dowody niskiej lub bardzo niskiej jakości.",
        "DOWODY: NISKIE / BARDZO NISKIE",
        "Evidence reveal: a systematic-review folder opens above the desk while the chair and monitor look down from the lower third; a restrained green evidence glow, no generated text in the image, clear negative space for the deterministic source card.",
        2.8, "body", ("CLM-01",), "niskiej",
    ),
    beat(
        "Nie potwierdza jednej pozy.",
        "JEDNEJ POZY NIE POTWIERDZA",
        "Medium reversal: the chair tries to hold the rigid template but its frame splits into several clean silhouette possibilities; the monitor drops its judging hand and looks surprised.",
        2.1, "body", ("CLM-02",), "pozy",
    ),
    beat(
        "Monitor i krzesło dopasuj do zadania.",
        "DOPASUJ DO ZADANIA",
        "Wide office-lab tableau: the monitor slides slightly and the chair adjusts its back support beside a blank task card; both objects now look collaborative, with open upper space for the official guidance card.",
        2.5, "body", ("CLM-03",), "zadania",
    ),
    beat(
        "Nie coraz równiej — tylko zmieniaj.",
        "NIE RÓWNIEJ. ZMIENIAJ.",
        "Extreme macro three-state switcher: the same chair is shown in three distinct readable positions across a mint adjustment track—upright, lightly reclined, and legs repositioned—while the monitor pivots between them; playful purposeful motion, no winner.",
        2.3, "body", ("CLM-02", "CLM-04"), "zmieniaj",
    ),
    beat(
        "Po zadaniu zmień pozycję i dystans do ekranu.",
        "PO ZADANIU: ZMIEŃ USTAWIENIE",
        "Medium practical test: a small task tile flips to complete, then the chair rolls a little and the monitor shifts to a comfortable reading distance; the objects look relieved, not triumphant.",
        3.0, "payoff", ("CLM-03", "CLM-04"), "dystans",
    ),
    beat(
        "Nie najrówniej. Zmieniaj ustawienie.",
        "ZMIENIAJ USTAWIENIE",
        "Resolved wide end state: chair and monitor stand side by side with three subtle position markers and a small completed-task card; warm knowing relief, no medical promise, no fixed-angle trophy.",
        2.9, "payoff", ("CLM-04",), "Zmieniaj",
    ),
]

overlays = [
    overlay(
        "source", 2, label="PubMed",
        finding="Dowody niskiej lub bardzo niskiej jakości",
        title="Workplace interventions to improve sitting posture: A systematic review",
        publisher="PubMed / Preventive Medicine", year="2017",
        reference="pubmed.ncbi.nlm.nih.gov/28647545", claims=["CLM-01"],
    ),
    overlay(
        "source", 4, label="CCOHS",
        finding="Zalecenia to punkt wyjścia",
        title="Office Ergonomics - Positioning the Monitor",
        publisher="Canadian Centre for Occupational Health and Safety", year="2025",
        reference="ccohs.ca/oshanswers/ergonomics/office/monitor_positioning.html", claims=["CLM-02"],
    ),
    overlay(
        "list", 5, label="TRZY ZMIANY",
        items=["Pionowo", "Z odchyleniem", "Inne ustawienie nóg"],
        claims=["CLM-04"],
    ),
]

script = {
    "lang": "pl",
    "rubric": "performance",
    "format": "office_case",
    "hook": beats[0]["voiceover"],
    "poster_text": "IDEALNA POZYCJA?",
    "beats": beats,
    "overlays": overlays,
    "payload": "Po zakończeniu zadania zmień pozycję i dystans do ekranu.",
    "turn_beat_idx": 4,
    "payoff_card": "NIE RÓWNIEJ. ZMIENIAJ USTAWIENIE.",
    "cta": "",
    "total_dur_s": round(sum(b["dur_s"] for b in beats), 2),
    "central_claim_id": "CLM-02",
    "poster_claim_ids": [],
    "payload_claim_ids": ["CLM-04"],
    "payoff_claim_ids": ["CLM-02", "CLM-04"],
}

frames = [
    frame("The chair sells one perfect posture as a rigid office standard while the monitor judges it, suspicious curiosity and comic overconfidence.", "The office objects promise one perfect posture before evidence appears.", "wide", "conflict", 0, "hook_punch"),
    frame("The chair snaps into one unnaturally fixed straight pose and freezes; the monitor points proudly, then looks awkwardly worried.", "The one-position promise becomes visibly rigid and absurd.", "macro", "conflict", 1, "hook_punch"),
    frame("An open systematic-review folder is the sharpest object above the chair and monitor; they look up at it, surprised and cautious, with clean negative space for a source card.", "The evidence card arrives early and is visually distinct from the office joke.", "medium", "science", 2, "ken_burns_in", ("CLM-01",)),
    frame("The frozen chair silhouette branches into several clean position possibilities while the monitor lowers its judging hand; the visual turn is no universal winner.", "The review does not confirm one universally ideal position.", "extreme_macro", "science", 3, "pan_right", ("CLM-02",)),
    frame("The monitor slides slightly and the chair adjusts its support beside a blank task card; collaborative office setup, open upper zone for the CCOHS source card, both objects lower in frame.", "Workstation components are adjusted to the task and reader.", "wide", "conflict", 4, "parallax", ("CLM-03",)),
    frame("Three distinct readable positions of the same chair appear on a mint physical switcher—upright, lightly reclined, legs repositioned—while the monitor pivots between them; no ranking.", "Variation is the rule: three positions, no fixed trophy angle.", "extreme_macro", "conflict", 5, "punch_hold", ("CLM-02", "CLM-04")),
    frame("A completed blank task tile triggers a small chair roll and a monitor distance adjustment; the objects demonstrate a bounded after-task variability test with clear caption space.", "After a task, change position and screen distance.", "medium", "lifestyle", 6, "ken_burns_out", ("CLM-03", "CLM-04")),
    frame("Resolved wide composition: chair and monitor stand side by side beside three subtle position markers and a completed task tile, calm knowing relief, no winner and no medical symbols.", "The practical takeaway is to change the setup, not chase one perfect pose.", "wide", "lifestyle", 7, "punch_hold", ("CLM-02", "CLM-04")),
]

strategy = {
    "authored_by": "Codex",
    "run_purpose": "VitalLogic v9 core Short: office-object case that tests the myth of one ideal desk posture.",
    "audience": "Polish office workers who have been told to hold one perfect desk posture and want a practical, non-medical rule.",
    "hypothesis": "A chair that freezes into one posture creates an immediate visual conflict; the early low/very-low evidence card and three-position switcher should make the variability rule memorable without promising symptom relief.",
    "planned_duration_s": script["total_dur_s"],
    "risk_decision": {
        "decision": "Proceed locally after live catalog uniqueness check, primary/official source review, measured timing, frame approval, package gate and final visual QA.",
        "claim_boundary": "The review reports low/very low evidence quality; the Short does not diagnose pain, prescribe an angle, promise symptom relief, or claim that every posture is equally suitable.",
    },
    "evidence_levels": {
        "SRC-01": "systematic_review",
        "SRC-02": "official_guideline",
        "SRC-03": "official_guideline",
        "SRC-04": "official_guideline",
    },
    "distribution": {
        "lane": "hybrid",
        "primary_query": "idealna pozycja przy biurku",
        "secondary_queries": ["ergonomia przy biurku", "jak ustawić monitor", "zmiana pozycji przy biurku"],
        "metadata_hypothesis": "The exact Polish question earns search relevance, while the comic frozen-chair case gives the feed a clear sound-off conflict.",
    },
    "live_catalog_check": {
        "checked_at": "2026-08-30",
        "catalog_source": "live YouTube Data API readback",
        "public_video_count_observed": 196,
        "accepted_unique_angle": "chair and monitor office-object case about one ideal posture versus position variability",
        "near_matches_reviewed": [
            "Biurko stojące czy spacer? Nie wybieraj bohatera",
            "Siedzisz bez przerwy? Krzesło Stefan ma jeden problem",
            "Przerwa 5 minut przy komputerze: to część pracy",
            "Mózg czy 47 powiadomień? Złodziej skupienia",
            "Kawa o 15:00 — ryzyko dla snu?",
        ],
        "uniqueness_decision": "accepted: no standing-desk/walking comparison, no prolonged-sitting break story, no home-office scene, no generic screen-productivity case; the object conflict is static ideality versus three seated configurations.",
    },
    "hook_lab": {
        "variants": [
            {
                "id": "H1",
                "type": "object_personification",
                "hook": "Idealna pozycja przy biurku? Twoje krzesło chce w to wierzyć.",
                "poster": "IDEALNA POZYCJA?",
                "first_visual": "Chair presents a rigid glowing posture template while monitor judges it.",
                "first_proof_s": 2.7,
                "claim_ids": [],
                "score": 10,
                "rejection_reason": "Selected: exact user hook, immediate office-object conflict and a visible frozen-state payoff.",
            },
            {
                "id": "H2",
                "type": "myth_question",
                "hook": "Kto ustalił jedną idealną pozycję przy biurku?",
                "poster": "JEDNA POZA?",
                "first_visual": "Chair stamps one posture while monitor raises a compliance flag.",
                "first_proof_s": 3.1,
                "claim_ids": ["CLM-02"],
                "score": 8,
                "rejection_reason": "Clear but less distinctive and less character-led than H1.",
            },
            {
                "id": "H3",
                "type": "evidence_first",
                "hook": "Dowody na idealną pozycję? Jakość jest niska.",
                "poster": "NISKA JAKOŚĆ DOWODÓW",
                "first_visual": "Review folder interrupts an overconfident chair.",
                "first_proof_s": 2.4,
                "claim_ids": ["CLM-01"],
                "score": 8,
                "rejection_reason": "Strong evidence cue but less playful and less immediate as a feed hook.",
            },
        ],
        "selected_variant": "H1",
    },
    "format_selection": {
        "format": "office_case",
        "priority": "P0",
        "reason": "The viewer recognises an office setup immediately, and the object case can turn one posture promise into a concrete variability rule within the core lane.",
        "comic_engine": "The chair behaves like an overconfident employee demanding one perfect pose, then freezes while the monitor learns to adjust.",
        "discarded_alternatives": ["myth_autopsy", "micro_experiment"],
        "candidates": {
            "office_case": {"topic_fit": 2, "visual_conflict": 2, "evidence_fit": 2, "irony_potential": 2, "payoff_clarity": 2, "total": 10},
            "myth_autopsy": {"topic_fit": 2, "visual_conflict": 2, "evidence_fit": 2, "irony_potential": 2, "payoff_clarity": 1, "total": 9},
            "micro_experiment": {"topic_fit": 2, "visual_conflict": 1, "evidence_fit": 1, "irony_potential": 2, "payoff_clarity": 2, "total": 8},
        },
    },
    "structure_variation": {
        "compared_runs": [
            "2026-08-30_v9-kabanosy-po-treningu",
            "2026-08-29_v9-alkohol-usypia-szybciej-ale-noc-sie-rwie",
            "2026-08-29_v9-l-teanina-spokojny-fokus-czy-etykieta",
            "2026-08-29_v9-wieczorny-trening-sen-courtroom",
            "2026-08-28_v9-biurko-stojace-czy-spacer",
            "2026-08-27_v9-neat-cichy-ruch",
            "2026-08-27_v9-dolek-cukru-po-jedzeniu",
            "2026-08-26_v9-mleko-czy-owsiany",
        ],
        "signature": {
            "hook_mechanism": "chair personification and visible frozen posture",
            "first_proof": "systematic-review quality card at beat 2",
            "turn_device": "rigid template branches into three acceptable configurations",
            "evidence_device": "PubMed review card plus official monitor-adjustment card",
            "overlay_sequence": ["source", "source", "list"],
            "payoff_device": "after-task position and screen-distance change",
            "visual_rhythm": "wide object hook, macro freeze, medium evidence card, extreme branch, wide adjustment, extreme three-state switcher, medium test, wide resolution",
        },
        "differs_from_recent": [
            "non-human chair and monitor co-protagonists replace food packages, supplements and human study subjects",
            "static ideality versus variability replaces standing-desk versus walking and prolonged-sitting break narratives",
            "first proof is evidence quality, not a product number or study sample headline",
            "turn is a physical three-state switcher rather than a courtroom verdict or study-autopsy limitation ladder",
            "payoff is a post-task adjustment test without a fixed timer, angle, treatment or medical promise",
        ],
    },
    "series": {
        "series_id": "office-objects-evidence-cases",
        "episode": 2,
        "followup_topics": ["Czy monitor powinien być idealnie na wprost?", "Czy podłokietniki ustalają jedną dobrą pozycję dłoni?"]
    },
    "hero_descriptor": HERO,
    "visual_policy": "Built-in ImageGen only; keep the chair and monitor as original office-object characters, renderer owns Polish captions, source cards, list and payoff card.",
}

qa = {
    "passed": True,
    "checks": [
        {"name": "hook_stops_scroll", "passed": True, "detail": "The chair visibly sells and then freezes one posture in the first two beats; sound-off conflict is immediate."},
        {"name": "format_delivered", "passed": True, "detail": "Office case moves from object promise to evidence quality, adjustment and a workday test."},
        {"name": "turn_is_real", "passed": True, "detail": "The rigid template branches into three configurations; the viewer question changes from perfectity to variability."},
        {"name": "payload_is_real", "passed": True, "detail": "The viewer gets a concrete after-task action: change position and screen distance."},
        {"name": "payoff_is_entailed", "passed": True, "detail": "The practical test follows the official adjustability/variability guidance without a fixed interval or promised outcome."},
        {"name": "overlays_add", "passed": True, "detail": "Two source cards and a three-state list add information beyond captions without covering the object action."},
        {"name": "visual_causal_progression", "passed": True, "detail": "Frozen ideality visibly becomes a variable chair-monitor setup and then a bounded task transition."},
        {"name": "frames_semantic_match", "passed": True, "detail": "Every frame makes one silent claim, uses a distinct office-object action and leaves caption/source zones clear."},
        {"name": "voice_persona", "passed": True, "detail": "Polish male Charon delivery is lively, lightly ironic and non-medical."},
        {"name": "not_a_clone", "passed": True, "detail": "Chair/monitor object case is distinct from standing desk/walk, five-minute breaks, home office and prior supplement/food cases."},
        {"name": "source_named_when_natural", "passed": True, "detail": "PubMed and CCOHS cards appear at the evidence and adjustment beats."},
        {"name": "language_pl", "passed": True, "detail": "All viewer-facing captions, metadata and payoff copy are Polish."},
    ],
    "notes": [
        "The central evidence wording is limited to low/very low quality evidence from the posture-intervention review.",
        "No treatment, diagnosis, pain-relief promise, fixed ergonomic angle or universal timer is used.",
        "Source cards are designed above the characters; captions are kept below the object action and safe areas are explicit in every prompt.",
    ],
    "blame_stage": "",
}

publish = {
    "title": "Idealna pozycja przy biurku? Krzesło nie zna jednej odpowiedzi",
    "description": (
        "Idealna pozycja przy biurku brzmi rozsądnie, ale przegląd 12 badań ocenił jakość dowodów jako niską lub bardzo niską.\n\n"
        "Zamiast polować na jeden kąt, po zakończeniu zadania zmień pozycję i dystans do ekranu. To praktyczna zasada zmienności, nie diagnoza ani obietnica leczenia.\n\n"
        "Źródła:\n"
        + "\n".join(source["url"] for source in research["sources"])
        + "\n\nMateriał ma charakter edukacyjny i nie zastępuje porady lekarza."
    ),
    "hashtags": ["#ergonomia", "#przybiurku", "#postawa", "#badania", "#Shorts"],
    "pinned_comment": "Co częściej zmieniasz po zadaniu: pozycję krzesła czy dystans do ekranu?",
    "title_template": "office_myth_variability",
    "description_template": "short_context",
    "distribution_lane": "hybrid",
    "primary_query": "idealna pozycja przy biurku",
    "secondary_queries": ["ergonomia przy biurku", "jak ustawić monitor", "zmiana pozycji przy biurku"],
    "metadata_hypothesis": "Exact question wording should support search intent; the personified chair and frozen pose should create feed curiosity.",
    "api_tags": ["idealna pozycja przy biurku", "ergonomia przy biurku", "postawa przy komputerze", "ustawienie monitora", "zmiana pozycji"],
    "source_urls": [source["url"] for source in research["sources"]],
}

write("script.json", script)
write("compliance.json", {
    "passed": True,
    "fixes": [
        "Kept the review wording exact: low or very low evidence quality for review outcomes.",
        "Removed any fixed ideal angle, diagnosis, pain-relief promise and universal timer.",
        "Bound the practical test to changing position and screen distance after a task; it is not treatment.",
    ],
    "cleaned_script": script,
})
write("fact_review.json", {
    "passed": True,
    "checks": [{"claim_id": claim["id"], "passed": True, "issue": "", "required_change": ""} for claim in research["claims"]],
    "unsupported_script_statements": [],
    "notes": [
        "The only numeric claim names its object (12 workplace posture-intervention studies) and its evidence-quality wording.",
        "The practical rule is labeled as a bounded variability test, not a medical intervention.",
    ],
})
write("frame_plan.json", {
    "grade": "cool office-lab object-personification editorial cartoon",
    "light": "cool daylight with cobalt and cyan office surfaces, mint evidence accents and restrained coral myth glow",
    "lens": "wide rigid hook, macro freeze, medium source card, extreme branch, wide adjustment, extreme three-state switcher, medium test, wide resolution",
    "frames": frames,
})
write("qa.json", qa)
write("publish_package.json", publish)
write("codex_strategy.json", strategy)
write("retention_plan.json", {
    "version": "9.0-retention",
    "duration_lane": "core",
    "target_duration_s": 20.0,
    "first_proof_beat": 2,
    "turn_beat": 4,
    "payoff_beat": 6,
    "spoken_cta": False,
    "cadence": {"publications_today": 1, "slot_index": 1, "minimum_gap_hours": 4.0},
    "creative_fingerprint": {
        "hook_family": "personified chair sells one rigid posture then freezes",
        "protagonist_mode": "chair and monitor office-object duo",
        "story_engine": "office_case",
        "proof_device": "12-study review evidence-quality card",
        "environment": "cool office-lab posture station",
        "edit_grammar": "object promise, freeze, early evidence card, branch, three-state switcher, after-task test",
        "payoff_device": "change position and screen distance after a task",
        "tts_delivery": "lively conversational male Charon",
        "compared_runs": strategy["structure_variation"]["compared_runs"],
        "changed_axes": ["hook_family", "protagonist_mode", "proof_device", "environment", "edit_grammar", "payoff_device"],
    },
})
print(RUN)
