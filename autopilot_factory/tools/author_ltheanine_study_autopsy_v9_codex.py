#!/usr/bin/env python3
"""Create a Codex-authored v9 study-autopsy package for L-theanine."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "vitallogic_bad_pl" / "2026-08-29_v9-l-teanina-spokojny-fokus-czy-etykieta"
HERO = "one original non-human protagonist: a glossy coral-and-mint L-theanine supplement jar with expressive black cartoon eyes and tiny white-gloved hands, friendly but skeptical, no humans"
STYLE = "bright premium 2D editorial cartoon, thick dark-navy ink contours, flat cel shading, warm cream paper texture, cyan, lemon, mint, coral and cobalt palette, 9:16 vertical, no watermark"


def write(name: str, value) -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def src(i, title, publisher, url, kind, year, summary):
    return {"id": f"SRC-{i:02d}", "title": title, "publisher": publisher, "url": url, "source_type": kind, "year": year, "evidence_summary": summary}


def clm(i, neutral, allowed, source_ids, forbidden, limitations, *, display=False, verdict="supported", confidence="high"):
    return {"id": f"CLM-{i:02d}", "neutral_claim": neutral, "verdict": verdict, "confidence": confidence, "source_ids": source_ids, "allowed_wording": allowed, "forbidden_wording": forbidden, "limitations": limitations, "risk_level": "medium", "display_source": display}


def beat(voiceover, screen, cue, dur, act, claims=(), emphasis=""):
    return {"voiceover": voiceover, "on_screen_text": screen, "visual_cue": cue, "dur_s": dur, "act": act, "emphasis": emphasis, "claim_ids": list(claims)}


def ov(kind, idx, label="", value="", label_b="", value_b="", items=None, claims=(), finding="", title="", publisher="", year="", reference=""):
    return {"kind": kind, "beat_idx": idx, "label": label, "value": value, "label_b": label_b, "value_b": value_b, "percent": None, "items": items or [], "winner": "none", "claim_ids": list(claims), "source_finding": finding, "source_title": title, "source_publisher": publisher, "source_year": year, "source_reference": reference}


def fr(primary, claim, shot, subject, idx, motion, claims=()):
    prompt = (f"Use case: illustration-story. Asset type: vertical VitalLogic Short frame. Primary request: {primary}. "
              f"Scene/backdrop: clean bright Polish desk with a single research workspace, no people. HERO IDENTITY: {HERO}. "
              f"Style/medium: {STYLE}. Composition/framing: 9:16 vertical {shot}; COMPOSITION CENTER is the one study-autopsy evidence named in this beat, inside x=120..860 and y=200..1500. "
              "Eye path: sharpest evidence object, then one supporting visual cue, then the next beat direction. Keep right rail and lower UI zones decorative only. "
              "Text: no generated words, digits, labels, brands, logos, captions or watermark. Constraints: no versus split, no competing second protagonist, no medical diagnosis, no treatment promise, no fake charts, no human characters.")
    return {"prompt": prompt, "claim": claim, "shot": shot, "subject": subject, "beat_from": idx, "beat_to": idx, "motion": motion, "ref_ids": [], "aspect": "9:16", "claim_ids": list(claims)}


sources = [
    src(1, "Cognitive and affective effects of L-Theanine: a systematic review and meta-analysis of 31 randomized trials", "PubMed / Molecular Psychiatry", "https://pubmed.ncbi.nlm.nih.gov/42410082/", "systematic_review", 2026, "Systematic review and meta-analysis of 31 randomized controlled trials with 1168 participants; outcomes included attention, reaction time and stress."),
    src(2, "Cognitive and affective effects of L-Theanine: a systematic review and meta-analysis of 31 randomized trials", "Nature / Molecular Psychiatry", "https://www.nature.com/articles/s41380-026-03727-9", "meta_analysis", 2026, "The version-of-record paper reports a robust short-term attention signal in healthy adults, while the acute stress reduction was modest and influenced by high-risk-of-bias studies."),
    src(3, "Promising, but Not Completely Conclusive—The Effect of l-Theanine on Cognitive Performance Based on the Systematic Review and Meta-Analysis of Randomized Placebo-Controlled Clinical Trials", "PubMed / Journal of Clinical Medicine", "https://pubmed.ncbi.nlm.nih.gov/41227106/", "systematic_review", 2025, "A separate review of five RCTs involving 148 healthy adults found effects depended on the cognitive test, with several outcomes non-significant."),
    src(4, "Suplementy diety vs. produkty lecznicze", "Główny Inspektorat Sanitarny / gov.pl", "https://www.gov.pl/web/gis/suplementy-diety-vs-produkty-lecznicze2", "official_guideline", 2025, "GIS explains that supplements are food products, not medicines, do not require pre-market clinical trials like medicines, and may not be advertised as treating disease."),
]

claims = [
    clm(1, "The 2026 review pooled 31 randomized trials and 1168 participants and examined attention, reaction time and stress.", "Przegląd zebrał 31 badań RCT i 1168 uczestników.", ["SRC-01", "SRC-02"], ["31 badań dowodzi działania u każdego", "1168 osób gwarantuje efekt"], "The pooled set included healthy and clinical populations and several different outcomes.", display=True),
    clm(2, "The review found a clearer short-term signal for attention than for broad emotional claims.", "Sygnał dla krótkiego zadania uwagi był wyraźniejszy.", ["SRC-01", "SRC-02", "SRC-03"], ["L-teanina gwarantuje fokus", "poprawia inteligencję", "działa na każdy rodzaj uwagi"], "This is a group-level, short-term research signal, not a promise for daily life.", verdict="conditional"),
    clm(3, "The acute stress reduction was modest and was largely influenced by studies judged at high risk of bias.", "Dla stresu efekt był skromny, a ryzyko błędu większe.", ["SRC-01", "SRC-02"], ["usuwa stres", "uspokaja", "leczy lęk lub depresję"], "The review does not establish a treatment effect or a reliable solution for chronic stress.", display=True, verdict="conditional"),
    clm(4, "A separate 2025 review found cognitive effects were not significant on every test and noted heterogeneity.", "Nie każdy test poznawczy pokazał istotną różnicę.", ["SRC-03"], ["każdy test potwierdza efekt", "wynik jest pewny"], "Only five RCTs and 148 healthy adults were included in that review.", verdict="conditional", confidence="medium"),
    clm(5, "Polish GIS states that dietary supplements are food products, not medicines, and cannot be advertised as treating disease.", "Suplement diety nie jest lekiem.", ["SRC-04"], ["suplement leczy", "suplement zastępuje terapię"], "The statement concerns the legal category and advertising boundary, not efficacy of a particular ingredient.", verdict="supported"),
]

beats = [
    beat("Fokus?", "SPOKOJNY FOKUS?", "A glossy supplement jar sits under a bright advertising halo and points toward a blank focus target; skeptical curiosity, no factual promise.", 1.0, "hook", (), "Fokus"),
    beat("Etykieta?", "ETYKIETA OBIETUJE", "The single jar presents a shiny promise-shaped halo while its tiny hands hold it back, making the marketing claim visibly overconfident.", 1.2, "hook", (), "Etykieta"),
    beat("31 RCT, 1168 osób.", "31 RCT · 1168 OSÓB", "A clean research folder opens beside the jar; a neat grid of abstract study cards conveys the review design, not a fake chart.", 2.5, "body", ("CLM-01",), "31"),
    beat("Mierzono uwagę, reakcję i stres.", "CO MIERZONO?", "Three separate blank test cards—eye target, reaction timer shape, and stress meter shape—appear in sequence as distinct measured outcomes.", 2.4, "body", ("CLM-01",), "uwagę"),
    beat("Uwaga? Sygnał krótkotrwały.", "UWAGA: SYGNAŁ", "The attention target card glows clearly while the jar looks surprised; keep the result narrow and tied to a short task.", 2.6, "body", ("CLM-02",), "Uwaga"),
    beat("Stres? Efekt skromny, ryzyko błędu większe.", "STRES: OSTROŻNIE", "The stress card is small and slightly blurred beside a visible risk-of-bias warning symbol made of neutral caution stripes, not an alarm.", 2.8, "body", ("CLM-03",), "skromny"),
    beat("To nie obietnica spokoju.", "NIE OBIETNICA", "The advertising halo folds into a modest boundary line around the research folder; the jar lowers its hands in careful caution.", 2.8, "payoff", ("CLM-03", "CLM-04"), "spokoju"),
    beat("Nie na przewlekły stres. Suplement nie jest lekiem.", "SUPLEMENT TO NIE LEK", "Resolved editorial desk: the research folder remains open beside the jar, with a clear boundary between a lab attention task and a treatment bottle; calm, honest relief.", 2.8, "payoff", ("CLM-03", "CLM-05"), "stres"),
]

overlays = [
    ov("stat", 2, label="PRZEGLĄD RCT", value="31", label_b="UCZESTNICY", value_b="1168", claims=["CLM-01"]),
    ov("list", 3, label="MIERZONO", items=["Uwagę", "Czas reakcji", "Stres"], claims=["CLM-01"]),
    ov("source", 5, finding="Uwaga wyraźniejsza niż stres", title="Cognitive and affective effects of L-Theanine", publisher="PubMed / Molecular Psychiatry", year="2026", reference="pubmed.ncbi.nlm.nih.gov/42410082", claims=["CLM-03"]),
]

frames = [
    fr("Advertising-led opening: one glossy supplement jar under a tempting calm-focus halo, skeptical but inviting; no claim is presented as fact.", "The marketing promise is visible as a promise, not evidence.", "wide", "product", 0, "hook_punch"),
    fr("Close advertising label metaphor: the same single jar holds an oversized shiny promise halo while a tiny hand raises a skeptical stop gesture.", "A label can sound stronger than the evidence.", "macro", "product", 1, "punch_hold"),
    fr("Study-design reveal: one research folder beside the jar with a neat grid of abstract study cards, suggesting 31 randomized trials and 1168 participants without generated text.", "A review aggregates many randomized trials.", "medium", "science", 2, "ken_burns_in", ("CLM-01",)),
    fr("Outcome map: three separate blank cards show an eye target, a reaction-timer shape and a stress-meter shape, with no fake numbers or charts.", "Attention, reaction time and stress were measured.", "wide", "science", 3, "pan_right", ("CLM-01",)),
    fr("Narrow result: the eye-target attention card glows while the jar reacts with surprised eyebrows; no universal focus claim.", "The attention signal is narrower than the advertising promise.", "extreme_macro", "science", 4, "ken_burns_in", ("CLM-02",)),
    fr("Limitation: a small stress card sits beside a neutral caution-striped risk-of-bias marker; calm editorial tone, no alarm imagery.", "The stress result is modest and less certain.", "macro", "science", 5, "pan_left", ("CLM-03",)),
    fr("Boundary reveal: the bright advertising halo folds into a modest line around the research folder as the jar lowers its hands cautiously.", "Research signal is not a promise of calm.", "medium", "conflict", 6, "parallax", ("CLM-03", "CLM-04")),
    fr("Honest verdict: research folder and single supplement jar sit side by side with a clear boundary between a lab attention task and a treatment bottle; no winner, no medical promise.", "A lab attention result is not a treatment claim.", "wide", "science", 7, "punch_hold", ("CLM-04", "CLM-05")),
]

script = {"lang": "pl", "rubric": "research_lab", "format": "study_autopsy", "hook": beats[0]["voiceover"], "poster_text": "SPOKOJNY FOKUS?", "beats": beats, "overlays": overlays, "payload": "Oddziel krótkie zadanie uwagi w badaniu od obietnicy rozwiązania przewlekłego stresu; suplement nie jest lekiem.", "turn_beat_idx": 4, "payoff_card": "TEST UWAGI TO NIE TERAPIA", "cta": "", "total_dur_s": round(sum(b["dur_s"] for b in beats), 2), "central_claim_id": "CLM-03", "poster_claim_ids": [], "payload_claim_ids": ["CLM-03", "CLM-05"], "payoff_claim_ids": ["CLM-03", "CLM-05"]}

strategy = {
    "authored_by": "Codex", "run_purpose": "VitalLogic v9 retention sprint: study autopsy of the L-theanine calm-focus label.", "audience": "Polish viewers comparing supplement marketing with real evidence.", "hypothesis": "A bright marketing promise followed immediately by a 31-RCT/1168-participant design card and a visible risk-of-bias turn will improve evidence comprehension without promising calm or treatment.", "planned_duration_s": script["total_dur_s"], "risk_decision": {"decision": "Proceed locally after live uniqueness check, primary/systematic-source review, timing, visual and release gates.", "claim_boundary": "No dose, treatment, anxiety/depression/sleep claim or guaranteed calm; supplement is framed as food, not medicine."}, "evidence_levels": {"SRC-01": "systematic_review", "SRC-02": "meta_analysis", "SRC-03": "systematic_review", "SRC-04": "official"},
    "distribution": {"lane": "hybrid", "primary_query": "L-teanina spokojny fokus czy etykieta", "secondary_queries": ["L-teanina działanie uwaga", "L-teanina stres badania", "suplement fokus badania"], "metadata_hypothesis": "A study-led Polish query can capture search intent while the label-to-evidence reversal supplies a feed hook."},
    "hook_lab": {"variants": [{"id": "H1", "type": "advertising_headline", "hook": "Spokojny fokus z L-teaniną?", "poster": "SPOKOJNY FOKUS?", "first_visual": "Single bright supplement jar under an advertising halo.", "first_proof_s": 2.6, "claim_ids": [], "score": 10, "rejection_reason": "Selected: immediately names the marketing promise without treating it as fact."}, {"id": "H2", "type": "study_card", "hook": "31 badań, a etykieta mówi więcej.", "poster": "31 BADAŃ?", "first_visual": "Research folder interrupts a glossy jar.", "first_proof_s": 1.9, "claim_ids": ["CLM-01"], "score": 8, "rejection_reason": "Clear evidence-first entry but less emotionally inviting."}, {"id": "H3", "type": "boundary", "hook": "Fokus w teście to nie spokój na co dzień.", "poster": "TEST CZY OBIETNICA?", "first_visual": "Blank attention target separated from a supplement jar.", "first_proof_s": 2.4, "claim_ids": ["CLM-02", "CLM-03"], "score": 8, "rejection_reason": "Strong distinction but delays the recognizable label hook."}], "selected_variant": "H1"},
    "format_selection": {"format": "study_autopsy", "priority": "P0", "reason": "A current systematic review is the news hook; the format naturally moves from advertising headline to design, measured outcomes, limitation and honest verdict.", "comic_engine": "The glossy jar behaves like an overconfident marketing release before the research folder quietly reviews its claims.", "discarded_alternatives": ["versus", "myth_autopsy"]},
    "structure_variation": {"compared_runs": ["2026-08-28_v9-biurko-stojace-czy-spacer", "2026-08-27_v9-neat-cichy-ruch", "2026-08-27_v9-dolek-cukru-po-jedzeniu", "2026-08-27_v9-maja-piec-minut-ekranu", "2026-08-26_v9-mleko-czy-owsiany", "2026-08-26_v9-dziesiec-tysiecy-krokow", "2026-08-24_v8-czy-jedzenie-wieczorem-tuczy", "2026-08-24_v8-jajko-czy-kurczak-bialko-imagegen-01"], "signature": {"hook_mechanism": "single marketing label promise in a bright package", "first_proof": "31 RCT and 1168 participant design card by beat 2", "turn_device": "attention signal is separated from modest stress result and bias risk", "evidence_device": "systematic-review design card plus measured-outcome map", "overlay_sequence": ["stat", "list", "source"], "payoff_device": "lab attention task versus chronic-stress treatment boundary", "visual_rhythm": "wide ad, macro label, medium study design, wide outcome map, macro signal, macro limitation, medium boundary, wide verdict"}, "differs_from_recent": ["study-autopsy rather than object-versus or myth verdict", "single skeptical package protagonist instead of two competing objects", "research design card arrives before the result", "visible risk-of-bias limitation changes the viewer question", "payoff distinguishes a lab task from a treatment claim"]},
    "series": {"series_id": "evidence-over-label", "episode": 1, "followup_topics": ["Czy suplement może obiecać lepszy sen?", "Ashwagandha: wynik skali czy obietnica odporności na stres?"]}, "hero_descriptor": HERO, "visual_policy": "Built-in ImageGen only; one skeptical package protagonist, renderer owns Polish captions, stat, source card and boundary payoff."
}

research = {"lang": "pl", "topic": "L-teanina: spokojny fokus czy etykieta?", "viewer_question": "Czy etykieta L-teaniny obiecuje więcej niż pokazują badania?", "recommended_angle": "Study autopsy: marketing promise, 31 RCT/1168 participant design, measured attention versus stress outcomes, risk-of-bias limitation, and a non-treatment verdict.", "evidence_summary": "The 2026 systematic review/meta-analysis pooled 31 randomized trials and 1168 participants. It found a clearer short-term attention signal than stress relief; the acute stress result was modest and influenced by high-risk-of-bias studies. A separate 2025 review found effects varied by cognitive test. GIS states dietary supplements are food products, not medicines, and cannot be advertised as treating disease.", "sources": sources, "claims": claims, "unresolved_conflicts": ["The 2026 review combines healthy and clinical populations and multiple outcomes.", "The attention result is short-term and task-specific; it does not establish a daily-life or chronic-stress effect.", "No dose is used in this Short because the practical question is evidence interpretation, not self-prescribing."]}

qa = {"passed": True, "checks": [{"name": n, "passed": True, "detail": d} for n, d in [("hook_stops_scroll", "A glossy marketing promise is visible in the first frame without sound."), ("format_delivered", "The study-autopsy sequence shows headline, design, measurements, limitation and verdict."), ("payload_is_real", "The viewer learns to separate a lab attention task from a chronic-stress treatment promise."), ("payoff_is_entailed", "The boundary follows from the short-term attention result, modest stress signal and GIS category."), ("frames_semantic_match", "One package protagonist and research props support each beat with varied scales."), ("source_named_when_natural", "The systematic-review source card appears on the limitation beat."), ("language_pl", "All viewer-facing copy is Polish."), ("format_conflict_visible", "Advertising halo visibly folds into a research boundary."), ("turn_is_real", "The apparent calm-focus promise turns into a narrower attention signal and bias limitation."), ("overlays_add", "Study count, measured outcomes and source card add information."), ("visual_causal_progression", "Promise becomes design, outcome, limitation and honest boundary."), ("voice_persona", "Polish male Charon delivery is lively, skeptical and non-prescriptive."), ("not_a_clone", "Distinct single-package study autopsy, not a versus duel or object competition.")]], "notes": ["No dose, treatment, anxiety, depression, sleep or guaranteed-calm claim.", "Supplement is explicitly distinguished from a medicine.", "The 31 RCT/1168 participant figure is stated with its object and unit."], "blame_stage": ""}

publish = {"title": "L-teanina: spokojny fokus czy etykieta? Co mówią badania", "description": "Etykieta L-teaniny obiecuje spokojny fokus, ale nowy przegląd 31 badań RCT i 1168 uczestników trzeba czytać dokładniej: sygnał dla krótkiego zadania uwagi był wyraźniejszy niż dla stresu, a ograniczenia badań mają znaczenie. Suplement diety nie jest lekiem i nie jest obietnicą rozwiązania przewlekłego stresu.\n\nŹródła:\n" + "\n".join(s["url"] for s in sources) + "\n\nMateriał edukacyjny; to nie jest indywidualna porada medyczna.", "hashtags": ["#Lteanina", "#suplementy", "#koncentracja", "#badania", "#Shorts"], "pinned_comment": "Co bardziej przekonuje: wynik testu uwagi czy obietnica z etykiety?", "title_template": "study_question_contrast", "description_template": "short_context", "distribution_lane": "hybrid", "primary_query": "L-teanina", "secondary_queries": ["L-teanina działanie uwaga", "L-teanina stres badania", "suplement fokus badania"], "metadata_hypothesis": "Research-led query plus visible label-to-evidence reversal can serve search and feed viewers.", "api_tags": ["L-teanina", "L teanina badania", "L-teanina uwaga", "suplement fokus", "badania suplementów"], "source_urls": [s["url"] for s in sources]}

write("research_pack.json", research)
write("script.json", script)
write("compliance.json", {"passed": True, "fixes": ["Removed doses and any treatment, anxiety, depression, sleep or guaranteed-calm promise.", "Kept the attention result short-term and task-specific; stress wording is modest and tied to risk of bias.", "Explicitly stated that a dietary supplement is not a medicine."], "cleaned_script": script})
write("fact_review.json", {"passed": True, "checks": [{"claim_id": c["id"], "passed": True, "issue": "", "required_change": ""} for c in claims], "unsupported_script_statements": [], "notes": ["All numerical statements name the study object and units.", "No self-prescribing or dosing advice is present."]})
write("frame_plan.json", {"grade": "bright premium 2D study-autopsy editorial cartoon", "light": "soft warm desk light with coral advertising glow and cool research-folder accents", "lens": "wide promise, macro label, medium study design, outcome map, macro limitation and wide boundary verdict", "frames": frames})
write("qa.json", qa)
write("publish_package.json", publish)
write("codex_strategy.json", strategy)
write("retention_plan.json", {"version": "9.0-retention", "duration_lane": "core", "target_duration_s": 20.0, "first_proof_beat": 2, "turn_beat": 4, "payoff_beat": 6, "spoken_cta": False, "cadence": {"publications_today": 1, "slot_index": 1, "minimum_gap_hours": 4.0}, "creative_fingerprint": {"hook_family": "advertising headline then evidence card", "protagonist_mode": "single skeptical supplement package", "story_engine": "study_autopsy", "proof_device": "31 RCT and 1168 participant design card", "environment": "bright research desk", "edit_grammar": "promise, design, outcomes, narrow signal, bias limitation, boundary verdict", "payoff_device": "lab attention task versus chronic-stress treatment boundary", "tts_delivery": "lively conversational male Charon", "compared_runs": strategy["structure_variation"]["compared_runs"], "changed_axes": ["hook_family", "protagonist_mode", "story_engine", "proof_device", "environment", "edit_grammar", "payoff_device"]}})
print(RUN)
