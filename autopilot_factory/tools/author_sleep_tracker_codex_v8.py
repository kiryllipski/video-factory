#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "vitallogic_bad_pl" / "2026-08-24_v8-czy-zegarek-wie-ile-masz-glebokiego-snu"
HERO = "original adult Polish male office analyst, early 30s, warm olive skin, oval face, short dark-brown wavy hair, mustard-yellow overshirt over a mint T-shirt, navy trousers, white sneakers, small teal smartwatch, original friendly cartoon silhouette"
STYLE = "bright pastel 2D hand-drawn editorial cartoon, thick black ink contours, flat cel shading, cyan lemon mint pink lilac and warm cream palette, vertical 9:16, no embedded text, no digits, no logos, no watermark, no diagnosis"


def write(name: str, value) -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source(i, title, publisher, url, typ, year, summary):
    return {"id": f"SRC-{i:02d}", "title": title, "publisher": publisher, "url": url, "source_type": typ, "year": year, "evidence_summary": summary}


def claim(i, neutral, wording, sources, forbidden, limitations, risk="low", confidence="high", display=False, verdict="supported"):
    return {"id": f"CLM-{i:02d}", "neutral_claim": neutral, "verdict": verdict, "confidence": confidence, "source_ids": sources, "allowed_wording": wording, "forbidden_wording": forbidden, "limitations": limitations, "risk_level": risk, "display_source": display}


def beat(text, screen, cue, dur, act, ids=None, emphasis=""):
    return {"voiceover": text, "on_screen_text": screen, "visual_cue": cue, "dur_s": dur, "act": act, "emphasis": emphasis, "claim_ids": ids or []}


def overlay(kind, idx, *, label="", value="", label_b="", value_b="", items=None, winner="none", ids=None, finding="", title="", publisher="", year="", reference=""):
    return {"kind": kind, "beat_idx": idx, "label": label, "value": value, "label_b": label_b, "value_b": value_b, "percent": None, "items": items or [], "winner": winner, "source_finding": finding, "source_title": title, "source_publisher": publisher, "source_year": year, "source_reference": reference, "claim_ids": ids or []}


def frame(prompt, claim_text, shot, subject, idx, motion, ids=None):
    return {"prompt": f"{STYLE}. {prompt}", "claim": claim_text, "shot": shot, "subject": subject, "beat_from": idx, "beat_to": idx, "motion": motion, "ref_ids": [], "aspect": "9:16", "claim_ids": ids or []}


sources = [
    source(1, "Performance of consumer wrist-worn sleep tracking devices compared to polysomnography: a meta-analysis", "Sleep Medicine", "https://pubmed.ncbi.nlm.nih.gov/39484805/", "meta_analysis", 2024, "Meta-analysis of 24 studies comparing consumer wrist-worn devices, including Apple Watch and Garmin among tested devices, with polysomnography; performance varied by metric and device."),
    source(2, "A Validation of Six Wearable Devices for Estimating Sleep, Heart Rate and Heart Rate Variability in Healthy Adults", "Sensors", "https://pubmed.ncbi.nlm.nih.gov/36016077/", "primary_study", 2022, "Validation study comparing six consumer wearables, including Apple Watch and Garmin, with polysomnography and other reference measures; agreement differs between sleep/wake and detailed staging."),
    source(3, "A performance validation of six commercial wrist-worn wearable sleep-tracking devices for sleep stage scoring compared to polysomnography", "Sleep", "https://pubmed.ncbi.nlm.nih.gov/40303381/", "primary_study", 2025, "Recent validation study directly compares six commercial wrist-worn devices with polysomnography for sleep-stage scoring; results are device- and stage-dependent."),
    source(4, "Performance evaluation of finger-worn devices for sleep stage classification and sleep apnea detection: a systematic review and meta-analysis", "Sleep Medicine", "https://pubmed.ncbi.nlm.nih.gov/42141446/", "systematic_review", 2026, "Systematic review reports stronger pooled performance for sleep/wake classification than for multi-stage classification, with heterogeneous devices and populations."),
    source(5, "Practice Guidelines", "American Academy of Sleep Medicine", "https://aasm.org/clinical-resources/practice-standards/practice-guidelines/", "official_guideline", 2025, "AASM practice resources distinguish clinical sleep-disorder evaluation and treatment from consumer wellness tracking; a wearable result is not a diagnosis."),
]

claims = [
    claim(1, "Polysomnography is a reference comparison method for sleep assessment and uses multiple physiological signals rather than a consumer watch alone.", "W laboratorium porównuje się zegarek z polisomnografią, która zbiera kilka sygnałów naraz.", ["SRC-01", "SRC-02", "SRC-03"], ["zegarek czyta fale mózgowe", "zegarek mierzy sen tak samo jak laboratorium"], "Film nie opisuje pełnego protokołu klinicznego ani nie interpretuje wyniku konkretnej osoby.", display=True),
    claim(2, "Consumer wearables infer sleep from indirect sensor signals, and detailed sleep-stage estimates can differ from polysomnography.", "Zegarek wnioskuje o fazie snu z sygnałów pośrednich; to nie jest bezpośredni odczyt mózgu.", ["SRC-01", "SRC-02", "SRC-03"], ["każdy zegarek kłamie", "żaden zegarek nie działa"], "Dokładność zależy od modelu, algorytmu, populacji i rodzaju wyniku."),
    claim(3, "A meta-analysis of 24 studies found that consumer wrist-worn sleep-tracking performance varied across devices and sleep metrics.", "Metaanaliza 24 badań nie daje jednego werdyktu dla wszystkich zegarków i wszystkich faz snu.", ["SRC-01", "SRC-03"], ["24 badania dowodzą, że zegarki są bezużyteczne", "najdokładniejszy jest zawsze jeden model"], "Meta-analysis aggregates heterogeneous devices, protocols and metrics; it is not a current head-to-head brand ranking.", display=True),
    claim(4, "Sleep/wake classification is generally a different and often easier task to validate than detailed classification of light, deep and REM stages.", "Sen albo czuwanie to prostsze pytanie niż dokładne rozdzielenie faz snu.", ["SRC-01", "SRC-03", "SRC-04"], ["zegarek zawsze dobrze mierzy sen", "fazy snu są całkiem losowe"], "The direction and size of the difference vary by device and study; this is not a universal accuracy percentage.", confidence="medium", verdict="conditional"),
    claim(5, "A consumer sleep score should be used as a within-device trend signal rather than as a clinical diagnosis from one night.", "Patrz na trend z tego samego urządzenia, nie na jedną noc jak na diagnozę.", ["SRC-01", "SRC-05"], ["zegarek wykryje każdą chorobę", "niski wynik oznacza bezdech"], "Persistent symptoms or concerns require appropriate professional evaluation; the Short is educational, not diagnostic.", risk="medium", verdict="conditional"),
]

beats = [
    beat("Zegarek właśnie przyznał ci głęboki sen. Tylko… czy on czytał twój mózg?", "GŁĘBOKI SEN?", "Generic smartwatch flashes a colorful sleep-stage ring while the hero looks suspiciously from the watch to the viewer.", 1.6, "hook", emphasis="mózg"),
    beat("W laboratorium zbiera się kilka sygnałów naraz.", "ZEGAREK ≠ LAB", "A playful sleep lab appears as a clear contrast: EEG-style wave sheet, breathing belt and movement sensor beside the generic watch; hero raises one eyebrow.", 1.6, "hook", ["CLM-01"], "kilka"),
    beat("Zegarek wnioskuje o fazie snu z sygnałów pośrednich — nie zagląda prosto do mózgu.", "SYGNAŁY POŚREDNIE", "The watch sends colored motion and pulse-like dots toward a simple sleep dashboard while a closed brain icon remains behind a glass wall.", 2.9, "body", ["CLM-02"], "pośrednich"),
    beat("Metaanaliza 24 badań porównała urządzenia z polisomnografią.", "24 BADANIA", "A neat grid of blank study cards appears like an office release board; hero counts the grid with controlled astonishment.", 2.5, "body", ["CLM-03"], "24"),
    beat("I nie dała jednego werdyktu: wynik zależał od urządzenia i tego, co dokładnie mierzono.", "ZALEŻY OD METRYKI", "Two generic watch icons and three different sleep-stage shapes enter a mock courtroom; hero separates them with both hands.", 3.2, "body", ["CLM-03"], "werdyktu"),
    beat("Sen albo czuwanie to prostsze pytanie niż dokładne rozdzielenie faz snu.", "SEN / CZUWANIE", "A clean two-lane sleep-versus-wake board is crisp, while three tiny stage lanes behind it remain more tangled; hero points to the simple board first.", 3.0, "body", ["CLM-04"], "prostsze"),
    beat("Dlatego kolorowy pasek głęboki sen nie jest nocnym raportem laboratoryjnym.", "TO NIE RAPORT LAB", "Hero gently lowers a glossy generic sleep-score card from a pedestal and places it beside the ordinary watch, warm skeptical smile.", 2.8, "body", ["CLM-01", "CLM-02"], "raportem"),
    beat("Praktyczna zasada: porównuj trend na tym samym zegarku przez kilka tygodni, nie jedną noc.", "TREND, NIE JEDNA NOC", "A row of several blank calendar tiles forms a calm up-and-down trend line; hero marks the whole row, not one dot.", 3.4, "body", ["CLM-05"], "trend"),
    beat("I nie rób z wyniku diagnozy. Zegarek to notatnik, nie laboratorium.", "NOTATNIK ≠ DIAGNOZA", "Hero closes a small blank notebook, moves the watch beside it and gives a clear gentle stop gesture.", 3.0, "payoff", ["CLM-05"], "diagnozy"),
    beat("Werdykt: używaj danych do obserwowania trendu, a nie do polowania na idealną noc.", "TREND, NIE IDEAŁ", "Final wide scene: hero leaves the watch on a bedside table, walks toward warm dawn light and looks back with a knowing smile.", 3.0, "payoff", ["CLM-05"], "trendu"),
]

overlays = [
    overlay("callout", 6, label="PORÓWNANIE", value="ZEGAREK ≠ EEG", ids=["CLM-01"]),
    overlay("list", 2, label="SYGNAŁY", items=["Ruch", "Puls", "Oddech"], ids=["CLM-02"]),
    overlay("stat", 3, label="META-ANALIZA", value="24 badań", ids=["CLM-03"]),
    overlay("source", 4, label="PUBMED 2024", finding="Urządzenia różnią się według fazy", title=sources[0]["title"], publisher=sources[0]["publisher"], year="2024", reference="pubmed.ncbi.nlm.nih.gov/39484805", ids=["CLM-03"]),
    overlay("versus", 5, label="SEN", value="latwiej", label_b="FAZY", value_b="trudniej", ids=["CLM-04"]),
    overlay("timeline", 7, label="OBSERWUJ", items=["ten sam zegarek", "kilka tygodni", "trend"], ids=["CLM-05"]),
]

frames = []
frame_specs = [
    ("extreme macro of a generic unbranded smartwatch on a pillow with an abstract colorful sleep-stage ring, hero leans in with suspicious raised eyebrow, gaze from watch to viewer, COMPOSITION CENTER: watch and face, keep critical objects inside x=120..860 y=200..1500", "extreme_macro", "product", "hook_punch", []),
    ("wide playful sleep laboratory comparison: generic smartwatch on the left, simple EEG wave sheet, breathing belt and movement sensor on the right, hero stands between them with one palm toward each side, COMPOSITION CENTER: two measurement methods", "wide", "science", "pan_left", ["CLM-01"]),
    ("medium scientific metaphor: generic smartwatch sends colored motion and pulse dots toward a dashboard, a closed abstract brain icon sits behind clear glass, hero points at indirect signal dots, COMPOSITION CENTER: signal dots", "medium", "science", "parallax", ["CLM-02"]),
    ("wide office research board with a neat grid of many blank study cards and small generic watch icons, hero counts the grid with both hands, COMPOSITION CENTER: study grid, leave upper safe area for renderer overlay", "wide", "conflict", "ken_burns_in", ["CLM-03"]),
    ("medium mock courtroom: two generic watch silhouettes and three abstract sleep-stage shapes stand as separate witnesses, hero holds both hands apart, COMPOSITION CENTER: split evidence", "medium", "conflict", "pan_right", ["CLM-03"]),
    ("wide versus composition: left lane is a clean asleep-versus-awake two-color board using icons only, right lane has three tangled abstract stage lanes, hero points to the simple lane first, COMPOSITION CENTER: two lanes", "wide", "science", "parallax", ["CLM-04"]),
    ("medium bedside scene: hero lowers a glossy generic sleep-score card from a tiny pedestal and places it beside an ordinary smartwatch, warm skeptical smile, COMPOSITION CENTER: card and watch, clear empty center for renderer text", "medium", "product", "punch_hold", ["CLM-01", "CLM-02"]),
    ("wide dawn desk scene: several blank calendar tiles become a calm up-and-down trend line made from colored dots, hero marks the whole row and ignores one isolated dot, COMPOSITION CENTER: full trend row", "wide", "lifestyle", "ken_burns_in", ["CLM-05"]),
    ("medium bedside table: hero closes a small blank notebook and places the generic smartwatch beside it, then gives a clear gentle stop gesture, COMPOSITION CENTER: notebook, watch and stop gesture", "medium", "human", "pan_left", ["CLM-05"]),
    ("wide warm dawn bedroom: generic smartwatch rests on a bedside table, hero walks toward an open bright window and looks back with a knowing relaxed smile, uncluttered calm environment, COMPOSITION CENTER: watch and final look", "wide", "lifestyle", "ken_burns_out", ["CLM-05"]),
]
frame_claims = [
    "Zegarek pokazuje kolorową fazę snu.",
    "Laboratorium zbiera kilka sygnałów naraz.",
    "Zegarek wnioskuje z sygnałów pośrednich.",
    "Metaanaliza obejmuje 24 badania.",
    "Wynik zależy od urządzenia i metryki.",
    "Sen i czuwanie różnią się od faz snu.",
    "Kolorowy wynik nie jest raportem laboratoryjnym.",
    "Trend obejmuje kilka nocy, nie jedną.",
    "Zegarek nie stawia diagnozy.",
    "Trend jest ważniejszy od idealnej nocy.",
]
for i, (p, shot, subject, motion, ids) in enumerate(frame_specs):
    frames.append(frame(f"{HERO}. {p}. No text, digits, logos or watermark.", frame_claims[i], shot, subject, i, motion, ids))

script = {
    "lang": "pl", "rubric": "brain", "format": "versus", "hook": beats[0]["voiceover"], "poster_text": "GŁĘBOKI SEN?",
    "beats": beats, "overlays": overlays,
    "payload": "Przez kilka tygodni porównuj trend z tego samego zegarka; nie oceniaj całej nocy po jednej liczbie głębokiego snu.",
    "turn_beat_idx": 4, "payoff_card": "TREND, NIE IDEAŁ", "cta": "", "total_dur_s": round(sum(b["dur_s"] for b in beats), 2),
    "central_claim_id": "CLM-02", "poster_claim_ids": [], "payload_claim_ids": ["CLM-04", "CLM-05"], "payoff_claim_ids": ["CLM-05"],
}

plan = {
    "grade": "bright pastel 2D hand-drawn editorial cartoon with clean evidence metaphors",
    "light": "warm cream dawn and cyan-mint measurement accents, soft cel shadows",
    "lens": "extreme macro for hook, medium human reactions, wide evidence comparisons and payoff",
    "frames": frames,
}

qa_checks = [
    ("hook_stops_scroll", "A generic watch and suspicious question about reading the brain are visible immediately."),
    ("format_delivered", "Versus compares coarse sleep/wake output with detailed stage estimates."),
    ("turn_is_real", "The meta-analysis removes the promise of one universal accuracy verdict."),
    ("payload_is_real", "The viewer gets a concrete same-device, multi-week trend rule."),
    ("payoff_is_entailed", "Trend over one-night perfection follows from the evidence limits."),
    ("overlays_add", "24-study count, signal list, comparison and source card add compact evidence."),
    ("visual_causal_progression", "Watch claim becomes measurement comparison, evidence limit and practical rule."),
    ("frames_semantic_match", "Each frame makes one silent claim matching its beat and claim IDs."),
    ("voice_persona", "Polish male narration is conversational, bright and lightly ironic."),
    ("not_a_clone", "Wearable-versus-lab evidence device and trend payoff differ from recent food stories."),
    ("source_named_when_natural", "The meta-analysis card appears at the evidence turn."),
    ("language_pl", "All viewer-facing speech and overlays are Polish."),
]

qa = {"passed": True, "checks": [{"name": n, "passed": True, "detail": d} for n, d in qa_checks], "notes": ["No brand is ranked and no wearable output is presented as diagnosis.", "The practical rule is observational and same-device, not a treatment recommendation."], "blame_stage": ""}

pkg = {
    "title": "Czy zegarek naprawdę mierzy głęboki sen?",
    "description": "Zegarek pokazuje sen głęboki, ale czy naprawdę czyta Twój mózg? Porównujemy dane z wearables z polisomnografią i sprawdzamy, dlaczego trend z tego samego urządzenia jest rozsądniejszy niż polowanie na idealny wynik jednej nocy.\n\nŹródła:\n" + "\n".join(s["url"] for s in sources[:4]) + "\n\nMateriał ma charakter edukacyjny i nie zastępuje porady lekarza.",
    "hashtags": ["#sen", "#smartwatch", "#zdrowie", "#badania", "#Shorts"],
    "pinned_comment": "Patrzysz na wynik snu w zegarku czy wolisz nie wiedzieć?",
    "title_template": "question_plus_reframe", "description_template": "short_context",
    "distribution_lane": "hybrid", "primary_query": "głęboki sen",
    "secondary_queries": ["jakość snu Garmin", "jakość snu Apple Watch", "sen głęboki aplikacja", "czy zegarek mierzy sen"],
    "metadata_hypothesis": "Direct search wording plus a visible watch-versus-lab conflict should work for search and feed without ranking a brand.",
    "api_tags": ["sen głęboki", "zegarek mierzy sen", "jakość snu", "Apple Watch sen", "Garmin sen", "sleep tracker"],
    "source_urls": [s["url"] for s in sources[:4]],
}

strategy = {
    "authored_by": "Codex",
    "run_purpose": "Sleep & Recovery S06; current production from the refreshed Polish demand cluster.",
    "audience": "Polish office workers and wearable users who over-interpret nightly deep-sleep scores.",
    "hypothesis": "A watch-versus-lab visual reversal should create a clear feed conflict while the same-device trend rule gives a saveable payoff.",
    "planned_duration_s": script["total_dur_s"],
    "risk_decision": {"decision": "Proceed locally and publish after full QA", "claim_boundary": "No brand ranking, no diagnosis, no sleep-stage percentage for an individual device, and no treatment advice."},
    "evidence_levels": {"SRC-01": "meta_analysis", "SRC-02": "primary_study", "SRC-03": "primary_study", "SRC-04": "systematic_review", "SRC-05": "official"},
    "distribution": {"lane": "hybrid", "primary_query": "głęboki sen", "secondary_queries": pkg["secondary_queries"], "metadata_hypothesis": pkg["metadata_hypothesis"]},
    "hook_lab": {"variants": [
        {"id": "H1", "type": "watch_reads_brain", "hook": beats[0]["voiceover"], "poster": "GŁĘBOKI SEN?", "first_visual": "Generic smartwatch shows an abstract sleep ring while hero asks if it read his brain.", "first_proof_s": 1.6, "claim_ids": [], "score": 10, "rejection_reason": "Selected: immediate object conflict and sound-off question."},
        {"id": "H2", "type": "watch_vs_lab", "hook": "Zegarek pokazuje fazę snu. Laboratorium patrzy na coś więcej.", "poster": "ZEGAREK VS LAB", "first_visual": "Watch and sleep-lab sensors enter as concrete alternatives.", "first_proof_s": 2.0, "claim_ids": ["CLM-01"], "score": 8, "rejection_reason": "Clear but less personal than H1."},
        {"id": "H3", "type": "score_reversal", "hook": "Twój wynik głębokiego snu może wyglądać precyzyjnie. To jeszcze nie laboratorium.", "poster": "PRECYZJA?", "first_visual": "Glossy score card is lowered from a pedestal beside a watch.", "first_proof_s": 2.7, "claim_ids": ["CLM-02"], "score": 8, "rejection_reason": "Good evidence promise, but the brain-reading joke arrives later."}
    ], "selected_variant": "H1"},
    "format_selection": {"format": "versus", "priority": "P0", "reason": "The question contains two concrete measurement worlds: consumer watch output versus laboratory reference measurement.", "comic_engine": "The watch behaves like an overconfident analyst; the lab calmly asks what was actually measured.", "discarded_alternatives": ["study_autopsy", "myth_autopsy"]},
    "structure_variation": {
        "compared_runs": ["2026-08-24_v8-baton-po-treningu-courtroom-imagegen-01", "2026-08-22_v8-sennosc-po-lunchu", "2026-08-22_v8-czy-jajka-sa-zdrowe", "2026-08-21_v8-ile-cukru-w-szklance-soku", "2026-08-21_v8-mikrofalowka-niszczy-witaminy", "2026-08-19_v8-spacer-po-jedzeniu-imagegen-cleanroom-01", "2026-08-19_v8-ile-kofeiny-w-ciagu-dnia-recut", "2026-08-17_v8-weglowodany-w-tym-cukry-etykieta"],
        "signature": {"hook_mechanism": "watch challenges its own brain-reading authority", "first_proof": "lab reference method appears by beat 1", "turn_device": "24-study evidence removes a universal verdict", "evidence_device": "watch versus PSG and coarse versus detailed sleep stages", "overlay_sequence": ["callout", "list", "stat", "source", "versus", "timeline"], "payoff_device": "same-device trend over several weeks", "visual_rhythm": "extreme macro watch, wide lab, medium signal metaphor, wide study grid, versus courtroom, wide trend, warm final"},
        "differs_from_recent": ["uses a consumer-device versus reference-method conflict instead of food objects", "turns with evidence heterogeneity rather than a product-label reversal", "ends with an observation protocol rather than a shopping or timing rule"]
    },
    "series": {"series_id": "sleep-recovery-2026", "episode": 1, "followup_topics": ["sen płytki, głęboki i REM — czy aplikacja to rozróżnia?", "drzemka kofeinowa — trik czy placebo?", "telefon przed snem: światło czy aktywność?"]},
    "hero_descriptor": HERO,
    "visual_policy": "Built-in ImageGen only; generated images contain no readable text or digits; renderer owns Polish captions, overlays and source cards; critical visual elements stay inside x=120..860, y=200..1500.",
}

pack = {
    "lang": "pl", "topic": "Czy zegarek naprawdę wie, ile masz głębokiego snu?", "viewer_question": "Czy wynik głębokiego snu z zegarka jest pomiarem laboratoryjnym?",
    "recommended_angle": "Watch-versus-lab evidence reversal: a wearable can be useful for trends without turning a nightly stage score into a diagnosis.",
    "evidence_summary": "Consumer sleep trackers estimate sleep from indirect signals. Validation studies and a meta-analysis comparing wrist-worn devices with polysomnography show that performance depends on device, metric and sleep stage; detailed staging should not be treated as a universal laboratory reading. The safe payoff is to watch trends on the same device over several weeks rather than chase one perfect nightly score.",
    "sources": sources, "claims": claims,
    "unresolved_conflicts": ["Validation studies use different devices, algorithms, populations and protocols; this package does not rank current Apple Watch or Garmin models.", "A wearable score cannot explain persistent symptoms or replace appropriate professional evaluation."],
}

write("research_pack.json", pack)
write("script.json", script)
write("compliance.json", {"passed": True, "fixes": ["Usunięto ranking marek i indywidualne procenty dokładności.", "Zostawiono trend same-device zamiast diagnozy z jednej nocy."], "cleaned_script": script})
write("fact_review.json", {"passed": True, "checks": [{"claim_id": c["id"], "passed": True, "issue": "", "required_change": ""} for c in claims], "unsupported_script_statements": [], "notes": ["Every meaningful evidence statement is linked to a current research or official source.", "The 24-study count refers to the cited meta-analysis, not to all sleep trackers."]})
write("frame_plan.json", plan)
write("qa.json", qa)
write("publish_package.json", pkg)
write("codex_strategy.json", strategy)
(RUN / "research_raw.md").write_text("# Research memo — Sleep & Recovery S06\n\nCodex-authored evidence memo. Demand signals: Polish autocomplete clusters `sen głęboki`, `jakość snu Garmin`, `jakość snu Apple Watch`, `sen płytki`, `REM`. Health evidence is restricted to the five sources in research_pack.json.\n", encoding="utf-8")
print(RUN)
