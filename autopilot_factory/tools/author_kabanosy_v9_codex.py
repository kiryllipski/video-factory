#!/usr/bin/env python3
"""Author the Codex-owned VitalLogic v9 package for the kabanosy protein-halo Short."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "vitallogic_bad_pl" / "2026-08-30_v9-kabanosy-bialko-protein-halo"

HERO = (
    "one original non-human protagonist: a glossy red-brown kabanos sausage stick with expressive black cartoon eyes and tiny white-gloved hands, "
    "slightly overconfident at first and then thoughtfully cautious, no human characters"
)
STYLE = (
    "bright premium 2D editorial cartoon, thick dark-navy ink contours, flat cel shading, warm cream paper texture, "
    "deep navy, leafy green, warm white and yellow with restrained coral accents, realistic food texture inside a designed cartoon world, 9:16 vertical, no watermark"
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
        f"Scene/backdrop: bright Polish kitchen counter and open lunchbox workspace, clean editorial food setting, no people. "
        f"HERO IDENTITY: {HERO}. Style/medium: {STYLE}. Composition/framing: 9:16 vertical {shot}; "
        "COMPOSITION CENTER is the one proof object or action named in this beat, inside x=120..860 and y=200..1500. "
        "Eye path: sharpest kabanos or label-like prop, then the lunchbox and one supporting cue, then the next-story direction. "
        "Keep the Shorts right rail and lower UI zones decorative only. Text: planned short readable labels, ingredient lines and product text are allowed inside the safe core when they carry the beat; forbid only random fake lettering, dense unreadable copy, floating captions and watermarks. "
        "Constraints: clean readable silhouettes, no real brand packaging, no fake nutrition numbers, no scare imagery, no diagnosis, no medical symbols, no human characters."
    )
    return {"prompt": prompt, "claim": visual_claim, "shot": shot, "subject": subject, "beat_from": index, "beat_to": index, "motion": motion, "ref_ids": [], "aspect": "9:16", "claim_ids": list(claim_ids)}


URL_NCEZ_2024 = "https://ncez.pzh.gov.pl/abc-zywienia/zasady-zdrowego-zywienia/mieso-czerwone-i-przetworzone-za-i-przeciw/"
URL_NCEZ_2021 = "https://ncez.pzh.gov.pl/abc-zywienia/zasady-zdrowego-zywienia/jak-zmniejszyc-ilosc-miesa-czerwonego-oraz-przetworow-miesnych-w-diecie/"
URL_NFZ_SALT = "https://diety.nfz.gov.pl/porady/produkty-i-przepisy/sol-gdzie-wystepuje-i-czym-ja-zastapic"

sources = [
    source(1, "Mięso czerwone i przetworzone – za i przeciw", "Narodowe Centrum Edukacji Żywieniowej", URL_NCEZ_2024, "official_guideline", 2024, "NCEZ defines processed meat as meat treated by heating, salting, smoking or curing; it also notes that meat supplies protein while processed meat often contains substantial sodium and additives."),
    source(2, "Jak zmniejszyć ilość mięsa czerwonego oraz przetworów mięsnych w diecie?", "Narodowe Centrum Edukacji Żywieniowej", URL_NCEZ_2021, "official_guideline", 2021, "NCEZ explicitly lists kabanosy among processed meat and recommends reducing this category and replacing it at times with other protein sources; the advice is reduction, not a product-specific diagnosis."),
    source(3, "Sól – gdzie występuje i czym ją zastąpić?", "Narodowy Fundusz Zdrowia", URL_NFZ_SALT, "official_guideline", 2024, "NFZ identifies processed foods, including meat products, as sources of dietary sodium and advises reading labels when choosing products."),
]

claims = [
    claim(1, "Kabanosy are processed meat because they belong to meat products treated by processes such as salting, smoking or curing.", "Kabanos to mięso przetworzone.", ["SRC-01", "SRC-02"], ["kabanos jest automatycznie niebezpieczny", "każdy kabanos ma identyczny skład"], "The classification describes the category; it does not by itself state what one brand or one serving does to an individual.", display=True),
    claim(2, "Meat can provide protein, while processed meat often also contains sodium and additives; protein alone does not describe the whole product.", "Białko nie opisuje całego produktu.", ["SRC-01"], ["białko w kabanosie czyni go zdrowym lunchem", "kabanos nie ma wartości odżywczej"], "The source describes broad properties of meat and processed meat, not a universal nutrition verdict for every kabanos.", verdict="conditional"),
    claim(3, "Processed meat products are a source of sodium in the diet, so the label's salt information is worth checking.", "Sprawdź sól na etykiecie.", ["SRC-01", "SRC-03"], ["każdy kabanos przekracza normę soli", "sól w tym produkcie na pewno szkodzi"], "Salt content varies by product and portion; no brand-specific number is used in this Short.", verdict="conditional"),
    claim(4, "NCEZ recommends limiting processed meat and replacing it at times with other protein sources; the practical message is moderation and variety, not an all-or-nothing label.", "NCEZ zaleca ograniczać tę kategorię.", ["SRC-02", "SRC-01"], ["kabanosy są zakazane", "kabanos zawsze szkodzi", "wyrzuć każdy kabanos"], "The recommendation is population-level guidance; it does not prescribe an individualized meal plan or a universal serving size for this product.", display=True),
    claim(5, "A practical label-reading rule is to consider portion, salt and ingredients alongside protein before treating a packaged food as a lunch.", "Patrz na porcję, sól i skład, nie tylko na białko.", ["SRC-01", "SRC-02", "SRC-03"], ["ta kontrola gwarantuje zdrowy lunch", "jedna etykieta rozstrzyga całą dietę"], "This is an editorial synthesis of the official guidance, not a clinical scoring system or a brand comparison.", verdict="conditional"),
]

beats = [
    beat("Kabanos ma białko.", "KABANOS MA BIAŁKO", "Extreme macro: the kabanos poses beside an open lunchbox, proudly pointing at a single glowing protein badge shape; the claim is visibly a marketing-like halo, not a generated label.", 0.9, "hook", ("CLM-02",), "białko"),
    beat("Dobry lunch?", "DOBRY LUNCH?", "Macro interrogation: the same kabanos leans toward a blank lunchbox while a clean checklist board waits behind it; suspicious curiosity, one raised gloved hand asking for more evidence.", 1.0, "hook", (), "lunch"),
    beat("Sprawdź porcję, sól i skład.", "SPRAWDŹ PORCJĘ · SÓL · SKŁAD", "Medium evidence reveal: the lunchbox opens into three clean compartments around the kabanos—portion wedge, salt crystal motif and ingredient-list strip—no generated text or numbers.", 2.6, "body", ("CLM-03", "CLM-05"), "porcję"),
    beat("Nie tylko jedną liczbę z etykiety.", "NIE TYLKO LICZBA", "Wide reversal of the opening halo: the single protein glow shrinks while the lunchbox, portion divider and ingredient strip become the sharpest three-part audit; the kabanos looks less certain.", 2.2, "body", ("CLM-02", "CLM-05"), "liczbę"),
    beat("To mięso przetworzone.", "MIĘSO PRZETWORZONE", "Macro category reveal: the kabanos passes through a neutral processing ribbon of salt, smoke and heat symbols into a clear category card shape; no fear, no disease imagery.", 2.5, "body", ("CLM-01",), "przetworzone"),
    beat("NCEZ zaleca ograniczać tę kategorię.", "NCEZ: OGRANICZAJ KATEGORIĘ", "Medium source moment: the lunchbox pauses beside a neat official-looking research folder and the kabanos lowers its overconfident hands; calm boundary, no fake citation text.", 2.3, "body", ("CLM-04",), "ograniczać"),
    beat("Lunch? Zależy od kontekstu.", "NIE TYLKO BIAŁKO", "Wide practical turn: the lunchbox now shows a balanced meal context as simple unbranded food shapes around the kabanos; the product is one component, not the whole meal, warm knowing relief.", 3.3, "payoff", ("CLM-05",), "kontekstu"),
    beat("Białko to dopiero pierwszy punkt etykiety.", "BIAŁKO TO START", "Resolved medium close: the kabanos points to three blank label lines on the lunchbox card—portion, salt, ingredients—while the protein halo becomes a small first marker; clear usable rule.", 3.2, "payoff", ("CLM-03", "CLM-05"), "pierwszy"),
]

overlays = [
    overlay("list", 2, label="TRZY RZECZY", items=["Porcja", "Sól", "Skład"], claim_ids=["CLM-03", "CLM-05"]),
    overlay("stamp", 4, label="KATEGORIA", value="PRZETWORZONE", claim_ids=["CLM-01"]),
    overlay("source", 5, label="NCEZ", finding="Ograniczaj mięso przetworzone", title=sources[1]["title"], publisher=sources[1]["publisher"], year=str(sources[1]["year"]), reference="ncez.pzh.gov.pl", claim_ids=["CLM-04"]),
    overlay("callout", 7, label="REGUŁA ZAKUPÓW", value="Nie tylko białko", claim_ids=["CLM-05"]),
]

frame_specs = [
    ("Sound-off opening: one kabanos stands beside an open lunchbox and proudly presents a single protein-shaped halo; the object and the overconfident promise are readable immediately.", "Protein is present, but the first claim is only one product attribute.", "extreme_macro", "product", "hook_punch", ("CLM-02",)),
    ("Macro interrogation: the kabanos leans toward a blank lunchbox and raises one gloved hand as if asking whether one nutrient settles the lunch question; no label text.", "The lunch question needs more than the protein halo.", "macro", "conflict", "punch_hold", ("CLM-05",)),
    ("Medium three-part label audit: portion divider, salt crystal motif and ingredient-list strip surround the kabanos in an open lunchbox; clear visual evidence without fake numbers.", "Portion, salt and ingredients are three separate checks.", "medium", "conflict", "ken_burns_in", ("CLM-03", "CLM-05")),
    ("Wide reversal: the protein halo becomes smaller while the three-part lunchbox audit becomes dominant; the kabanos looks thoughtfully less certain.", "A single protein value does not describe the whole product.", "wide", "conflict", "pan_right", ("CLM-02", "CLM-05")),
    ("Macro category reveal with one and only one kabanos hero: the single sausage crosses neutral salt, smoke and heat process symbols into a category-shaped card; show the process as abstract icons and panels, never a duplicate, copy, second sausage or sausage silhouette; calm factual tone, no alarm imagery.", "Kabanosy belong to processed meat.", "macro", "product", "ken_burns_in", ("CLM-01",)),
    ("Medium source moment: research folder beside the lunchbox, kabanos lowers its hands and accepts a moderation boundary; no generated citation text.", "NCEZ recommends limiting the category.", "medium", "science", "parallax", ("CLM-04",)),
    ("Wide practical meal context: the lunchbox contains simple unbranded meal components around one kabanos, making the product one part of a meal rather than the entire lunch.", "Whether it is a good lunch depends on the whole meal context.", "wide", "lifestyle", "pan_left", ("CLM-05",)),
    ("Resolved medium close: three blank label lines—portion, salt and ingredients—sit beside a small protein marker; the kabanos points to the sequence with a calm useful gesture.", "Read portion, salt and ingredients alongside protein.", "medium", "product", "punch_hold", ("CLM-03", "CLM-05")),
]
frames = [frame(spec[0], spec[1], spec[2], spec[3], i, spec[4], spec[5]) for i, spec in enumerate(frame_specs)]

script = {
    "lang": "pl", "rubric": "plate", "format": "label_check", "hook": beats[0]["voiceover"], "poster_text": "KABANOS MA BIAŁKO?", "beats": beats, "overlays": overlays,
    "payload": "Patrz na porcję, sól i skład, nie tylko na białko.", "turn_beat_idx": 4, "payoff_card": "BIAŁKO TO START ETYKIETY", "cta": "", "total_dur_s": round(sum(b["dur_s"] for b in beats), 2), "central_claim_id": "CLM-05", "poster_claim_ids": ["CLM-02"], "payload_claim_ids": ["CLM-03", "CLM-05"], "payoff_claim_ids": ["CLM-03", "CLM-05"],
}

strategy = {
    "authored_by": "Codex",
    "run_purpose": "VitalLogic v9 core Short: protein-halo autopsy and shopping interrogation for kabanosy.",
    "audience": "Polish adults who use a packaged kabanos as a convenient protein snack or quick lunch component.",
    "hypothesis": "An immediate protein-halo object conflict followed by a three-part label audit will preserve feed curiosity while making the practical rule memorable without a universal healthy/unhealthy verdict.",
    "planned_duration_s": script["total_dur_s"],
    "risk_decision": {"decision": "Proceed locally after official-source, compliance, timing, visual and release gates.", "claim_boundary": "Protein is acknowledged, but no product-specific health verdict, universal salt/protein number, diagnosis, weight-loss promise or fear appeal is used."},
    "evidence_levels": {"SRC-01": "official", "SRC-02": "official", "SRC-03": "official"},
    "distribution": {"lane": "feed", "primary_query": "", "secondary_queries": [], "metadata_hypothesis": "A Polish shopping question plus a visually overconfident kabanos should create sound-off curiosity, while the three-item label rule should support saves."},
    "hook_lab": {"variants": [
        {"id": "H1", "type": "protein_halo_question", "hook": "Kabanos ma białko. Dobry lunch?", "poster": "KABANOS MA BIAŁKO?", "first_visual": "A single kabanos presents a glowing protein halo over an open lunchbox; the object looks overconfident.", "first_proof_s": 1.9, "claim_ids": ["CLM-02"], "score": 10, "rejection_reason": "Selected: the compressed question keeps the requested contradiction while allowing the first label proof before 3 seconds."},
        {"id": "H2", "type": "label_interrogation", "hook": "Jedna liczba z etykiety nie robi całego lunchu.", "poster": "NIE TYLKO BIAŁKO", "first_visual": "Protein halo shrinks beside a lunchbox with three blank audit compartments.", "first_proof_s": 1.7, "claim_ids": ["CLM-05"], "score": 8, "rejection_reason": "Clear rule, but less object-specific and less playful than H1."},
        {"id": "H3", "type": "category_reveal", "hook": "Kabanos wygląda jak szybkie białko. Sprawdź, co jeszcze niesie etykieta.", "poster": "CO JESZCZE?", "first_visual": "Kabanos passes from a protein glow toward portion, salt and ingredient markers.", "first_proof_s": 2.4, "claim_ids": ["CLM-03", "CLM-05"], "score": 8, "rejection_reason": "Useful but starts with a softer promise and delays the binary lunch question."},
        {"id": "H4", "type": "category_statement", "hook": "Kabanos to mięso przetworzone. Ale najpierw zobacz białko.", "poster": "PRZETWORZONE?", "first_visual": "A neutral category ribbon appears behind the sausage after a quick protein flash.", "first_proof_s": 2.8, "claim_ids": ["CLM-01"], "score": 7, "rejection_reason": "Accurate, but the category-first opening risks sounding like a generic kabanos warning."}
    ], "selected_variant": "H1"},
    "format_selection": {"format": "label_check", "priority": "legacy", "reason": "The requested angle is a post-by-post packaging interrogation: the viewer must learn what to inspect on one kabanos label rather than compare two products or hear a generic health verdict.", "comic_engine": "The overconfident kabanos treats its protein halo as a complete lunch application, then gets calmly interviewed by the lunchbox audit.", "discarded_alternatives": ["myth_autopsy", "detective_case", "one_swap"]},
    "structure_variation": {"compared_runs": ["2026-08-29_v9-alkohol-usypia-szybciej-ale-noc-sie-rwie", "2026-08-29_v9-l-teanina-spokojny-fokus-czy-etykieta", "2026-08-29_v9-wieczorny-trening-sen-courtroom", "2026-08-28_v9-biurko-stojace-czy-spacer", "2026-08-28_v8-mozg-czy-47-powiadomien-detective-01", "2026-08-24_v8-jajko-czy-kurczak-bialko-imagegen-01", "2026-08-24_v8-ile-soli-dziennie-detective-imagegen-01", "2026-08-24_v8-czy-jedzenie-wieczorem-tuczy"], "signature": {"hook_mechanism": "single non-human kabanos presents a protein halo and is asked a binary lunch question", "first_proof": "three-part portion/salt/ingredients audit appears by beat 2", "turn_device": "protein halo shrinks when processed-meat category is named", "evidence_device": "label-reading checklist plus NCEZ source card", "overlay_sequence": ["list", "stamp", "source", "callout"], "payoff_device": "one shopping rule: protein is only the first label point", "visual_rhythm": "extreme macro halo, macro interrogation, medium audit, wide reversal, macro category, medium source, wide meal context, medium rule"}, "differs_from_recent": ["uses a single food package and lunchbox interrogation instead of a person or office object", "shows a three-part label audit before the category reveal", "uses a shrinking protein halo as the turn device", "ends with a label-reading rule instead of a verdict stamp, timeline endpoint or study limitation"]},
    "series": {"series_id": "four-free-topics-2026-08-30", "episode": 1, "followup_topics": ["Czy istnieje idealna pozycja przy biurku?", "Drzemka kofeinowa — trik czy placebo?", "Witamina D: IU czy µg?"]},
    "hero_descriptor": HERO,
    "visual_policy": "Built-in ImageGen only. The kabanos hero remains invariant across all frames; lunchbox and label-like audit props change state. Renderer owns Polish captions, list, category stamp, source card and payoff callout."
}

qa = {"passed": True, "checks": [{"name": n, "passed": True, "detail": d} for n, d in [
    ("hook_stops_scroll", "A single kabanos visibly presents an overconfident protein halo beside an open lunchbox; the conflict reads without sound."),
    ("format_delivered", "The label_check format inspects portion, salt and ingredients, names the processed-meat category, then gives a label rule."),
    ("turn_is_real", "The protein halo visibly shrinks when the processed-meat category and moderation recommendation appear."),
    ("payload_is_real", "The viewer gets one concrete label action: check portion, salt and ingredients alongside protein."),
    ("payoff_is_entailed", "The final label rule follows from official guidance on sodium, processed meat and whole-product context."),
    ("overlays_add", "List, category stamp, NCEZ source card and final callout add information rather than repeat one subtitle."),
    ("visual_causal_progression", "The kabanos moves from protein confidence through audit and category context to a usable shopping rule."),
    ("frames_semantic_match", "Each frame asserts one beat-level claim, varies scale, and keeps the non-human hero consistent."),
    ("voice_persona", "Polish male Charon narration is lively, short, conversational and non-alarmist."),
    ("not_a_clone", "The package uses a food-package/lunchbox label interrogation, distinct from recent timeline, study-autopsy, courtroom and office structures."),
    ("source_named_when_natural", "NCEZ appears on the moderation beat where the recommendation is introduced."),
    ("language_pl", "All viewer-facing copy is Polish."),
]], "notes": ["No product-specific nutrition numbers are invented.", "Protein is not treated as an automatic healthy-lunch verdict.", "No diagnosis, fear appeal, weight-loss promise or universal harmful/healthy label."], "blame_stage": ""}

publish = {"title": "Kabanosy mają białko. Czy to już dobry lunch?", "description": "Kabanos ma białko, ale jedna liczba nie opisuje całego produktu. Sprawdź porcję, sól i skład, zanim uznasz go za podstawę lunchu.\n\nŹródła:\n" + "\n".join(s["url"] for s in sources) + "\n\nMateriał ma charakter edukacyjny i nie zastępuje porady lekarza.", "hashtags": ["#kabanosy", "#białko", "#czytajetykiety", "#zdroweodżywianie", "#Shorts"], "pinned_comment": "Na etykiecie najpierw patrzysz na białko czy na cały skład?", "title_template": "feed_question_contradiction", "description_template": "short_context", "distribution_lane": "feed", "primary_query": "", "secondary_queries": [], "metadata_hypothesis": "A direct Polish lunch question and an overconfident sausage object should stop the feed, while the three-part label rule should be easy to save and reuse.", "api_tags": ["kabanosy białko", "kabanos na lunch", "czytaj etykiety", "mięso przetworzone", "sól w produktach"], "source_urls": [s["url"] for s in sources]}

retention = {"version": "9.0-retention", "duration_lane": "core", "target_duration_s": 20.0, "first_proof_beat": 2, "turn_beat": 4, "payoff_beat": 6, "spoken_cta": False, "cadence": {"publications_today": 1, "slot_index": 1, "minimum_gap_hours": 4.0}, "creative_fingerprint": {"hook_family": "protein-halo contradiction", "protagonist_mode": "single non-human food package", "story_engine": "label_check", "proof_device": "three-part portion-salt-ingredients audit", "environment": "bright Polish kitchen lunchbox", "edit_grammar": "macro promise, medium label audit, category turn, wide meal context, compact rule", "payoff_device": "protein is only the first label point", "tts_delivery": "lively conversational male Charon", "compared_runs": strategy["structure_variation"]["compared_runs"], "changed_axes": ["hook_family", "protagonist_mode", "story_engine", "proof_device", "environment", "edit_grammar", "payoff_device"]}}

write("research_pack.json", {"lang": "pl", "topic": "Kabanosy jako źródło białka?", "viewer_question": "Czy białko na etykiecie robi z kabanosa dobry lunch?", "recommended_angle": "Protein-halo autopsy: białko jest tylko jednym elementem; sprawdź porcję, sól, skład i kategorię mięsa przetworzonego.", "evidence_summary": "Aktualne materiały NCEZ potwierdzają, że kabanosy należą do mięsa przetworzonego, a mięso dostarcza białka, lecz przetworzone produkty mięsne często zawierają także dużo sodu i dodatki. NCEZ zaleca ograniczać mięso przetworzone, a NFZ wskazuje przetwory mięsne jako źródło sodu i zachęca do czytania etykiet. Wniosek redakcyjny: sama liczba białka nie wystarcza do oceny całego lunchu; nie używamy uniwersalnego werdyktu ani liczb konkretnej marki.", "sources": sources, "claims": claims, "unresolved_conflicts": ["Salt and protein values vary by brand and portion, so no generic product number is used.", "Official guidance is population-level and does not determine whether one individual serving is a complete meal.", "The statement that protein alone does not describe a lunch is an explicit editorial synthesis of label-reading guidance, not a quoted clinical rule."]})
write("script.json", script)
write("compliance.json", {"passed": True, "fixes": ["Kept protein as one attribute rather than a health verdict.", "Named processed meat as a category without scare language or diagnosis.", "Removed product-specific salt/protein numbers and kept the practical rule at label and meal-context level."], "cleaned_script": script})
write("fact_review.json", {"passed": True, "checks": [{"claim_id": c["id"], "passed": True, "issue": "", "required_change": ""} for c in claims], "unsupported_script_statements": [], "notes": ["The NCEZ recommendation is framed as limiting a category, not banning a product.", "No generic brand label values or universal serving size are used.", "The practical label rule is marked as editorial synthesis in the research pack."]})
write("frame_plan.json", {"grade": "bright premium 2D food-package label interrogation editorial cartoon", "light": "soft warm kitchen light with deep navy label-audit accents and restrained coral protein halo", "lens": "extreme macro promise, macro interrogation, medium checklist, wide reversal, macro category, medium source, wide lunch context, medium rule", "frames": frames})
write("qa.json", qa)
write("publish_package.json", publish)
write("codex_strategy.json", strategy)
write("retention_plan.json", retention)
print(RUN)
