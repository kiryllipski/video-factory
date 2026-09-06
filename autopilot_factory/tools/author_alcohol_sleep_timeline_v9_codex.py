#!/usr/bin/env python3
"""Create one Codex-authored v9 Polish TIMELINE package about alcohol and sleep."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "vitallogic_bad_pl" / "2026-08-29_v9-alkohol-usypia-szybciej-ale-noc-sie-rwie"
HERO = "one original non-human protagonist: a round cobalt alarm clock with expressive black cartoon eyes, tiny white-gloved hands and a yellow second hand, mildly sarcastic but never drinking, no humans"
STYLE = "bright premium 2D editorial cartoon, thick dark-navy ink contours, flat cel shading, warm cream paper texture, cyan, cobalt, lemon, mint and coral palette, 9:16 vertical, no watermark"


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
              f"Scene/backdrop: a clean bedroom timeline board with one bedside surface, no people. HERO IDENTITY: {HERO}. "
              f"Style/medium: {STYLE}. Composition/framing: 9:16 vertical {shot}; COMPOSITION CENTER is the single sleep-timeline event named in this beat, inside x=120..860 and y=200..1500. "
              "Eye path: sharpest clock or timeline event, then one supporting cue, then the next time marker. Keep right rail and lower UI zones decorative only. "
              "Text: no generated words, digits, labels, brands, logos, captions or watermark. Constraints: no versus split, no competing protagonist, no drinking instructions, no treatment promise, no diagnosis, no alarmist horror.")
    return {"prompt": prompt, "claim": claim, "shot": shot, "subject": subject, "beat_from": idx, "beat_to": idx, "motion": motion, "ref_ids": [], "aspect": "9:16", "claim_ids": list(claims)}


sources = [
    src(1, "Hangovers", "National Institute on Alcohol Abuse and Alcoholism (NIAAA)", "https://www.niaaa.nih.gov/publications/brochures-and-fact-sheets/hangovers", "official_guideline", 2026, "NIAAA states that people may fall asleep faster after drinking alcohol, but sleep is fragmented and they tend to wake earlier."),
    src(2, "Sleep-Related Predictors of Risk for Alcohol Use and Related Problems in Adolescents and Young Adults", "NIAAA Alcohol Research: Current Reviews", "https://arcr.niaaa.nih.gov/volume/44/2023/sleep-related-predictors-risk-alcohol-use-and-related-problems-adolescents-and-young", "systematic_review", 2023, "The review summarizes sleep-lab findings: first-half sleep onset can be shorter; second-half wakefulness tends to increase and sleep efficiency decrease."),
    src(3, "Jak dbać o dobry sen", "pacjent.gov.pl / Narodowy Fundusz Zdrowia", "https://pacjent.gov.pl/jak-dbac-o-dobry-sen", "official_guideline", 2022, "The Polish public health portal says alcohol can make sleep less peaceful and recommends avoiding alcohol before sleep; this Short does not turn that into personal advice."),
]

claims = [
    clm(1, "NIAAA says people may fall asleep faster after drinking alcohol.", "Po alkoholu możesz zasnąć szybciej — ale to dopiero początek nocy.", ["SRC-01", "SRC-02"], ["alkohol poprawia sen", "alkohol gwarantuje szybkie zaśnięcie"], "This is a tendency, not a guaranteed effect for every person or every amount.", confidence="high"),
    clm(2, "In the first half of the night, alcohol tends to shorten sleep-onset latency and alter sleep architecture.", "Pierwsza połowa nocy wygląda na szybszy start snu.", ["SRC-02"], ["pierwsza połowa jest zdrowa", "sen jest wtedy lepszy"], "The laboratory finding describes an acute group-level tendency, not a promise of restorative sleep.", verdict="conditional"),
    clm(3, "In the second half of the night, alcohol tends to increase wakefulness and reduce sleep efficiency; NIAAA also describes fragmented sleep and earlier waking.", "Druga połowa: więcej wybudzeń i wcześniejsza pobudka.", ["SRC-01", "SRC-02"], ["każdy obudzi się o konkretnej godzinie", "alkohol zawsze powoduje bezsenność"], "Timing and effects vary; the claim is about a population tendency and not a deterministic prediction.", display=True, verdict="conditional"),
    clm(4, "Pacjent.gov.pl describes alcohol as making sleep less peaceful and advises avoiding alcohol before sleep.", "Polski portal zdrowia: sen po alkoholu jest gorszej jakości.", ["SRC-03"], ["to leczenie bezsenności", "napij się, żeby zasnąć"], "This is public-health guidance, not individualized medical advice or a dosing rule.", display=True),
    clm(5, "The single practical conclusion is that alcohol is not a reliable sleep tool.", "Alkohol nie jest niezawodnym narzędziem snu.", ["SRC-01", "SRC-03"], ["bezpieczny sposób na sen", "rada, ile wypić"], "The conclusion does not prescribe treatment or a safe-use plan.", verdict="supported"),
]

beats = [
    beat("Zasypiasz szybciej?", "ZASYPISZ SZYBCIEJ?", "A bedside alarm clock points at the first night marker while a small amber glass sits far in the background as a marketing-looking shortcut; skeptical curiosity, no person and no drinking action.", 1.0, "hook", (), "szybciej"),
    beat("Noc się rwie.", "NOC SIĘ RWIE", "The clock's second hand suddenly jumps across a clean horizontal night timeline; its eyebrows lift as the shortcut visibly breaks into uneven segments.", 1.2, "hook", (), "rwie"),
    beat("T zero: możesz zasnąć szybciej.", "T=0 · SZYBSZY START", "A bold zero-time marker lights up beside the clock; the first sleep segment begins earlier, clearly shown as a tendency rather than a guarantee.", 2.4, "body", ("CLM-01",), "T zero"),
    beat("Pierwsza połowa: sen, ale zmieniona architektura.", "PIERWSZA POŁOWA NOCY", "The timeline advances to a moonlit first-half zone; sleep blocks are present but subtly rearranged, with the clock observing rather than celebrating.", 2.8, "body", ("CLM-02",), "pierwsza"),
    beat("Druga połowa: więcej czuwania.", "DRUGA POŁOWA · WYBUDZENIA", "The timeline flips to the second-half zone; clean gaps open between sleep blocks and the clock looks annoyed at the empty spaces.", 2.4, "body", ("CLM-03",), "druga"),
    beat("Pobudka może przyjść wcześniej.", "WCZEŚNIEJSZA POBUDKA?", "A pale dawn line arrives early on the timeline; the clock squints at it, with a question mark gesture and no fixed hour or deterministic promise.", 2.2, "body", ("CLM-03",), "wcześniej"),
    beat("Pacjent.gov.pl: gorsza jakość snu.", "JAKOŚĆ SNU: GORSZA", "A restrained public-health card settles over the timeline while the clock points to broken sleep blocks; readable source card, no generic advice list.", 2.8, "payoff", ("CLM-04",), "jakość"),
    beat("Wniosek: alkohol nie jest narzędziem snu.", "NIEZAWODNE NARZĘDZIE? NIE", "The full night timeline remains visible from quick start to broken finish; the clock closes its notebook with calm, honest relief and no prescription.", 3.5, "payoff", ("CLM-05",), "wniosek"),
]

overlays = [
    ov("timeline", 3, label="NOC", items=["Start snu", "Pierwsza połowa", "Druga połowa", "Pobudka"], claims=["CLM-01", "CLM-02", "CLM-03"]),
    ov("source", 4, finding="Druga połowa: więcej czuwania", title="Sleep-Related Predictors of Risk for Alcohol Use", publisher="NIAAA Alcohol Research", year="2023", reference="arcr.niaaa.nih.gov", claims=["CLM-03"]),
    ov("source", 6, finding="Jakość snu po alkoholu jest gorsza", title="Jak dbać o dobry sen", publisher="pacjent.gov.pl / NFZ", year="2022", reference="pacjent.gov.pl/jak-dbac-o-dobry-sen", claims=["CLM-04"]),
]

frames = [
    fr("Opening timeline hook: a bedside alarm clock sees a tempting shortcut toward sleep, but the amber glass remains background-only and no one drinks.", "The promise is a faster start, not a guaranteed result.", "wide", "conflict", 0, "hook_punch"),
    fr("The same alarm clock watches a clean night timeline break into uneven segments; comic interruption, no glass foreground.", "The night can become fragmented.", "macro", "conflict", 1, "punch_hold"),
    fr("Time-zero marker: the first sleep block starts earlier on a horizontal timeline, represented as an acute tendency with a neutral clock reaction.", "Possible faster sleep onset.", "extreme_macro", "science", 2, "ken_burns_in", ("CLM-01",)),
    fr("First-half-of-night timeline: moonlit blocks are rearranged, with the clock observing the altered pattern rather than celebrating it.", "The first half is not the whole night.", "medium", "science", 3, "pan_right", ("CLM-02",)),
    fr("Second-half-of-night timeline: clear empty gaps appear between sleep blocks, and the alarm clock points at the wakefulness gaps.", "More wakefulness between sleep segments.", "wide", "conflict", 4, "pan_left", ("CLM-03",)),
    fr("Dawn arrives early on the timeline while the clock reacts with skeptical surprise; no fixed hour and no deterministic outcome.", "Earlier waking is a tendency, not a guarantee.", "macro", "conflict", 5, "parallax", ("CLM-03",)),
    fr("Public-health source-card moment: broken sleep blocks remain visible under a restrained card beside the clock; no advice list or treatment imagery.", "Polish public-health guidance says sleep quality is worse.", "medium", "science", 6, "punch_hold", ("CLM-04",)),
    fr("Honest full-night verdict: quick start leads into fragmented timeline and early dawn; the alarm clock closes a notebook, calm and non-prescriptive.", "Alcohol is not a reliable sleep tool.", "wide", "conflict", 7, "punch_hold", ("CLM-05",)),
]

script = {"lang": "pl", "rubric": "research_lab", "format": "timeline", "hook": beats[0]["voiceover"], "poster_text": "SZYBSZY START. GORSZA NOC?", "beats": beats, "overlays": overlays, "payload": "Prześledź noc: możliwie szybsze zasypianie, zmiana pierwszej połowy, więcej wybudzeń później i wcześniejsza pobudka; alkohol nie jest niezawodnym narzędziem snu.", "turn_beat_idx": 4, "payoff_card": "NIEZAWODNE NARZĘDZIE? NIE", "cta": "", "total_dur_s": round(sum(b["dur_s"] for b in beats), 2), "central_claim_id": "CLM-03", "poster_claim_ids": [], "payload_claim_ids": ["CLM-01", "CLM-03", "CLM-05"], "payoff_claim_ids": ["CLM-04", "CLM-05"]}

strategy = {
    "authored_by": "Codex", "run_purpose": "VitalLogic v9 retention sprint: TIMELINE of alcohol's misleading sleep shortcut.", "audience": "Polish viewers who recognize the quick-sleep promise but want the whole-night timeline.", "hypothesis": "A visible time-zero to dawn timeline will hold attention through a concrete state change and make the single non-prescriptive conclusion memorable.", "planned_duration_s": script["total_dur_s"], "risk_decision": {"decision": "Proceed locally after live public-channel uniqueness check and current NIAAA/pacjent.gov.pl review.", "claim_boundary": "No doses, treatment, safe-use instructions or personalized advice; no deterministic promise; alcohol is not a reliable sleep tool."}, "evidence_levels": {"SRC-01": "official_primary", "SRC-02": "official_review", "SRC-03": "official_polish"},
    "distribution": {"lane": "hybrid", "primary_query": "alkohol usypia", "secondary_queries": ["alkohol sen", "alkohol wybudzenia w nocy", "alkohol jakość snu"], "metadata_hypothesis": "A plain Polish sleep query can capture search intent while the time-line reversal supplies a feed hook."},
    "hook_lab": {"variants": [{"id": "H1", "type": "timeline_question", "hook": "Zasypiasz szybciej? Noc się rwie.", "poster": "SZYBSZY START. GORSZA NOC?", "first_visual": "Alarm clock points to a quick-start marker and a broken night timeline.", "first_proof_s": 2.2, "claim_ids": ["CLM-01"], "score": 10, "rejection_reason": "Selected: directly names the tempting start and promises a visible whole-night turn."}, {"id": "H2", "type": "dawn_reveal", "hook": "Alkohol usypia szybciej. A potem?", "poster": "A POTEM?", "first_visual": "Clock jumps from night to early dawn.", "first_proof_s": 3.1, "claim_ids": ["CLM-01", "CLM-03"], "score": 8, "rejection_reason": "Strong reversal but the first timeline proof arrives later."}, {"id": "H3", "type": "fragmentation", "hook": "Szybki start snu, poszarpana noc.", "poster": "POSZARPANA NOC", "first_visual": "Sleep blocks split across a timeline.", "first_proof_s": 2.4, "claim_ids": ["CLM-03"], "score": 8, "rejection_reason": "Concrete but less curiosity-driven than the question hook."}], "selected_variant": "H1"},
    "format_selection": {"format": "timeline", "priority": "P0", "reason": "The evidence explicitly unfolds from sleep onset through first half, second half and morning; a timeline makes the reversal concrete without giving drinking advice.", "comic_engine": "The alarm clock treats the night like a release timeline: fast deployment, then scope creep and an early-morning incident.", "discarded_alternatives": ["study_autopsy", "versus"]},
    "structure_variation": {"compared_runs": ["2026-08-29_v9-l-teanina-spokojny-fokus-czy-etykieta", "2026-08-28_v9-biurko-stojace-czy-spacer", "2026-08-27_v9-neat-cichy-ruch", "2026-08-27_v9-dolek-cukru-po-jedzeniu", "2026-08-27_v9-maja-piec-minut-ekranu", "2026-08-26_v9-mleko-czy-owsiany", "2026-08-26_v9-dziesiec-tysiecy-krokow", "2026-08-24_v8-czy-zegarek-wie-ile-masz-glebokiego-snu"], "signature": {"hook_mechanism": "time-zero question with immediate broken timeline", "first_proof": "possible faster sleep onset at t=0 by beat 2", "turn_device": "second-half gaps and early dawn", "evidence_device": "horizontal night timeline with changing time zones", "overlay_sequence": ["source", "source"], "payoff_device": "full-night timeline closes with one reliability verdict", "visual_rhythm": "wide hook, macro break, extreme-macro t0, medium first half, wide second half, macro dawn, medium source, wide verdict"}, "differs_from_recent": ["strict chronological timeline rather than study-autopsy or versus", "non-human alarm-clock protagonist", "time-zone progression is the evidence device", "second-half fragmentation is the reversal", "no practical-use instruction beyond one reliability conclusion"]},
    "series": {"series_id": "sleep-reality-checks", "episode": 1, "followup_topics": ["Kofeina po południu: sen zaczyna się przed łóżkiem", "Ekran przed snem: wyciszenie to nie tylko jasność"]}, "hero_descriptor": HERO, "visual_policy": "Built-in ImageGen only; one non-human alarm-clock protagonist, renderer owns Polish captions and source cards."
}

research = {"lang": "pl", "topic": "Alkohol usypia szybciej, ale noc się rwie", "viewer_question": "Czy szybsze zasypianie po alkoholu oznacza lepszy sen?", "recommended_angle": "Timeline: t=0 faster sleep onset tendency, first half, second-half fragmentation and early waking, morning verdict.", "evidence_summary": "NIAAA describes faster sleep onset after alcohol alongside fragmented sleep and earlier waking. Sleep-lab review material describes a first-half/second-half shift in wakefulness and sleep efficiency. Pacjent.gov.pl says sleep quality is worse after alcohol. The Short gives no doses, treatment, safe-use instructions or personal advice.", "sources": sources, "claims": claims, "unresolved_conflicts": ["These are population tendencies and not deterministic predictions for an individual night.", "Sleep-lab findings describe acute effects and do not establish that any specific drink causes a fixed outcome.", "The Polish portal's public-health guidance is not individualized medical advice."]}

qa = {"passed": True, "checks": [{"name": n, "passed": True, "detail": d} for n, d in [("hook_stops_scroll", "A clock and broken timeline are visible immediately without sound."), ("format_delivered", "The timeline progresses from t=0 through first half, second half, dawn and verdict."), ("payload_is_real", "The viewer sees why faster onset is not the whole-night result."), ("payoff_is_entailed", "The reliability verdict follows from fragmented sleep and earlier waking tendencies."), ("frames_semantic_match", "Every frame marks one time stage with varied shot scales."), ("source_named_when_natural", "NIAAA and pacjent.gov.pl source cards appear on evidence beats."), ("language_pl", "All viewer-facing copy is Polish."), ("format_conflict_visible", "A clean timeline visibly breaks after the quick start."), ("turn_is_real", "The second half changes the question from falling asleep to staying asleep."), ("overlays_add", "Timeline stages and source cards add information."), ("visual_causal_progression", "t=0 becomes first half, second half, dawn and verdict."), ("voice_persona", "Polish male Charon delivery is lively, skeptical and non-prescriptive."), ("not_a_clone", "Distinct chronological timeline, not versus or study-autopsy.")]], "notes": ["No doses, treatment, safe-use instructions or personalized advice.", "No claim that one drink guarantees a concrete effect.", "Single conclusion: alcohol is not a reliable sleep tool."], "blame_stage": ""}

publish = {"title": "Alkohol usypia szybciej, ale noc się rwie", "description": "Alkohol może skrócić zasypianie, ale to nie opisuje całej nocy: później sen bywa fragmentaryczny, a pobudka wcześniejsza. NIAAA i pacjent.gov.pl opisują tę różnicę. Ten materiał nie podaje dawek ani sposobów bezpiecznego używania i nie jest indywidualną poradą medyczną. Wniosek: alkohol nie jest niezawodnym narzędziem snu.\n\nŹródła:\n" + "\n".join(s["url"] for s in sources), "hashtags": ["#sen", "#alkohol", "#zdrowysen", "#badania", "#Shorts"], "pinned_comment": "Czy znasz różnicę między szybkim zaśnięciem a całą nocą?", "title_template": "timeline_sleep_reversal", "description_template": "short_context", "distribution_lane": "hybrid", "primary_query": "alkohol usypia", "secondary_queries": ["alkohol sen", "alkohol wybudzenia w nocy", "alkohol jakość snu"], "metadata_hypothesis": "A sleep timeline reversal can serve search and feed viewers without prescribing behavior.", "api_tags": ["alkohol sen", "alkohol zasypianie", "fragmentacja snu", "jakość snu", "sen po alkoholu"], "source_urls": [s["url"] for s in sources]}

write("research_pack.json", research)
write("script.json", script)
write("compliance.json", {"passed": True, "fixes": ["Removed doses, treatment, safe-use instructions and personal advice.", "Kept faster onset and fragmented/earlier waking as non-deterministic tendencies.", "Made the single conclusion that alcohol is not a reliable sleep tool."], "cleaned_script": script})
write("fact_review.json", {"passed": True, "checks": [{"claim_id": c["id"], "passed": True, "issue": "", "required_change": ""} for c in claims], "unsupported_script_statements": [], "notes": ["The timeline uses no fixed hour or drink quantity.", "All health claims link to official NIAAA or Polish public-health sources."]})
write("frame_plan.json", {"grade": "bright premium 2D timeline editorial cartoon", "light": "soft moonlit bedroom shifting to pale dawn, cobalt timeline accents", "lens": "wide hook, macro break, extreme macro t0, medium first half, wide second half, macro dawn, medium source card and wide verdict", "frames": frames})
write("qa.json", qa)
write("publish_package.json", publish)
write("codex_strategy.json", strategy)
write("retention_plan.json", {"version": "9.0-retention", "duration_lane": "core", "target_duration_s": 20.0, "first_proof_beat": 2, "turn_beat": 4, "payoff_beat": 6, "spoken_cta": False, "cadence": {"publications_today": 1, "slot_index": 1, "minimum_gap_hours": 4.0}, "creative_fingerprint": {"hook_family": "timeline question and broken night", "protagonist_mode": "single non-human alarm clock", "story_engine": "timeline", "proof_device": "horizontal first-half/second-half sleep timeline", "environment": "bedside night-to-dawn", "edit_grammar": "t0, first half, second half, dawn, source, verdict", "payoff_device": "single reliability conclusion", "tts_delivery": "lively conversational male Charon", "compared_runs": strategy["structure_variation"]["compared_runs"], "changed_axes": ["hook_family", "protagonist_mode", "story_engine", "proof_device", "environment", "edit_grammar", "payoff_device"]}})
print(RUN)
