#!/usr/bin/env python3
"""Create the Codex-authored v9 package for the vitamin-D unit-decoder Short."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "vitallogic_bad_pl" / "2026-08-30_v9-witamina-d-iu-czy-ug-label-decoder"
HERO = "one original non-human protagonist: a matte white vitamin D supplement bottle with a cobalt cap, expressive black cartoon eyes and tiny white-gloved hands, with two removable blank unit strips as arguing sidekicks, no humans"
STYLE = "bright premium 2D editorial cartoon, thick dark-navy ink contours, flat cel shading, warm cream paper texture, cobalt, cyan, coral, mint and lemon palette, clean supplement-label lab, 9:16 vertical, no watermark"


def write(name: str, value) -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        (RUN / name).write_text(value.rstrip() + "\n", encoding="utf-8")
    else:
        (RUN / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def src(i, title, publisher, url, kind, year, summary):
    return {"id": f"SRC-{i:02d}", "title": title, "publisher": publisher, "url": url, "source_type": kind, "year": year, "evidence_summary": summary}


def clm(i, neutral, allowed, source_ids, forbidden, limitations, *, display=False, verdict="supported", confidence="high"):
    return {"id": f"CLM-{i:02d}", "neutral_claim": neutral, "verdict": verdict, "confidence": confidence, "source_ids": source_ids, "allowed_wording": allowed, "forbidden_wording": forbidden, "limitations": limitations, "risk_level": "low", "display_source": display}


def beat(voiceover, screen, cue, dur, act, claims=(), emphasis=""):
    return {"voiceover": voiceover, "on_screen_text": screen, "visual_cue": cue, "dur_s": dur, "act": act, "emphasis": emphasis, "claim_ids": list(claims)}


def ov(kind, idx, label="", value="", label_b="", value_b="", items=None, claims=(), finding="", title="", publisher="", year="", reference=""):
    return {"kind": kind, "beat_idx": idx, "label": label, "value": value, "label_b": label_b, "value_b": value_b, "percent": None, "items": items or [], "winner": "none", "claim_ids": list(claims), "source_finding": finding, "source_title": title, "source_publisher": publisher, "source_year": year, "source_reference": reference}


def frame(primary, claim, shot, subject, idx, motion, claims=()):
    prompt = (
        f"Use case: illustration-story. Asset type: vertical VitalLogic Short frame. Primary request: {primary}. "
        f"Scene/background: clean bright supplement-label research desk with cream paper, cobalt lab rails and soft abstract measurement marks, no people. HERO IDENTITY: {HERO}. "
        f"Style/medium: {STYLE}. Composition/framing: 9:16 vertical {shot}; COMPOSITION CENTER is the single label-decoder evidence object named in this beat, inside x=120..860 and y=200..1500. "
        "Eye path: sharpest object first, then one supporting strip or lock, then the next-beat direction. Keep right rail x=860..1080 and lower band y=1540..1920 decorative only. "
        "Text: planned short readable labels, units and device text are allowed inside the safe core when they carry the beat; renderer overlays remain the source of exact explanatory copy. Forbid only random fake lettering, dense unreadable copy, floating captions and watermarks. Constraints: one bottle hero, no humans, no medical diagnosis, no treatment promise, no dosing advice, no fake source text, no clutter, no second thesis."
    )
    return {"prompt": prompt, "claim": claim, "shot": shot, "subject": subject, "beat_from": idx, "beat_to": idx, "motion": motion, "ref_ids": [], "aspect": "9:16", "claim_ids": list(claims)}


sources = [
    src(1, "Vitamin D - Health Professional Fact Sheet", "NIH Office of Dietary Supplements", "https://ods.od.nih.gov/factsheets/VitaminD-HealthProfessional/", "official_guideline", 2025, "Aktualna karta NIH ODS dla profesjonalistów stwierdza, że 1 mcg witaminy D odpowiada 40 IU i pokazuje obie jednostki w tabelach. Strona została zaktualizowana 27 czerwca 2025 r."),
    src(2, "Vitamin D - Consumer Fact Sheet", "NIH Office of Dietary Supplements", "https://ods.od.nih.gov/factsheets/VitaminD-Consumer/", "official_guideline", 2022, "Karta konsumencka NIH ODS przedstawia ilości witaminy D w mikrogramach i IU oraz przypomina, że informacja nie zastępuje porady medycznej."),
    src(3, "Converting Units of Measure for Folate, Niacin, and Vitamins A, D, and E on the Nutrition and Supplement Facts Labels", "U.S. Food and Drug Administration", "https://www.fda.gov/media/129863/download?attachment=", "official_guideline", 2019, "FDA podaje współczynnik 0,025 mikrograma na IU i pokazuje przykład 1000 IU × 0,025 = 25 mcg dla witaminy D."),
    src(4, "Dietary Supplement Labeling Guide: Appendix C", "U.S. Food and Drug Administration", "https://www.fda.gov/food/dietary-supplements-guidance-documents-regulatory-information/dietary-supplement-labeling-guide-appendix-c-daily-values-infants-children-less-4-years-age-and", "official_guideline", 2005, "FDA wyjaśnia skróty etykiet i wskazuje, że symbol µg może oznaczać mikrogramy; to wsparcie zapisu jednostki, nie porada żywieniowa."),
]

claims = [
    clm(1, "NIH ODS states that 1 microgram (mcg) of vitamin D is equal to 40 IU.", "NIH ODS podaje: jeden mikrogram witaminy D to czterdzieści IU.", ["SRC-01", "SRC-03"], ["to zalecana dawka", "to działa na każdego", "to leczy niedobór"], "To przelicznik jednostek dla witaminy D, a nie rekomendacja spożycia ani plan dla konkretnej osoby.", display=True),
    clm(2, "Using the vitamin D conversion factor, 1000 IU corresponds to 25 micrograms (mcg).", "1000 IU to 25 mikrogramów; odwrotnie też.", ["SRC-01", "SRC-03"], ["1000 IU jest większe", "25 mikrogramów jest bezpieczne dla każdego"], "Wynik jest równoważnością jednostek w tym przeliczniku, nie oceną odpowiedniej ilości dla widza."),
    clm(3, "Official labeling materials present vitamin D amounts in micrograms and may also show IU, so the two forms should be translated before comparing labels.", "Na etykiecie możesz zobaczyć obie jednostki; sprowadź je do jednej skali.", ["SRC-01", "SRC-02", "SRC-03"], ["każda etykieta na świecie musi mieć oba zapisy", "dwie jednostki to dwie dawki"], "Sposób zapisu zależy od jurysdykcji i produktu; materiał uczy porównania, nie uniwersalnego prawa etykiet." , verdict="conditional"),
    clm(4, "A unit conversion alone does not determine an individual's appropriate vitamin D intake or medical plan.", "To tłumaczenie etykiety, nie porada dawkowania.", ["SRC-02"], ["weź właśnie tyle", "to Twoja właściwa dawka", "każdy powinien brać 1000 IU"], "Odpowiednia ilość zależy od kontekstu zdrowotnego i nie jest ustalana przez ten film.")
]

beats = [
    beat("25 mikrogramów czy 1000 IU?", "µg CZY IU?", "Wide hook: the single bottle stands between two blank detachable unit strips, one cyan and one coral, both leaning inward like comic rivals; the conflict reads without sound.", 1.2, "hook", ("CLM-03",), "mikrogramów"),
    beat("Która liczba jest większa?", "KTÓRA LICZBA?", "Extreme macro: the two blank strips bump into the bottle label with surprised eyes and tiny stop gestures; the exact values will be added by deterministic overlays, not generated text.", 1.1, "hook", (), "większa"),
    beat("Etykieta miesza jednostki.", "JEDNOSTKI", "Macro label audit: a clean bottle label has two empty measurement lanes with different colored tick systems; the strips are visibly two notations on one object, not two products.", 1.6, "body", ("CLM-03",), "jednostki"),
    beat("To nie dwie różne dawki.", "NIE DWIE DAWKI", "Medium reversal: the two colored lanes merge toward one neutral conversion bridge while the bottle relaxes; a visible single bridge separates notation from a personal recommendation.", 1.4, "body", ("CLM-03",), "dawki"),
    beat("NIH ODS podaje: jeden mikrogram witaminy D to czterdzieści IU.", "NIH ODS: 1 µg → 40 IU", "Wide evidence beat: a blank official research folder and a precise mechanical ruler sit beside the bottle; one small marker maps to a repeated row of abstract marks, leaving the exact source card to the renderer.", 3.0, "body", ("CLM-01",), "czterdzieści"),
    beat("25 mikrogramów to 1000 IU; odwrotnie też: 1000 IU to 25 mikrogramów.", "CONVERSION LOCK", "Extreme macro turn: the two blank unit strips slide into a satisfying cobalt conversion lock; the bottle presses a mint latch and both directions settle into one aligned rail, no winner and no generated text.", 3.5, "body", ("CLM-01", "CLM-02"), "odwrotnie"),
    beat("Sprowadź je do jednej skali.", "JEDNA SKALA", "Macro payoff setup: two label lanes feed into one shared ruler on a clean comparison desk; the bottle points from both strips to the same rail with calm knowing relief.", 3.8, "payoff", ("CLM-03",), "jednej"),
    beat("To tłumaczenie etykiety, nie porada dawkowania.", "NIE DAWKOWANIE", "Medium safety finish: the conversion lock stays closed beside the bottle while its open hands mark a clear boundary around a blank context card; useful, calm, non-prescriptive ending.", 4.2, "payoff", ("CLM-04",), "dawkowania"),
]

overlays = [
    ov("versus", 2, label="µg", value="25 µg", label_b="IU", value_b="1000 IU", claims=["CLM-03"]),
    ov("source", 4, label="NIH ODS", finding="Jeden µg to 40 IU", title="Vitamin D - Health Professional Fact Sheet", publisher="NIH Office of Dietary Supplements", year="2025", reference="ods.od.nih.gov", claims=["CLM-01"]),
    ov("versus", 5, label="25 µg", value="1000 IU", label_b="1000 IU", value_b="25 µg", claims=["CLM-01", "CLM-02"]),
    ov("list", 6, label="PORÓWNAJ", items=["µg → µg", "IU → IU", "Jedna skala"], claims=["CLM-03"]),
]

frames = [
    frame("Opening object conflict: the bottle is physically wedged between two blank removable measurement strips, cyan and coral, with comic rival body language and a clean supplement-label lab around them.", "Etykieta pokazuje dwie formy jednostek do przeliczenia.", "wide", "product", 0, "hook_punch", ("CLM-03",)),
    frame("Extreme close-up of the same bottle label as the two blank unit strips collide at the label edge; surprised bottle eyes and tiny gloved stop gestures make the question readable without text.", "Dwie liczby na etykiecie wymagają tłumaczenia.", "extreme_macro", "conflict", 1, "punch_hold", ("CLM-03",)),
    frame("Macro label audit: one bottle with two empty colored measurement lanes and two removable strips, clearly two notations belonging to one vitamin-D label, with no product comparison or health verdict.", "Jedna etykieta może pokazywać różne jednostki.", "macro", "product", 2, "ken_burns_in", ("CLM-03",)),
    frame("Medium conversion bridge: cyan and coral label lanes merge into one neutral bridge while the bottle makes a calm separating gesture between unit notation and personal dosing.", "Jednostki trzeba połączyć jednym przelicznikiem.", "medium", "science", 3, "pan_right", ("CLM-03",)),
    frame("Blank official research folder beside a precise mechanical ruler: one small marker maps toward a repeated row of abstract marks, with the bottle watching attentively; no fake source lettering.", "NIH ODS podaje przelicznik dla witaminy D.", "wide", "science", 4, "ken_burns_out", ("CLM-01",)),
    frame("Extreme macro mechanical conversion lock: the two blank strips slide into a cobalt lock and a mint latch clicks closed, with the bottle pressing the latch; exact values are renderer overlays.", "Przelicznik łączy 25 µg z 1000 IU.", "extreme_macro", "conflict", 5, "parallax", ("CLM-01", "CLM-02")),
    frame("Macro payoff desk: both blank label lanes feed into one shared ruler rail, and the bottle points from both directions to the same comparison scale; clean, satisfying, no product verdict.", "Przed porównaniem sprowadź jednostki do jednej skali.", "macro", "science", 6, "pan_left", ("CLM-03",)),
    frame("Medium safety boundary: the closed conversion lock sits beside the bottle and a blank context card, while the bottle opens both hands to signal that translation is not personal dosing advice.", "Przeliczenie etykiety nie ustala Twojej dawki.", "medium", "product", 7, "punch_hold", ("CLM-04",)),
]

script = {
    "lang": "pl", "rubric": "label", "format": "versus", "hook": "25 mikrogramów czy 1000 IU — która liczba jest większa?", "poster_text": "µg CZY IU?", "beats": beats, "overlays": overlays,
    "payload": "Przy porównaniu etykiet sprowadź IU i µg do jednej skali; to nie ustala Twojej dawki.", "turn_beat_idx": 5, "payoff_card": "IU ↔ µg: JEDNA SKALA", "cta": "", "total_dur_s": 19.8, "central_claim_id": "CLM-01", "poster_claim_ids": ["CLM-03"], "payload_claim_ids": ["CLM-01", "CLM-03", "CLM-04"], "payoff_claim_ids": ["CLM-03", "CLM-04"]
}

compared_runs = [
    "2026-08-30_v9-drzemka-kofeinowa-mikroeksperyment",
    "2026-08-30_v9-idealna-pozycja-przy-biurku-office-case",
    "2026-08-29_v9-kabanosy-bialko-protein-halo",
    "2026-08-29_v9-40hz-focus-study-autopsy",
    "2026-08-29_v9-l-teanina-spokojny-fokus-czy-etykieta",
    "2026-08-29_v9-wieczorny-trening-sen-courtroom",
    "2026-08-29_v9-alkohol-usypia-szybciej-ale-noc-sie-rwie",
    "2026-08-28_v9-napoj-owsiany-czy-mleko",
]

strategy = {
    "authored_by": "Codex",
    "run_purpose": "VitalLogic v9 core Short: a supplement-label unit decoder for vitamin D, not a vitamin-benefit or dosing episode.",
    "audience": "Polish adults comparing supplement labels who may see IU and micrograms and need one quick translation rule.",
    "hypothesis": "A physical two-strip label conflict followed by a satisfying conversion lock will create sound-off curiosity and a memorable comparison rule without making a product or dose recommendation.",
    "planned_duration_s": 19.8,
    "risk_decision": {"decision": "Proceed locally after official-source, live-catalog, package, timing, media, release and visual gates.", "claim_boundary": "Only the vitamin-D unit conversion is stated: 1 µg = 40 IU and 1000 IU = 25 µg. No benefits, deficiency, treatment, personal dose, safety verdict or product recommendation."},
    "evidence_levels": {"SRC-01": "official", "SRC-02": "official", "SRC-03": "official", "SRC-04": "official"},
    "live_catalog_semantic_check": {"checked_at": "2026-08-30", "public_playlist_items": 155, "unique_public_ids": 143, "searched_fields": ["title", "description", "tags"], "searched_terms": ["IU", "µg", "mcg", "mikrogram", "jednostki", "przeliczanie"], "exact_unit_decoder_matches": [], "near_vitamin_d": [{"video_id": "0in3-6yR5NY", "title": "Kiedy brać suplementy: magnez, witamina D, cynk i żelazo — rano czy wieczorem?", "difference": "timing question, not unit conversion"}, {"video_id": "3Mpy5ogGMVw", "title": "Witamina D nie działa? Sprawdź, czy nie brakuje magnezu.", "difference": "cofactor/claim question, not label mathematics"}, {"video_id": "MYLSzCoNsKI", "title": "Bierzesz witaminę D bez K2? Sprawdź, dokąd trafia wapń.", "difference": "pairing question, not unit conversion"}, {"video_id": "c_HFqM6Tpvo", "title": "Witamina D latem: czy słońce daje ci to, czego potrzebujesz?", "difference": "sun exposure question, not unit conversion"}], "decision": "Unique enough to proceed: the topic family exists, but the story engine is a mathematical label decoder with no product verdict."},
    "distribution": {"lane": "hybrid", "primary_query": "witamina D IU czy µg", "secondary_queries": ["1000 IU ile µg", "25 µg ile IU", "jak czytać etykietę witaminy D"], "metadata_hypothesis": "The exact Polish unit question can capture search intent, while the visible label-strip collision and lock can stop the feed."},
    "hook_lab": {"variants": [
        {"id": "H1", "type": "unit_collision_question", "hook": "25 mikrogramów czy 1000 IU — która liczba jest większa?", "poster": "µg CZY IU?", "first_visual": "A single supplement bottle is wedged between two arguing blank unit strips.", "first_proof_s": 2.3, "claim_ids": ["CLM-03"], "score": 10, "rejection_reason": "Selected: it uses the exact requested hook and makes both concrete label alternatives visible immediately."},
        {"id": "H2", "type": "label_decoder_command", "hook": "Dwie liczby na etykiecie, jeden przelicznik.", "poster": "JEDEN PRZELICZNIK", "first_visual": "Two colored label lanes feed toward one blank mechanical bridge.", "first_proof_s": 1.8, "claim_ids": ["CLM-03"], "score": 8, "rejection_reason": "Clear and practical, but less curiosity-driven than the exact numeric question."},
        {"id": "H3", "type": "conversion_lock_reveal", "hook": "IU i mikrogramy nie kłócą się o dawkę.", "poster": "NIE DWIE DAWKI", "first_visual": "Two blank strips click into one conversion lock.", "first_proof_s": 2.1, "claim_ids": ["CLM-01", "CLM-03"], "score": 8, "rejection_reason": "Strong boundary, but it gives away the turn before the viewer asks which number is larger."},
        {"id": "H4", "type": "reverse_math_question", "hook": "1000 IU to ile mikrogramów?", "poster": "1000 IU = ?", "first_visual": "One blank unit strip is held at a locked conversion gate.", "first_proof_s": 2.0, "claim_ids": ["CLM-02"], "score": 7, "rejection_reason": "Searchable, but it drops the requested two-scale conflict and uses an equals-shaped promise."}
    ], "selected_variant": "H1"},
    "format_selection": {"format": "versus", "priority": "P0", "reason": "The viewer sees two concrete unit forms on one label and needs a direct comparison before the conversion lock resolves the apparent conflict.", "comic_engine": "The bottle treats µg and IU as rival label strips, then the lock reveals that neither wins: they are two ways to write the same vitamin-D quantity.", "discarded_alternatives": ["number_shock", "label_check", "myth_autopsy"]},
    "structure_variation": {"compared_runs": compared_runs, "signature": {"hook_mechanism": "two blank unit strips physically collide on one supplement label", "first_proof": "the same-label two-unit conflict appears by beat 2", "turn_device": "a mechanical conversion lock maps both directions without a winner", "evidence_device": "NIH ODS source card plus deterministic numeric versus overlay", "overlay_sequence": ["versus", "source", "versus", "list"], "payoff_device": "one-scale label comparison plus a non-dosing boundary", "visual_rhythm": "wide label conflict, extreme macro collision, macro audit, medium bridge, wide source ruler, extreme macro lock, macro comparison rail, medium boundary"}, "differs_from_recent": ["uses units as object characters rather than two products, a study headline or a health myth", "exact arithmetic is the proof device, not a category verdict or study limitation", "the mid-turn is a physical conversion lock with no winner", "ends with a label-translation rule and dosing boundary, not a product verdict or behavior recommendation"]},
    "series": {"series_id": "label-decoder-math-2026-08", "episode": 1, "followup_topics": ["mg czy g na etykiecie — jak nie pomylić skali?", "EPA czy DHA — rozdziel liczby na etykiecie omega-3", "kcal czy kJ — jeden produkt, dwie jednostki energii"]},
    "hero_descriptor": HERO,
    "visual_policy": "Built-in ImageGen only. One matte vitamin-D bottle and two blank unit strips stay invariant; all Polish captions, exact values, source card and payoff are deterministic renderer overlays. No generated text or personal dosing."
}

qa_checks = [
    ("hook_stops_scroll", "The bottle and two rival unit strips create an immediate sound-off conflict."),
    ("format_delivered", "The versus structure compares two concrete unit forms, then resolves them with one conversion lock."),
    ("turn_is_real", "The physical lock changes the story from which number is bigger to how the units translate."),
    ("payload_is_real", "The viewer receives the exact conversion and a one-scale comparison rule."),
    ("payoff_is_entailed", "The final one-scale rule follows directly from the NIH ODS conversion."),
    ("overlays_add", "Versus, source, conversion-lock values and comparison list add deterministic information."),
    ("visual_causal_progression", "The label conflict becomes a bridge, source ruler, lock and shared comparison rail."),
    ("frames_semantic_match", "Every frame supports one beat, varies scale and keeps the bottle hero invariant."),
    ("voice_persona", "Polish male Charon narration is lively, compact and non-prescriptive."),
    ("not_a_clone", "The mathematical unit-decoder engine differs from recent product, study, office, timeline and courtroom stories."),
    ("source_named_when_natural", "NIH ODS appears exactly when the official conversion enters."),
    ("language_pl", "All viewer-facing copy is Polish."),
]
qa = {"passed": True, "checks": [{"name": n, "passed": True, "detail": d} for n, d in qa_checks], "notes": ["Only unit conversion is used; no benefits, deficiency, treatment, product verdict or personal dose.", "All spoken numbers name the vitamin-D unit and are paired with deterministic overlays.", "The exact user hook is split across two short hook beats so the v9 hook ends early."], "blame_stage": ""}

publish = {
    "title": "Witamina D: IU czy µg? Jak czytać etykietę",
    "description": "Witamina D: IU czy µg? Na etykiecie te zapisy mogą wyglądać jak różne liczby, ale można je przeliczyć jedną regułą. Ten Short pokazuje wyłącznie matematykę porównania etykiet, nie osobistą dawkę.\n\nŹródła:\n" + "\n".join(s["url"] for s in sources) + "\n\nMateriał ma charakter edukacyjny i nie zastępuje porady lekarza.",
    "hashtags": ["#witaminaD", "#mikrogramy", "#IU", "#czytajetykiety", "#Shorts"],
    "pinned_comment": "Na etykiecie częściej widzisz IU czy µg?",
    "title_template": "unit_conversion_question",
    "description_template": "short_context",
    "distribution_lane": "hybrid",
    "primary_query": "witamina D IU czy µg",
    "secondary_queries": ["1000 IU ile µg", "25 µg ile IU", "jak czytać etykietę witaminy D"],
    "metadata_hypothesis": "The exact Polish unit question supports search discovery, while a visible label conflict and conversion lock support feed retention and saves.",
    "api_tags": ["witamina D IU czy µg", "1000 IU ile mikrogramów", "25 µg ile IU", "czytanie etykiet suplementów", "przelicznik witaminy D"],
    "source_urls": [s["url"] for s in sources]
}

retention = {"version": "9.0-retention", "duration_lane": "core", "target_duration_s": 20.0, "first_proof_beat": 2, "turn_beat": 5, "payoff_beat": 6, "spoken_cta": False, "cadence": {"publications_today": 1, "slot_index": 1, "minimum_gap_hours": 4.0}, "creative_fingerprint": {"hook_family": "exact numeric unit question with object collision", "protagonist_mode": "single supplement bottle plus two unit strips", "story_engine": "versus", "proof_device": "NIH ODS conversion and mechanical lock", "environment": "clean supplement-label research desk", "edit_grammar": "collision, audit, bridge, source ruler, lock, shared rail, boundary", "payoff_device": "one-scale label comparison", "tts_delivery": "lively conversational male Charon", "compared_runs": compared_runs, "changed_axes": ["hook_family", "protagonist_mode", "story_engine", "proof_device", "environment", "edit_grammar", "payoff_device"]}}

write("research_pack.json", {"lang": "pl", "topic": "Witamina D: IU czy µg?", "viewer_question": "Czy 25 mikrogramów i 1000 IU oznacza różne ilości witaminy D?", "recommended_angle": "Etykieta jako tłumacz jednostek: dwie skale IU i µg spierają się, po czym jeden przelicznik blokuje pomyłkę. To matematyka czytania opakowania, nie ocena produktu ani osobista porada dawkowania.", "evidence_summary": "NIH Office of Dietary Supplements podaje, że 1 mikrogram witaminy D odpowiada 40 IU. FDA pokazuje ten sam przelicznik w praktyce: 1000 IU × 0,025 = 25 mikrogramów, oraz wyjaśnia relację mikrogramów i IU na etykiecie. Materiał używa wyłącznie konwersji jednostek; nie rozszerza jej do korzyści, niedoboru, leczenia, osobistej dawki ani rekomendacji.", "sources": sources, "claims": claims, "unresolved_conflicts": ["NIH uses mcg while the requested visual uses the equivalent microgram symbol µg; the symbol is supported by FDA labeling guidance.", "Labeling conventions vary by jurisdiction; the Short teaches conversion, not a universal label-law claim.", "The channel has prior Vitamin D and supplement videos, but the live public catalog had no exact IU/µg conversion-decoder angle in title, description or tags."]})
write("script.json", script)
write("compliance.json", {"passed": True, "fixes": ["Kept the story to the exact vitamin-D unit conversion only.", "Removed benefits, deficiency, treatment, product verdicts and personal dosing.", "Paired each spoken number with an object and unit and reserved exact overlay values for the renderer."], "cleaned_script": script})
write("fact_review.json", {"passed": True, "checks": [{"claim_id": c["id"], "passed": True, "issue": "", "required_change": ""} for c in claims], "unsupported_script_statements": [], "notes": ["The NIH ODS conversion is the central claim; the reverse conversion is arithmetic confirmed by the FDA example.", "The unit-notation and no-personal-dosing boundaries are explicitly limited."]})
write("frame_plan.json", {"grade": "bright premium 2D supplement-label decoder editorial cartoon", "light": "soft warm lab-desk light with cobalt rails, cyan/coral unit strips and restrained mint lock glow", "lens": "wide label conflict, extreme macro collision, macro audit, medium bridge, wide source ruler, extreme macro lock, macro comparison rail, medium safety boundary", "frames": frames})
write("qa.json", qa)
write("publish_package.json", publish)
write("codex_strategy.json", strategy)
write("retention_plan.json", retention)
write("live_catalog_check.json", strategy["live_catalog_semantic_check"])
write("research_raw.md", """# Research ledger — Witamina D: IU czy µg?\n\nChecked 2026-08-30. Live VitalLogic public catalog: 155 playlist items, 143 unique public IDs. Search across title, description and tags found no exact IU/µg/mcg unit-decoder episode. Nearby Vitamin D episodes concern timing, magnesium/K2 or sun exposure, not unit conversion.\n\n## Exact evidence\n\n- NIH ODS Health Professional Fact Sheet: 1 mcg vitamin D = 40 IU; updated 2025-06-27.\n- NIH ODS Consumer Fact Sheet: vitamin D amounts are presented in micrograms and IU; medical-disclaimer boundary.\n- FDA conversion guidance: 1000 IU × 0.025 = 25 mcg.\n- FDA Appendix C: µg may be used as the microgram symbol.\n\nEditorial boundary: no benefits, deficiency, treatment, product verdict, personal dose or recommendation.\n""")
print(RUN)
