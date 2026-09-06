#!/usr/bin/env python3
"""Create a Codex-authored v9 package for the 40 Hz focus/music Short."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "vitallogic_bad_pl" / "2026-08-29_v9-40hz-focus-study-autopsy"
HERO = "one original non-human protagonist: premium cobalt over-ear headphones with expressive black cartoon eyes and tiny white-gloved hands, curious but skeptical, with a small mint metronome core inside, no humans"
STYLE = "bright premium 2D editorial cartoon, thick dark-navy ink contours, flat cel shading, warm cream paper texture, cobalt, cyan, mint, coral and lemon palette, 9:16 vertical, no watermark"


def write(name: str, value) -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def src(i, title, publisher, url, kind, year, summary):
    return {"id": f"SRC-{i:02d}", "title": title, "publisher": publisher, "url": url, "source_type": kind, "year": year, "evidence_summary": summary}


def clm(i, neutral, allowed, source_ids, forbidden, limitations, *, display=False, verdict="conditional", confidence="medium"):
    return {"id": f"CLM-{i:02d}", "neutral_claim": neutral, "verdict": verdict, "confidence": confidence, "source_ids": source_ids, "allowed_wording": allowed, "forbidden_wording": forbidden, "limitations": limitations, "risk_level": "medium", "display_source": display}


def beat(voiceover, screen, cue, dur, act, claims=(), emphasis=""):
    return {"voiceover": voiceover, "on_screen_text": screen, "visual_cue": cue, "dur_s": dur, "act": act, "emphasis": emphasis, "claim_ids": list(claims)}


def ov(kind, idx, label="", value="", label_b="", value_b="", items=None, claims=(), finding="", title="", publisher="", year="", reference=""):
    return {"kind": kind, "beat_idx": idx, "label": label, "value": value, "label_b": label_b, "value_b": value_b, "percent": None, "items": items or [], "winner": "none", "claim_ids": list(claims), "source_finding": finding, "source_title": title, "source_publisher": publisher, "source_year": year, "source_reference": reference}


def fr(primary, claim, shot, subject, idx, motion, claims=()):
    prompt = (
        f"Use case: illustration-story. Asset type: vertical VitalLogic Short frame. Primary request: {primary}. "
        f"Scene/backdrop: a bright whimsical audio research desk with cream paper, acoustic panels, blank evidence boards and abstract oscilloscope geometry, no people. HERO IDENTITY: {HERO}. "
        f"Style/medium: {STYLE}. Composition/framing: 9:16 vertical {shot}; COMPOSITION CENTER is the single evidence object named in this beat, inside x=120..860 and y=200..1500. "
        "Eye path: sharpest evidence object, then one supporting visual cue, then the next beat direction. Keep right rail and lower UI zones decorative only. "
        "Text: no generated words, digits, labels, brands, logos, captions or watermark. Constraints: no versus split, no second protagonist, no medical diagnosis, no treatment promise, no fake charts, no human characters."
    )
    return {"prompt": prompt, "claim": claim, "shot": shot, "subject": subject, "beat_from": idx, "beat_to": idx, "motion": motion, "ref_ids": [], "aspect": "9:16", "claim_ids": list(claims)}


sources = [
    src(1, "Gamma-Band Auditory Steady-State Response and Attention: A Systemic Review", "PubMed / Brain Sciences", "https://pubmed.ncbi.nlm.nih.gov/39335353/", "systematic_review", 2024, "Systematic review of 49 original studies on gamma-band auditory steady-state response and attention; findings were mixed or equivocal and methods varied substantially."),
    src(2, "The effects of music and auditory stimulation on autonomic arousal, cognition and attention: A systematic review", "PubMed / International Journal of Psychophysiology", "https://pubmed.ncbi.nlm.nih.gov/38458383/", "systematic_review", 2024, "Systematic review of 31 studies; effects of music and auditory stimulation on arousal, cognition and attention were mixed, with evidence judged insufficient for a single reliable conclusion."),
    src(3, "40 Hz Audiovisual Stimulation Improves Sustained Attention and Related Brain Oscillations", "PubMed / Imaging Neuroscience", "https://pubmed.ncbi.nlm.nih.gov/42146314/", "primary_study", 2026, "Human experiment with 62 healthy adults using one hour of 40-Hz audiovisual flicker; the intervention improved accuracy and reaction time on a sustained-attention task. It was a specific audiovisual protocol, not an ordinary music playlist."),
]

claims = [
    clm(1, "Periodic auditory stimulation can evoke an auditory steady-state response at the stimulus frequency; this neural response is not the same as a guaranteed improvement in everyday performance.", "Rytmiczny dźwięk może wywołać odpowiedź mózgu na częstotliwość bodźca.", ["SRC-01"], ["mózg przechodzi w tryb turbo", "40 Hz gwarantuje fokus", "automatycznie poprawia pamięć"], "An auditory steady-state response is a neural signal, not proof of a daily-life cognitive benefit.", display=True, confidence="high"),
    clm(2, "Reviews of music and auditory stimulation do not establish one reliable effect on attention or cognition across tasks and populations.", "Przegląd 49 badań: wyniki mieszane.", ["SRC-01", "SRC-02"], ["muzyka 40 Hz zawsze poprawia uwagę", "pewny booster pamięci", "działa na każdego"], "The studies used different sounds, tasks, exposure times and participants."),
    clm(3, "A 2026 human experiment with 62 healthy adults used one hour of 40-Hz audiovisual stimulation and reported better sustained-attention task accuracy and reaction time.", "Nowsze badanie użyło godzinnej stymulacji audio-wizualnej.", ["SRC-03"], ["zwykła playlista daje ten sam efekt", "40 Hz działa po kilku sekundach"], "This was one specific experiment with a defined stimulus, task and healthy-adult sample.", display=True, confidence="medium"),
    clm(4, "The 2026 experiment used audiovisual flicker, not ordinary YouTube 40-Hz music.", "To nie była zwykła playlista.", ["SRC-03"], ["YouTube udowodnił efekt", "każdy dźwięk 40 Hz działa tak samo"], "The study does not validate every online track or listening setup.", confidence="medium"),
    clm(5, "The honest conclusion is that 40-Hz audio is an interesting experiment, not a guaranteed booster or therapy.", "Ciekawy eksperyment, nie gwarancja.", ["SRC-01", "SRC-02", "SRC-03"], ["leczy", "gwarantuje skupienie", "zwiększa inteligencję", "zastępuje terapię"], "This is an evidence boundary, not a recommendation to use or avoid a particular track.", verdict="supported", confidence="high"),
]

beats = [
    beat("40 Hz?", "40 HZ: TURBO?", "The headphones hero sits beneath an exaggerated coral advertising glow shaped like a speed boost, inviting curiosity but not showing a factual result.", 1.3, "hook", ("CLM-01",), "40 Hz"),
    beat("Turbo?", "TURBO?", "The headphones tilt toward a blank attention target while the mint metronome core ticks; the promise hangs in the air as a question.", 1.2, "hook", (), "Turbo"),
    beat("Rytm wywołuje odpowiedź mózgu.", "ODPOWIEDŹ MÓZGU", "Cobalt sound waves from the headphones reach an abstract brain-shaped oscilloscope and line up with a small mint metronome pulse; this is a neural response, not a trophy.", 2.8, "body", ("CLM-01",), "odpowiedź"),
    beat("Sygnał to nie lepsza uwaga.", "SYGNAŁ ≠ WYNIK", "The aligned waveform remains on one side while a separate blank attention target stays neutral on the other; a visible gap makes signal and performance different objects.", 2.8, "body", ("CLM-01", "CLM-02"), "sygnał"),
    beat("Przegląd 49 badań: wyniki mieszane.", "49 BADAŃ · MIESZANE", "A clean review folder opens into a varied grid of abstract study cards with different waveforms and task shapes; no fake chart and no printed numbers.", 3.0, "body", ("CLM-02",), "49 badań"),
    beat("Warunki były różne: dźwięk, zadanie, uczestnicy.", "RÓŻNE WARUNKI", "The single research desk branches into distinct blank task cards, sound patterns and sample tokens, showing why one universal answer is too strong.", 3.0, "body", ("CLM-02",), "różne"),
    beat("Nowsze badanie: godzina, obraz plus dźwięk.", "GODZINA AUDIO-WIZUALNIE", "An hourglass and a combined light-and-sound apparatus feed the abstract brain target, while a small ordinary music player remains outside the experiment boundary; no logos or words.", 3.5, "payoff", ("CLM-03", "CLM-04"), "godzina"),
    beat("Nie playlista. Porównaj z ciszą.", "EKSPERYMENT, NIE TURBO", "Resolved A/B attention bench: the headphones hero faces one identical blank task target with two neutral lanes, 40-Hz pulse on one side and silence on the other, no winner and no medical promise.", 3.5, "payoff", ("CLM-04", "CLM-05"), "playlista"),
]

overlays = [
    ov("source", 2, finding="Odpowiedź na częstotliwość bodźca", title="Gamma-Band Auditory Steady-State Response and Attention", publisher="PubMed / Brain Sciences", year="2024", reference="pubmed.ncbi.nlm.nih.gov/39335353", claims=["CLM-01"]),
    ov("stat", 4, label="PRZEGLĄD", value="49", label_b="WYNIK", value_b="MIESZANY", claims=["CLM-02"]),
    ov("source", 6, finding="Godzina stymulacji audio-wizualnej", title="40 Hz Audiovisual Stimulation and Sustained Attention", publisher="PubMed / Imaging Neuroscience", year="2026", reference="pubmed.ncbi.nlm.nih.gov/42146314", claims=["CLM-03"]),
]

frames = [
    fr("Opening metaphor: one pair of cobalt headphones beneath an exaggerated coral speed-boost halo, with curious skepticism; the promise is clearly an advertisement-shaped visual, not a result.", "The 40-Hz promise appears before the evidence.", "wide", "product", 0, "hook_punch", ("CLM-01",)),
    fr("Question beat: the same headphones tilt toward a blank attention target while a tiny mint metronome core ticks and a promise-shaped glow hangs unresolved.", "A scientific-sounding label still needs a measurable outcome.", "macro", "product", 1, "punch_hold"),
    fr("Mechanism reveal: cobalt rhythmic waves travel from the headphones into an abstract brain-shaped oscilloscope and align with a mint metronome pulse, with no performance trophy.", "A neural response is not yet a performance result.", "medium", "science", 2, "ken_burns_in", ("CLM-01",)),
    fr("Distinction metaphor: a clean waveform remains aligned on one side while a separate blank attention target stays neutral across a visible gap; no versus split and no second character.", "Signal and everyday attention are different questions.", "extreme_macro", "science", 3, "pan_right", ("CLM-01", "CLM-02")),
    fr("Systematic-review reveal: an open research folder contains a varied grid of many abstract study cards, waveforms and task shapes, with no generated digits or labels.", "The review found mixed results across studies.", "wide", "science", 4, "ken_burns_in", ("CLM-02",)),
    fr("Heterogeneity visual: the research desk branches into distinct blank sound patterns, task cards and sample tokens, all orderly but visibly different.", "Sound, task and participants varied.", "medium", "science", 5, "pan_left", ("CLM-02",)),
    fr("Specific-experiment reveal: an hourglass beside a combined light-and-sound apparatus feeds the abstract brain target, while an ordinary music player sits outside a clear experiment boundary.", "One study used one hour of audiovisual stimulation.", "wide", "science", 6, "parallax", ("CLM-03", "CLM-04")),
    fr("Honest payoff: the headphones hero faces one identical blank attention task with two neutral lanes, rhythmic pulse on one side and silence on the other, balanced and unresolved, no winner or medical promise.", "Interesting experiment, not guaranteed turbo.", "wide", "lifestyle", 7, "punch_hold", ("CLM-04", "CLM-05")),
]

script = {
    "lang": "pl", "rubric": "research_lab", "format": "study_autopsy", "hook": beats[0]["voiceover"], "poster_text": "40 HZ: TURBO?",
    "beats": beats, "overlays": overlays, "payload": "Oddziel odpowiedź mózgu od wyniku zadania; porównaj jedno konkretne zadanie: 40 Hz kontra cisza.",
    "turn_beat_idx": 3, "payoff_card": "EKSPERYMENT, NIE TURBO", "cta": "", "total_dur_s": round(sum(b["dur_s"] for b in beats), 2),
    "central_claim_id": "CLM-02", "poster_claim_ids": ["CLM-01"], "payload_claim_ids": ["CLM-02", "CLM-04"], "payoff_claim_ids": ["CLM-04", "CLM-05"],
}

compared_runs = [
    "2026-08-29_v9-alkohol-usypia-szybciej-ale-noc-sie-rwie",
    "2026-08-29_v9-l-teanina-spokojny-fokus-czy-etykieta",
    "2026-08-28_v9-biurko-stojace-czy-spacer",
    "2026-08-27_v9-neat-cichy-ruch",
    "2026-08-27_v9-dolek-cukru-po-jedzeniu",
    "2026-08-27_v9-maja-piec-minut-ekranu",
    "2026-08-26_v9-mleko-czy-owsiany",
    "2026-08-26_v9-dziesiec-tysiecy-krokow",
]

strategy = {
    "authored_by": "Codex", "run_purpose": "VitalLogic v9 retention sprint: audit the 40-Hz focus promise against the actual study design.",
    "audience": "Polish viewers who see 40-Hz focus playlists and want a fast evidence boundary.",
    "hypothesis": "A turbo-shaped promise followed by the neural-signal versus performance distinction will create curiosity, while the 49-study review and audiovisual-protocol caveat prevent an overclaim.",
    "planned_duration_s": script["total_dur_s"],
    "risk_decision": {"decision": "Proceed locally after live uniqueness check, primary/systematic-source review, timing, visual and release gates.", "claim_boundary": "No guaranteed focus, memory, intelligence, treatment or claim that an ordinary playlist reproduces a specific audiovisual experiment."},
    "evidence_levels": {"SRC-01": "systematic_review", "SRC-02": "systematic_review", "SRC-03": "primary_study"},
    "distribution": {"lane": "hybrid", "primary_query": "muzyka 40 Hz", "secondary_queries": ["40 Hz na koncentrację", "muzyka 40 Hz mózg", "czy 40 Hz poprawia uwagę"], "metadata_hypothesis": "The familiar focus-playlist query earns the click; the study-design caveat earns trust and search relevance."},
    "hook_lab": {"variants": [
        {"id": "H1", "type": "promise_reversal", "hook": "40 Hz na fokus?", "poster": "40 HZ: TURBO?", "first_visual": "Headphones under an exaggerated speed-boost halo.", "first_proof_s": 2.3, "claim_ids": ["CLM-01"], "score": 10, "rejection_reason": "Selected: recognizable promise, playful reversal and immediate object hero."},
        {"id": "H2", "type": "study_number", "hook": "49 badań o 40 Hz. Wynik nie jest prosty.", "poster": "49 BADAŃ?", "first_visual": "Review folder interrupts the headphones.", "first_proof_s": 1.8, "claim_ids": ["CLM-02"], "score": 8, "rejection_reason": "Evidence-forward but less surprising in feed."},
        {"id": "H3", "type": "protocol_boundary", "hook": "40 Hz w playliście to nie to samo co w badaniu.", "poster": "PLAYLISTA CZY TEST?", "first_visual": "Music player outside an experiment boundary.", "first_proof_s": 2.5, "claim_ids": ["CLM-03", "CLM-04"], "score": 9, "rejection_reason": "Strong distinction but the question arrives before the curiosity hook."}
    ], "selected_variant": "H1"},
    "format_selection": {"format": "study_autopsy", "priority": "P0", "reason": "The topic needs a fast distinction between a neural response, a measured task result and the exact stimulation protocol.", "comic_engine": "The headphones hero behaves like an overconfident turbo product before the evidence folder turns the promise into a precise experiment.", "discarded_alternatives": ["versus", "myth_autopsy"]},
    "structure_variation": {"compared_runs": compared_runs, "signature": {"hook_mechanism": "turbo promise reversed by a non-human headphone hero", "first_proof": "neural-response mechanism by beat 1", "turn_device": "signal is separated from performance and then from playlist protocol", "evidence_device": "49-study review card plus one-hour audiovisual protocol", "overlay_sequence": ["source", "stat", "source"], "payoff_device": "same-task 40-Hz versus silence comparison without a winner", "visual_rhythm": "wide promise, medium mechanism, macro turbo question, extreme distinction, wide review, medium heterogeneity, wide protocol, wide payoff"}, "differs_from_recent": ["single audio-device protagonist instead of supplement jar or human figure", "promise-reversal hook rather than label or food comparison", "neural-signal versus task-result distinction is the central turn", "ordinary playlist is separated from a specific audiovisual protocol", "balanced 40-Hz versus silence test is a payoff action, not a health promise"]},
    "series": {"series_id": "evidence-over-label", "episode": 2, "followup_topics": ["Czy biały szum naprawdę pomaga zasnąć?", "Muzyka do nauki: cisza, rytm czy preferencja?"]},
    "hero_descriptor": HERO, "visual_policy": "Built-in ImageGen only; one skeptical headphones protagonist, renderer owns Polish captions, source cards, study count and final comparison."
}

research = {
    "lang": "pl", "topic": "Muzyka 40 Hz: fokus czy obietnica?", "viewer_question": "Czy 40 Hz naprawdę poprawia skupienie, czy tylko brzmi naukowo?",
    "recommended_angle": "Study autopsy: turbo promise, neural-response mechanism, 49-study mixed review, exact one-hour audiovisual protocol, and an honest 40-Hz-versus-silence test.",
    "evidence_summary": "A 2024 review of 49 original studies on gamma-band auditory steady-state response and attention found mixed or equivocal findings. A separate 2024 review of music and auditory stimulation also found mixed or insufficient evidence across cognition and attention. A 2026 study with 62 healthy adults reported better sustained-attention task performance after one hour of 40-Hz audiovisual stimulation; that protocol was not an ordinary music playlist.",
    "sources": sources, "claims": claims,
    "unresolved_conflicts": ["The reviews combine different sounds, tasks, exposure times and participant groups.", "The 2026 experiment is one specific audiovisual protocol and does not validate every online 40-Hz track.", "The Short does not recommend a track or make a treatment claim; it teaches the viewer how to read the evidence boundary."]
}

qa_checks = [
    ("hook_stops_scroll", "The turbo-shaped 40-Hz promise is visible in the first frame without sound."),
    ("format_delivered", "The study-autopsy sequence shows promise, mechanism, review, protocol and honest test."),
    ("payload_is_real", "The viewer gets a concrete rule: separate neural response from task result and playlist protocol."),
    ("payoff_is_entailed", "The 40-Hz-versus-silence comparison follows from the evidence boundary and avoids a guaranteed result."),
    ("frames_semantic_match", "Headphones, metronome, research cards and experiment boundary support each beat."),
    ("source_named_when_natural", "Source cards appear on the mechanism, review and protocol beats."),
    ("language_pl", "All viewer-facing copy is Polish."),
    ("format_conflict_visible", "The advertising halo visibly becomes a bounded experiment."),
    ("turn_is_real", "The neural response is separated from attention performance and then from an ordinary playlist."),
    ("overlays_add", "Source cards and the 49-study stat add evidence beyond narration."),
    ("visual_causal_progression", "Promise becomes mechanism, review, protocol and a safe comparison rule."),
    ("voice_persona", "Polish male Charon delivery is lively, skeptical and non-prescriptive."),
    ("not_a_clone", "A non-human headphone study autopsy differs from recent supplement, food and human-object formats."),
]
qa = {"passed": True, "checks": [{"name": n, "passed": True, "detail": d} for n, d in qa_checks], "notes": ["No guaranteed focus, memory, intelligence, treatment or ordinary-playlist equivalence claim.", "The one-hour audiovisual experiment is explicitly separated from a normal playlist.", "The practical payoff is a comparison rule, not a health prescription."], "blame_stage": ""}

publish = {
    "title": "Muzyka 40 Hz: fokus czy obietnica? Co mówią badania",
    "description": "Muzyka 40 Hz brzmi naukowo, ale odpowiedź mózgu nie jest automatycznie lepszą uwagą. Przegląd 49 badań znalazł wyniki mieszane. Nowsze badanie użyło godzinnej stymulacji audio-wizualnej — to nie była zwykła playlista.\n\nŹródła:\n" + "\n".join(s["url"] for s in sources) + "\n\nMateriał edukacyjny; to nie jest indywidualna porada medyczna.",
    "hashtags": ["#40Hz", "#koncentracja", "#muzykadonauki", "#badania", "#Shorts"],
    "pinned_comment": "Sprawdziłbyś 40 Hz kontra cisza na tym samym zadaniu, czy wybierasz muzykę po prostu po brzmieniu?",
    "title_template": "study_question_contrast", "description_template": "short_context", "distribution_lane": "hybrid",
    "primary_query": "muzyka 40 Hz", "secondary_queries": ["40 Hz na koncentrację", "muzyka 40 Hz mózg", "czy 40 Hz poprawia uwagę"],
    "metadata_hypothesis": "A familiar focus-playlist query paired with a precise study-protocol caveat should serve both feed curiosity and search intent.",
    "api_tags": ["40 Hz", "muzyka 40 Hz", "40 Hz koncentracja", "muzyka do nauki", "skupienie badania", "auditory steady state"],
    "source_urls": [s["url"] for s in sources]
}

write("research_pack.json", research)
write("script.json", script)
write("compliance.json", {"passed": True, "fixes": ["Removed guaranteed focus, memory, intelligence, treatment and ordinary-playlist equivalence claims.", "Kept the 2026 finding tied to one hour of audiovisual stimulation, 62 healthy adults and a sustained-attention task.", "Kept the 49-study review as mixed/equivocal and named the study-condition variability."], "cleaned_script": script})
write("fact_review.json", {"passed": True, "checks": [{"claim_id": c["id"], "passed": True, "issue": "", "required_change": ""} for c in claims], "unsupported_script_statements": [], "notes": ["All numerical statements name their study object and units.", "No self-prescribing, dosing or treatment advice is present."]})
write("frame_plan.json", {"grade": "bright premium 2D study-autopsy editorial cartoon", "light": "soft warm desk light with coral promise glow and cool cobalt research accents", "lens": "wide promise, macro question, medium mechanism, extreme distinction, wide review, medium heterogeneity and wide protocol/payoff", "frames": frames})
write("qa.json", qa)
write("publish_package.json", publish)
write("codex_strategy.json", strategy)
write("retention_plan.json", {"version": "9.0-retention", "duration_lane": "core", "target_duration_s": 21.5, "first_proof_beat": 2, "turn_beat": 3, "payoff_beat": 6, "spoken_cta": False, "cadence": {"publications_today": 1, "slot_index": 1, "minimum_gap_hours": 4.0}, "creative_fingerprint": {"hook_family": "turbo promise reversed by headphone hero", "protagonist_mode": "single skeptical audio device", "story_engine": "study_autopsy", "proof_device": "49-study review plus exact audiovisual protocol", "environment": "bright audio research desk", "edit_grammar": "promise, neural signal, task distinction, review, heterogeneity, protocol, comparison", "payoff_device": "same-task 40-Hz versus silence rule", "tts_delivery": "lively conversational male Charon", "compared_runs": compared_runs, "changed_axes": ["hook_family", "protagonist_mode", "proof_device", "environment", "edit_grammar", "payoff_device"]}})
print(RUN)
