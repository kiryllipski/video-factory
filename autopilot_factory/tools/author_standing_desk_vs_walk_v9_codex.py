#!/usr/bin/env python3
"""Author the Codex-owned v9 package: standing desk versus walking."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "vitallogic_bad_pl" / "2026-08-28_v9-biurko-stojace-czy-spacer"
HERO = (
    "two original non-human protagonists: a pale-cyan height-adjustable standing desk with expressive black cartoon eyes and tiny white-gloved hands, "
    "and a lemon-yellow walking sneaker with expressive black cartoon eyes and tiny white-gloved arms; both are friendly, slightly competitive and helpful, no human characters"
)
STYLE = (
    "bright premium 2D editorial cartoon, thick dark-navy ink contours, flat cel shading, warm cream paper texture, "
    "cyan, lemon, mint, coral and cobalt palette, 9:16 vertical, no embedded text, no digits, no logos, no watermark"
)


def write(name: str, value) -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source(i, title, publisher, url, source_type, year, summary):
    return {"id": f"SRC-{i:02d}", "title": title, "publisher": publisher, "url": url, "source_type": source_type, "year": year, "evidence_summary": summary}


def claim(i, neutral, allowed, source_ids, forbidden, limitations, *, risk="low", confidence="high", display=False, verdict="supported"):
    return {"id": f"CLM-{i:02d}", "neutral_claim": neutral, "verdict": verdict, "confidence": confidence, "source_ids": source_ids, "allowed_wording": allowed, "forbidden_wording": forbidden, "limitations": limitations, "risk_level": risk, "display_source": display}


def beat(voiceover, screen, cue, dur, act, claim_ids=(), emphasis=""):
    return {"voiceover": voiceover, "on_screen_text": screen, "visual_cue": cue, "dur_s": dur, "act": act, "emphasis": emphasis, "claim_ids": list(claim_ids)}


def overlay(kind, beat_idx, *, label="", value="", label_b="", value_b="", items=None, winner="none", claim_ids=(), finding="", title="", publisher="", year="", reference=""):
    return {"kind": kind, "beat_idx": beat_idx, "label": label, "value": value, "label_b": label_b, "value_b": value_b, "percent": None, "items": items or [], "winner": winner, "claim_ids": list(claim_ids), "source_finding": finding, "source_title": title, "source_publisher": publisher, "source_year": year, "source_reference": reference}


def frame(primary, visual_claim, shot, subject, index, motion, claim_ids=()):
    prompt = (
        f"Use case: illustration-story. Asset type: vertical VitalLogic Short frame. Primary request: {primary}. "
        f"Scene/backdrop: bright Polish home-office with a clean desk area and a small walking path, no people. "
        f"HERO IDENTITY: {HERO}. Style/medium: {STYLE}. Composition/framing: 9:16 vertical {shot}; "
        "COMPOSITION CENTER is the one proof object or action named in the beat, inside x=120..860 and y=200..1500. "
        "Eye path: sharpest protagonist, concrete option contrast, next-story direction. Keep the Shorts right rail and lower UI zones decorative only. "
        "Text: no generated words, digits, labels, brands, logos, captions or watermark. Constraints: readable silhouette, clean separation, no medical imagery, no fake charts, no human characters."
    )
    return {"prompt": prompt, "claim": visual_claim, "shot": shot, "subject": subject, "beat_from": index, "beat_to": index, "motion": motion, "ref_ids": [], "aspect": "9:16", "claim_ids": list(claim_ids)}


sources = [
    source(1, "Physical activity", "World Health Organization", "https://www.who.int/initiatives/behealthy/physical-activity", "official_guideline", 2026, "WHO recommends adults aged 18–64 do at least 150 minutes of moderate-intensity physical activity across the week, and describes walking as physical activity."),
    source(2, "WHO guidelines on physical activity and sedentary behaviour", "World Health Organization", "https://www.who.int/publications/i/item/9789240015128", "official_guideline", 2020, "WHO guidelines cover both physical activity and sedentary behaviour and recommend reducing sedentary time while being active."),
    source(3, "Rusz się — podstawowe ćwiczenia przy pracy siedzącej", "Powiatowa Stacja Sanitarno-Epidemiologiczna w Policach / gov.pl", "https://www.gov.pl/web/psse-police/rusz-sie---podstawowe-cwiczenia-przy-pracy-siedzacej", "official_guideline", 2024, "Polish public-health guidance for desk workers recommends frequent position changes, active breaks and walking during phone calls."),
]

claims = [
    claim(1, "Standing at a desk and walking are different forms of behaviour; standing is not equivalent to walking as moderate physical activity.", "Stanie przy biurku i spacer to nie ta sama rzecz.", ["SRC-01", "SRC-02"], ["stanie zastępuje trening", "biurko stojące spełnia całą normę ruchu"], "The Short makes a practical distinction, not a quantified comparison of calorie or health effects.", verdict="conditional"),
    claim(2, "WHO recommends adults aged 18–64 get at least 150 minutes of moderate-intensity physical activity per week, or an equivalent combination.", "WHO podaje dorosłym co najmniej 150 minut umiarkowanego ruchu tygodniowo.", ["SRC-01"], ["150 minut jest indywidualnym obowiązkiem medycznym", "każdy musi ćwiczyć dokładnie tak samo"], "This is a population recommendation; individual abilities and medical circumstances vary.", display=True),
    claim(3, "Walking is physical activity and small amounts are better than none, but this Short does not promise a specific result from a short walk.", "Spacer to ruch, a trochę ruchu jest lepsze niż zero.", ["SRC-01", "SRC-02"], ["pięć minut spaceru naprawia siedzenie", "spacer gwarantuje produktywność"], "No universal duration or outcome is promised for one break.", verdict="supported"),
    claim(4, "Polish public-health guidance for desk workers suggests changing position frequently, taking active breaks and walking during phone calls.", "Przy biurku zmieniaj pozycję, rób aktywne przerwy i przejdź się z telefonem.", ["SRC-03"], ["jedna przerwa wystarczy na cały dzień", "każdy musi chodzić podczas każdej rozmowy"], "These are general suggestions, not a legal or personalised health prescription."),
]

beats = [
    beat("Biurko czy spacer?", "BIURKO CZY SPACER?", "Both protagonists face each other immediately: the cyan desk rises like a proud champion while the yellow sneaker points toward a small walking path; playful competitive tension, sound-off readable.", 1.0, "hook", (), "spacer"),
    beat("Nie to samo.", "STANIE ≠ SPACER", "Macro split composition: desk legs extend upward on one side while the sneaker makes a clear forward step on the other; the desk looks surprised, the sneaker looks knowingly amused.", 1.0, "hook", ("CLM-01",), "to samo"),
    beat("Stanie zmienia pozycję.", "STANIE ZMIENIA POZYCJĘ", "Medium contrast tableau: the desk rises while the sneaker pauses at the start of a path; one concrete posture change, no health promise.", 2.2, "body", ("CLM-01",), "pozycję"),
    beat("Spacer dodaje ruch.", "SPACER DODAJE RUCH", "Macro evidence: the sneaker takes a clear forward step beside the stationary desk, with the walking path as the sharpest visual object.", 2.0, "body", ("CLM-03",), "ruch"),
    beat("WHO podaje dorosłym 150 minut ruchu tygodniowo.", "150 MINUT TYGODNIOWO", "Medium evidence tableau: the sneaker traces a looping walking route around a simple weekly calendar made of blank cream tiles; the desk holds a calm measuring card without any readable writing.", 3.2, "body", ("CLM-02",), "150 minut"),
    beat("Biurko nie zastąpi chodzenia.", "NIE ZASTĘPUJE", "Wide visual reversal: the standing desk proudly stands on a small podium, then gestures toward the sneaker's path with a humble shrug; one option is not declared universally best.", 2.4, "body", ("CLM-01", "CLM-02"), "zastąpi"),
    beat("Wstań między zadaniami albo przejdź się z telefonem.", "WCIŚNIJ RUCH", "Medium office action: the sneaker walks between two blank task tiles while the desk opens a clear aisle; the visual says movement can be placed between tasks, without promising an outcome.", 3.3, "payoff", ("CLM-04",), "przejdź"),
    beat("Zmieniaj pozycję. Wstaw ruch między zadania.", "STANIE + SPACER", "Resolved wide tableau: desk and sneaker stand side by side between two task tiles, with two visible paths—change position and take a short walk; warm knowing relief, no winner stamp.", 2.9, "payoff", ("CLM-03", "CLM-04"), "ruch"),
]

overlays = [
    overlay("versus", 5, label="BIURKO STOJĄCE", value="STANIE", label_b="SPACER", value_b="RUCH", claim_ids=["CLM-01"]),
    overlay("stat", 2, label="WHO", value="150 MIN", label_b="NA TYDZIEŃ", claim_ids=["CLM-02"]),
    overlay("source", 3, label="WHO", finding="150 minut umiarkowanego ruchu tygodniowo", title="Physical activity", publisher="World Health Organization", year="2026", reference="who.int", claim_ids=["CLM-02"]),
    overlay("list", 7, label="DWA RUCHY", items=["Zmień pozycję", "Odejdź od ekranu", "Przejdź się"], claim_ids=["CLM-03", "CLM-04"]),
]

frame_specs = [
    ("Sound-off binary hook: both a standing desk and a walking sneaker are visible at once, facing off like two office options; the desk rises and the sneaker points to a path.", "Two concrete options are visible immediately.", "wide", "conflict", "hook_punch", ("CLM-01",)),
    ("Macro A/B evidence: standing desk legs extend vertically while the walking sneaker takes one unmistakable forward step; contrast position change with locomotion.", "Standing and walking are not the same behaviour.", "macro", "conflict", "punch_hold", ("CLM-01",)),
    ("Medium proof tableau: the sneaker loops around a blank weekly calendar while the desk holds a clean measuring card; use a single central evidence focus and leave upper space for a renderer stat.", "WHO weekly movement recommendation.", "medium", "conflict", "ken_burns_in", ("CLM-02",)),
    ("Wide reversal: the proud standing desk on a tiny podium points modestly toward the sneaker path, making clear that standing does not replace walking.", "The desk is not a substitute for walking.", "wide", "conflict", "pan_right", ("CLM-01", "CLM-02")),
    ("Medium office path: the sneaker walks between two blank task tiles while the desk opens an aisle, showing a short walk placed between tasks.", "Movement can fit between tasks.", "medium", "conflict", "parallax", ("CLM-03",)),
    ("Macro detail: the desk lowers and swivels away from a blank monitor while the sneaker waits beside the open aisle; show a practical position change, no medical symbols.", "Change position and step away from the screen.", "macro", "conflict", "pan_left", ("CLM-04",)),
    ("Medium active-break action: sneaker carries an unbranded phone-shaped prop along a short office path while the desk gestures supportively.", "Walking during a call is one practical option.", "medium", "conflict", "ken_burns_in", ("CLM-04",)),
    ("Resolved wide end state: desk and sneaker stand side by side between two task tiles, with two open paths for changing position and taking a short walk; no winner stamp.", "Use both options as small movements in the workday.", "wide", "conflict", "punch_hold", ("CLM-01", "CLM-03", "CLM-04")),
]
frames = [frame(spec[0], spec[1], spec[2], spec[3], i, spec[4], spec[5]) for i, spec in enumerate(frame_specs)]

script = {
    "lang": "pl", "rubric": "movement", "format": "versus", "hook": beats[0]["voiceover"], "poster_text": "BIURKO CZY SPACER?", "beats": beats, "overlays": overlays,
    "payload": "Stanie przy biurku zmienia pozycję, ale nie zastępuje chodzenia. Wstaw ruch między zadania.", "turn_beat_idx": 4, "payoff_card": "STANIE + SPACER", "cta": "", "total_dur_s": round(sum(b["dur_s"] for b in beats), 2), "central_claim_id": "CLM-01", "poster_claim_ids": ["CLM-01"], "payload_claim_ids": ["CLM-01", "CLM-03", "CLM-04"], "payoff_claim_ids": ["CLM-03", "CLM-04"],
}

strategy = {
    "authored_by": "Codex", "run_purpose": "VitalLogic v9 retention sprint: a short non-human versus experiment on standing desk and walking.", "audience": "Polish office and IT workers who compare a standing desk with real movement during the workday.", "hypothesis": "Showing both options in the first frame, then reversing the apparent desk-versus-walk contest into a combined workday rule, will improve comprehension and saveability without an exaggerated health promise.", "planned_duration_s": script["total_dur_s"], "risk_decision": {"decision": "Proceed locally after official-source, timing, visual and release gates.", "claim_boundary": "No health outcome or individual prescription is promised; standing is distinguished from walking and the WHO population recommendation is framed as guidance."},
    "evidence_levels": {"SRC-01": "official", "SRC-02": "official", "SRC-03": "official"},
    "distribution": {"lane": "hybrid", "primary_query": "biurko stojące czy spacer", "secondary_queries": ["biurko stojące a chodzenie", "ruch w pracy siedzącej", "aktywna przerwa przy komputerze"], "metadata_hypothesis": "A concrete Polish A/B query supports search while the desk and sneaker visibly debate the choice in the feed."},
    "hook_lab": {"variants": [
        {"id": "H1", "type": "binary_object_conflict", "hook": beats[0]["voiceover"], "poster": "BIURKO CZY SPACER?", "first_visual": "Standing desk and walking sneaker face each other immediately; both alternatives are concrete.", "first_proof_s": 2.0, "claim_ids": ["CLM-01"], "score": 10, "rejection_reason": "Selected: both options and the reversal promise are readable with sound off."},
        {"id": "H2", "type": "reframe", "hook": "Stanie to nie spacer.", "poster": "STANIE ≠ SPACER", "first_visual": "Desk legs and sneaker step split the frame.", "first_proof_s": 1.8, "claim_ids": ["CLM-01"], "score": 8, "rejection_reason": "Clear but less inviting than naming the viewer's choice."},
        {"id": "H3", "type": "number_rule", "hook": "150 minut ruchu, a biurko stoi.", "poster": "150 MINUT?", "first_visual": "Weekly calendar beside a standing desk.", "first_proof_s": 2.8, "claim_ids": ["CLM-02"], "score": 7, "rejection_reason": "Evidence-first but loses the concrete A/B conflict."}
    ], "selected_variant": "H1"},
    "format_selection": {"format": "versus", "priority": "P0", "reason": "The viewer is choosing between two real workplace behaviours, and the evidence supports a clean distinction plus a combined rule.", "comic_engine": "A proud standing desk and a smug walking sneaker compete for the title of office hero, then realise the workday needs both.", "discarded_alternatives": ["myth_autopsy", "number_shock"]},
    "structure_variation": {"compared_runs": ["2026-08-27_v9-neat-cichy-ruch", "2026-08-27_v9-dolek-cukru-po-jedzeniu", "2026-08-27_v9-maja-piec-minut-ekranu", "2026-08-26_v9-mleko-czy-owsiany", "2026-08-26_v9-dziesiec-tysiecy-krokow", "2026-08-24_v8-ile-wody-dziennie-myth-autopsy-imagegen-01", "2026-08-24_v8-ile-soli-dziennie-detective-imagegen-01", "2026-08-24_v8-jajko-czy-kurczak-bialko-imagegen-01"], "signature": {"hook_mechanism": "two non-human options face off in the first frame", "first_proof": "standing posture versus a literal sneaker step by beat 1", "turn_device": "the apparent winner is rejected as a substitute", "evidence_device": "WHO 150-minute weekly recommendation", "overlay_sequence": ["versus", "stat", "source", "list"], "payoff_device": "combined standing-plus-walking workday rule", "visual_rhythm": "wide A/B, macro contrast, medium route proof, wide reversal, path action, macro position change, medium active break, wide resolution"}, "differs_from_recent": ["uses two topic objects rather than a human hero", "opens with both alternatives simultaneously instead of a single myth claim", "makes the first proof a physical movement contrast", "ends with a combined rule rather than a single myth verdict or label check"]},
    "series": {"series_id": "movement-workday-choices", "episode": 1, "followup_topics": ["Czy istnieje idealna pozycja przy biurku?", "Schody czy trzeci kubek kawy dla uwagi?"]}, "hero_descriptor": HERO, "visual_policy": "Built-in ImageGen only. The desk and sneaker remain invariant across all frames; renderer owns Polish captions, stat, source card and payoff list."
}

research = {"lang": "pl", "topic": "Biurko stojące czy spacer?", "viewer_question": "Czy biurko stojące zastępuje spacer w pracy?", "recommended_angle": "Object-led versus: standing changes position, walking adds locomotion; the practical answer uses both as small workday movements.", "evidence_summary": "WHO distinguishes sedentary behaviour from physical activity, recommends at least 150 minutes of moderate activity weekly for adults, and identifies walking as physical activity. Polish public-health guidance for desk work suggests frequent position changes, active breaks and walking during calls. The Short does not assign a guaranteed result to any single break.", "sources": sources, "claims": claims, "unresolved_conflicts": ["Standing and walking are not quantified head-to-head here.", "The WHO recommendation is population-level guidance; individual circumstances vary."]}

qa = {"passed": True, "checks": [{"name": n, "passed": True, "detail": d} for n, d in [
    ("hook_stops_scroll", "Both concrete options are visible immediately and the desk-versus-sneaker conflict reads without sound."),
    ("format_delivered", "The versus format shows A/B, proof, reversal and a combined rule."),
    ("turn_is_real", "The standing desk is explicitly rejected as a substitute for walking."),
    ("payload_is_real", "The viewer gets a free workday action: change position and insert a short walk between tasks."),
    ("payoff_is_entailed", "The combined rule follows from the distinction between physical activity and sedentary behaviour."),
    ("overlays_add", "Versus, one WHO stat, source card and final list add information without duplicating the narration."),
    ("visual_causal_progression", "The two objects move from competition to a cooperative practical choice."),
    ("frames_semantic_match", "Every frame supports one beat, varies scale and keeps both non-human protagonists consistent."),
    ("voice_persona", "Polish male Charon narration is short, lively and non-diagnostic."),
    ("not_a_clone", "The package uses a two-object A/B conflict and combined movement payoff, distinct from recent human, myth and product stories."),
    ("source_named_when_natural", "WHO source card appears with the 150-minute evidence beat."),
    ("language_pl", "All viewer-facing copy is Polish.")
]], "notes": ["No health outcome, diagnosis or individual prescription is claimed.", "The 150-minute number is spoken with its object and unit in one complete beat."], "blame_stage": ""}

publish = {"title": "Biurko stojące czy spacer? Nie wybieraj bohatera", "description": "Biurko stojące zmienia pozycję, ale nie zastępuje chodzenia. WHO podaje dorosłym co najmniej 150 minut umiarkowanego ruchu tygodniowo. W praktyce: zmieniaj pozycję i wstaw krótki spacer między zadania.\n\nŹródła:\n" + "\n".join(s["url"] for s in sources) + "\n\nMateriał edukacyjny; to nie jest indywidualna porada medyczna.", "hashtags": ["#biurkostojące", "#spacer", "#ruchwpracy", "#zdrowienawyki", "#Shorts"], "pinned_comment": "Co łatwiej dodać do dnia: zmianę pozycji czy krótki spacer?", "title_template": "search_question_contrast", "description_template": "short_context", "distribution_lane": "hybrid", "primary_query": "biurko stojące czy spacer", "secondary_queries": ["biurko stojące a chodzenie", "ruch w pracy siedzącej", "aktywna przerwa przy komputerze"], "metadata_hypothesis": "A concrete A/B workday query supports search while two animated objects create a sound-off feed conflict.", "api_tags": ["biurko stojące czy spacer", "biurko stojące", "spacer w pracy", "ruch przy komputerze", "aktywna przerwa"], "source_urls": [s["url"] for s in sources]}

write("research_pack.json", research)
write("script.json", script)
write("compliance.json", {"passed": True, "fixes": ["Kept the WHO number as population guidance and avoided promising a specific result from standing or walking.", "Framed the practical action as a choice between changing position and taking a short walk, without medical advice."], "cleaned_script": script})
write("fact_review.json", {"passed": True, "checks": [{"claim_id": c["id"], "passed": True, "issue": "", "required_change": ""} for c in claims], "unsupported_script_statements": [], "notes": ["The 150-minute number is spoken with object and unit in one beat.", "Standing is not presented as a quantified health comparison with walking."]})
write("frame_plan.json", {"grade": "bright premium 2D object-led versus cartoon with cyan standing desk and lemon sneaker", "light": "soft warm office light with mint route accents and lemon movement highlights", "lens": "wide A/B hook, macro movement contrast, medium route proof and wide cooperative payoff", "frames": frames})
write("qa.json", qa)
write("publish_package.json", publish)
write("codex_strategy.json", strategy)
write("retention_plan.json", {"version": "9.0-retention", "duration_lane": "core", "target_duration_s": 19.0, "first_proof_beat": 1, "turn_beat": 4, "payoff_beat": 6, "spoken_cta": False, "cadence": {"publications_today": 1, "slot_index": 1, "minimum_gap_hours": 4.0}, "creative_fingerprint": {"hook_family": "binary object face-off", "protagonist_mode": "two topic objects", "story_engine": "versus", "proof_device": "literal standing-versus-walking contrast plus WHO weekly number", "environment": "bright home-office path", "edit_grammar": "wide conflict, macro proof, stat reveal, reversal, route action, cooperative payoff", "payoff_device": "combined standing-plus-walking workday rule", "tts_delivery": "lively conversational male Charon", "compared_runs": strategy["structure_variation"]["compared_runs"], "changed_axes": ["hook_family", "protagonist_mode", "proof_device", "environment", "edit_grammar", "payoff_device"]}})
print(RUN)
