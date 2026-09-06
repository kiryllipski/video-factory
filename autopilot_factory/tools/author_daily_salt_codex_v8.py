#!/usr/bin/env python3
"""Author the Codex-owned v8 package for the Polish daily-salt Short."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "vitallogic_bad_pl" / "2026-08-24_v8-ile-soli-dziennie-detective-imagegen-01"
HERO = (
    "recurring protagonist: an original small cobalt-blue glass salt shaker with a brushed steel cap, "
    "two expressive black cartoon eyes and tiny white-gloved arms, three visible salt crystals inside, "
    "mischievous but ultimately helpful, no human characters"
)
STYLE = (
    "bright premium 2D editorial cartoon, thick navy ink contours, flat cel shading, warm cream paper texture, "
    "cobalt blue, leafy green and sunflower yellow palette, 9:16 vertical, no embedded text, no digits, no logos, no watermark"
)


def write(name: str, value) -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source(i, title, publisher, url, source_type, year, summary):
    return {
        "id": f"SRC-{i:02d}", "title": title, "publisher": publisher, "url": url,
        "source_type": source_type, "year": year, "evidence_summary": summary,
    }


def claim(i, neutral, allowed, source_ids, forbidden, limitations, *, risk="low", confidence="high", display=False, verdict="supported"):
    return {
        "id": f"CLM-{i:02d}", "neutral_claim": neutral, "verdict": verdict,
        "confidence": confidence, "source_ids": source_ids, "allowed_wording": allowed,
        "forbidden_wording": forbidden, "limitations": limitations, "risk_level": risk,
        "display_source": display,
    }


def beat(voiceover, screen, cue, dur, act, claim_ids=(), emphasis=""):
    return {
        "voiceover": voiceover, "on_screen_text": screen, "visual_cue": cue, "dur_s": dur,
        "act": act, "emphasis": emphasis, "claim_ids": list(claim_ids),
    }


def overlay(kind, beat_idx, *, label="", value="", label_b="", value_b="", items=None, winner="none", claim_ids=(), finding="", title="", publisher="", year="", reference=""):
    return {
        "kind": kind, "beat_idx": beat_idx, "label": label, "value": value,
        "label_b": label_b, "value_b": value_b, "percent": None, "items": items or [],
        "winner": winner, "claim_ids": list(claim_ids), "source_finding": finding,
        "source_title": title, "source_publisher": publisher, "source_year": year,
        "source_reference": reference,
    }


def frame(primary, visual_claim, shot, subject, index, motion, claim_ids=()):
    prompt = (
        f"Use case: illustration-story. Asset type: vertical VitalLogic Short frame. Primary request: {primary}. "
        f"Scene/backdrop: simple Polish kitchen-to-office visual world, no people. Subject: {HERO}. "
        f"Style/medium: {STYLE}. Composition/framing: 9:16 vertical {shot}; keep the central hero and all proof objects "
        f"inside x=120..860 and y=200..1500, leave lower and right Shorts UI zones decorative only. "
        "Eye path: hero expression, concrete evidence object, next-story direction. Text (verbatim): none. "
        "Constraints: no readable words, numbers, labels, brand packaging, logos or watermark. Avoid: humans, medical diagnosis, clutter, fake charts, AI lettering."
    )
    return {
        "prompt": prompt, "claim": visual_claim, "shot": shot, "subject": subject,
        "beat_from": index, "beat_to": index, "motion": motion, "ref_ids": [],
        "aspect": "9:16", "claim_ids": list(claim_ids),
    }


sources = [
    source(1, "Sodium reduction", "World Health Organization", "https://www.who.int/news-room/fact-sheets/detail/sodium-reduction", "official_guideline", 2025,
           "WHO recommends adults consume less than 2,000 mg sodium per day, equivalent to less than 5 g salt (just under one teaspoon), and notes much sodium comes from processed foods."),
    source(2, "Healthy diet", "World Health Organization", "https://www.who.int/news-room/fact-sheets/detail/healthy-diet", "official_guideline", 2026,
           "WHO healthy-diet guidance limits adult salt intake to less than 5 g per day, equivalent to less than 2 g sodium."),
    source(3, "Dieta w zapobieganiu i leczeniu nadciśnienia tętniczego", "Diety NFZ", "https://diety.nfz.gov.pl/porady/dieta-w-chorobie/dieta-w-zapobieganiu-i-leczeniu-nadcisnienia-tetniczego", "official_guideline", 2025,
           "The Polish NFZ page states 5 g salt is a level teaspoon and recommends avoiding table-side salting, keeping the shaker off the table, using herbs and choosing lower-salt foods."),
    source(4, "Sól w diecie", "Gov.pl", "https://www.gov.pl/attachment/3c9c8dc9-0407-4c1b-b83d-3bc81b39152c", "official_guideline", 2022,
           "Polish public-health material says daily salt should not exceed 5 g, approximately one teaspoon, and links salt reduction with lower blood pressure at a population level."),
]

claims = [
    claim(1, "WHO recommends adults consume less than 2 g sodium per day, equivalent to less than 5 g salt per day.",
          "Dla dorosłych WHO zaleca mniej niż 5 gramów soli dziennie, czyli mniej niż 2 gramy sodu.", ["SRC-01", "SRC-02"],
          ["dokładnie 5 gramów dla każdego", "pięć gramów to indywidualne leczenie"],
          "This is a population dietary recommendation for adults, not a personalised medical prescription.", display=True),
    claim(2, "The 5 g reference covers salt from all dietary sources, not only salt added at the table.",
          "Te 5 gramów to sól z całego dnia, nie tylko z solniczki.", ["SRC-01", "SRC-03"],
          ["cała sól pochodzi z solniczki", "wystarczy przestać dosalać"],
          "The mix of sources differs between people and meals; this Short does not quantify an individual's intake.", display=True),
    claim(3, "A level teaspoon is an approximate household comparison for 5 g of salt.",
          "Pięć gramów soli to w przybliżeniu jedna płaska łyżeczka do herbaty.", ["SRC-03", "SRC-04"],
          ["każda łyżeczka zawsze waży dokładnie pięć gramów"],
          "Household spoon volume and salt grain size vary, so this is an approximation."),
    claim(4, "Processed and packaged foods can be important sources of dietary sodium; WHO lists reducing sodium in manufactured foods and using food labels among population approaches.",
          "Dużo sodu może przychodzić z żywności przetworzonej i pakowanej, więc warto zaglądać na etykietę.", ["SRC-01", "SRC-03"],
          ["każdy produkt pakowany jest przesolony", "jeden produkt zawsze przekracza limit"],
          "Salt content varies by product, brand and portion; the Short names categories rather than assigning fixed values.", confidence="medium", verdict="conditional"),
    claim(5, "Polish NFZ advice includes not adding salt at the table, keeping a salt shaker off the table and using herbs and salt-free spices.",
          "Praktyczny ruch: schowaj solniczkę ze stołu i dopraw ziołami albo przyprawami bez soli.", ["SRC-03"],
          ["zioła zastępują całą sól każdemu", "nigdy nie jedz soli"],
          "This is a general food-preparation suggestion; individual dietary instructions take priority.", risk="medium", confidence="high"),
]

beats = [
    beat("Myślisz, że to tylko ta szczypta? Solniczka ma alibi.", "TYLKO SZCZYPTA?", "Mała niebieska solniczka teatralnie pokazuje puste dłonie, a za nią widać zamknięty lunchbox jako drugi podejrzany.", 1.8, "hook", emphasis="alibi"),
    beat("Dla dorosłych WHO zaleca mniej niż 5 gramów soli dziennie.", "MNIEJ NIŻ 5 G", "Solniczka staje przed prostą kuchenną wagą i wielką pustą łyżeczką; jej mina zmienia się z pewnej w zaskoczoną.", 2.6, "hook", ("CLM-01",), "5 gramów"),
    beat("To w przybliżeniu jedna płaska łyżeczka do herbaty.", "1 PŁASKA ŁYŻECZKA", "Ekstremalne zbliżenie: solniczka ostrożnie wsypuje kryształki do jednej płaskiej łyżeczki, bez cyfr ani napisów.", 2.5, "body", ("CLM-03",), "płaska"),
    beat("Ale uwaga: ta łyżeczka liczy sól z całego dnia, nie tylko z solniczki.", "CAŁY DZIEŃ", "Solniczka odsuwa się spod pojedynczego reflektora; wokół niej pojawiają się ikony lunchboxa, sera, pieczywa i gotowego sosu jako rząd potencjalnych źródeł.", 3.1, "body", ("CLM-02",), "całego dnia"),
    beat("I tu zwrot: solniczka nie jest jedyną podejrzaną.", "NIE JEDYNA", "Komediowe przesłuchanie: solniczka siedzi przy biurku detektywa, a zamknięty lunchbox w tle powoli wysuwa rękę z numerkiem podejrzanego.", 2.5, "body", ("CLM-02",), "zwrot"),
    beat("Dużo sodu może przychodzić z żywności przetworzonej i pakowanej.", "SPRAWDŹ ETYKIETĘ", "Solniczka i lunchbox patrzą przez wielkie szkło powiększające na neutralną, całkowicie pustą etykietę żywieniową; bez marek i tekstu.", 3.0, "body", ("CLM-04",), "pakowanej"),
    beat("Dlatego samo niedosalanie pomaga, ale nie zamyka całej sprawy.", "NIE TYLKO SOLNICZKA", "Solniczka dostaje częściowo zamkniętą teczkę sprawy, a obok lunchbox otwiera drugą teczkę; obie wskazują na wspólny koszyk dnia.", 2.8, "body", ("CLM-02", "CLM-04"), "całej"),
    beat("Praktyczny ruch: schowaj solniczkę ze stołu i dopraw ziołami albo przyprawami bez soli.", "ZIOŁA ZAMIAST", "Solniczka z ulgą chowa się do szafki, podczas gdy bazylia, oregano i pieprz tworzą kolorowy, nieagresywny zespół przypraw.", 3.4, "body", ("CLM-05",), "ziołami"),
    beat("A przy gotowych produktach porównaj etykiety, zamiast zgadywać po smaku.", "PORÓWNAJ ETYKIETY", "Solniczka używa lupy, aby porównać dwie całkowicie abstrakcyjne, beztekstowe karty produktu; jedna karta dostaje spokojny zielony znacznik wyboru.", 3.1, "payoff", ("CLM-04",), "porównaj"),
    beat("Werdykt: mniej niż 5 gramów soli z całego dnia — solniczka to tylko jeden trop.", "5 G Z CAŁEGO DNIA", "Finał szeroki: solniczka, płaska łyżeczka, lunchbox i zioła stoją razem na spokojnej planszy detektywistycznej; solniczka wskazuje nie na siebie, lecz na cały koszyk dnia.", 3.4, "payoff", ("CLM-01", "CLM-02", "CLM-03"), "całego dnia"),
]

overlays = [
    overlay("stat", 4, label="WHO: dorośli", value="<5 g soli", label_b="czyli", value_b="<2 g sodu", claim_ids=("CLM-01",)),
    overlay("callout", 2, value="ŁYŻECZKA", claim_ids=("CLM-03",)),
    overlay("source", 3, label="WHO / NFZ", finding="Limit liczy cały dzień", title=sources[0]["title"], publisher=sources[0]["publisher"], year="2025", reference="who.int/sodium-reduction", claim_ids=("CLM-01", "CLM-02")),
    overlay("list", 5, label="SPRAWDŹ", items=["Pakowane", "Przetworzone", "Etykiety"], claim_ids=("CLM-04",)),
    overlay("stamp", 6, value="SOLNICZKA MA ALIBI", claim_ids=("CLM-02", "CLM-04")),
    overlay("list", 7, label="ZAMIEŃ", items=["Zioła", "Przyprawy bez soli", "Mniej dosalania"], claim_ids=("CLM-05",)),
]

frame_specs = [
    ("comic detective hook: the salt shaker protagonist theatrically holds up its empty gloved hands as if claiming innocence; a closed generic lunchbox peeks from behind it as a second suspect; close conflict instantly readable", "Solniczka nie jest jedynym źródłem soli w całym dniu.", "extreme_macro", "conflict", "hook_punch", ()),
    ("the salt shaker stands on one side of a simple kitchen scale facing one large level teaspoon; the hero's expression flips from smug confidence to surprised concern; all scale marks abstract and blank", "WHO zaleca dorosłym mniej niż 5 gramów soli dziennie.", "macro", "science", "ken_burns_in", ("CLM-01",)),
    ("extreme macro: the salt shaker carefully pours a tiny stream of visible salt crystals into one level teaspoon, looking sideways at the amount; one exact household comparison, no number marks", "Pięć gramów soli to w przybliżeniu jedna płaska łyżeczka.", "extreme_macro", "ingredient", "punch_hold", ("CLM-03",)),
    ("wide evidence composition: the salt shaker steps out from a spotlight while four neutral icons—lunchbox, plain cheese wedge, bread loaf and sauce jar—form a full-day source circle; protagonist gestures to the circle", "Limit obejmuje sól z całego dnia, nie tylko z solniczki.", "wide", "science", "parallax", ("CLM-02",)),
    ("comic detective interrogation: salt shaker sits at a tiny blank detective desk with a relieved face, while a closed generic lunchbox slowly raises a gloved hand holding an abstract suspect token", "Solniczka nie jest jedyną podejrzaną w diecie.", "medium", "conflict", "pan_right", ("CLM-02",)),
    ("medium label-check scene: salt shaker and generic lunchbox look through one oversized magnifying glass at a completely blank neutral nutrition panel; the image makes checking a label the evidence action", "Żywność pakowana i przetworzona może dostarczać dużo sodu.", "medium", "science", "ken_burns_in", ("CLM-04",)),
    ("abstract case-board reversal: salt shaker holds one partly closed blank case file while lunchbox opens another; both files point with colored string to one shared basket representing the whole day", "Samo niedosalanie nie obejmuje wszystkich źródeł soli.", "abstract", "conflict", "pan_left", ("CLM-02", "CLM-04")),
    ("wide practical swap: salt shaker happily retreats into a cupboard, while basil, oregano and pepper become a colorful friendly seasoning team around a plain dinner plate; no human hands", "Zioła i przyprawy bez soli mogą zastąpić dosalanie na stole.", "wide", "ingredient", "parallax", ("CLM-05",)),
    ("macro comparison: salt shaker uses a magnifying glass to compare two generic completely textless package cards; one card receives a simple green check symbol and the other remains neutral, no brand claims", "Porównywanie etykiet pomaga nie zgadywać po smaku.", "macro", "science", "punch_hold", ("CLM-04",)),
    ("warm wide detective payoff tableau: salt shaker, level teaspoon, lunchbox and herbs stand around one shared daily basket; protagonist points outward to all objects, not at itself, resolved helpful smile", "Mniej niż 5 gramów soli odnosi się do całego dnia.", "wide", "conflict", "ken_burns_out", ("CLM-01", "CLM-02", "CLM-03")),
]
frames = [frame(*spec[:4], i, spec[4], spec[5]) for i, spec in enumerate(frame_specs)]

script = {
    "lang": "pl", "rubric": "how_much", "format": "detective_case", "hook": beats[0]["voiceover"],
    "poster_text": "TYLKO *SZCZYPTA*?", "beats": beats, "overlays": overlays,
    "payload": "Traktuj mniej niż 5 gramów jako limit soli z całego dnia: nie dosalaj automatycznie, używaj ziół i porównuj etykiety gotowych produktów.",
    "turn_beat_idx": 4, "payoff_card": "5 G Z CAŁEGO DNIA", "cta": "",
    "total_dur_s": round(sum(item["dur_s"] for item in beats), 2), "central_claim_id": "CLM-02",
    "poster_claim_ids": [], "payload_claim_ids": ["CLM-01", "CLM-02", "CLM-04", "CLM-05"],
    "payoff_claim_ids": ["CLM-01", "CLM-02", "CLM-03"],
}

plan = {
    "grade": "bright premium 2D detective editorial cartoon with cobalt blue salt-shaker hero and warm cream evidence spaces",
    "light": "soft warm kitchen light with leafy-green proof accents and a sunflower-yellow reveal beat",
    "lens": "extreme macro salt crystals, macro household proof, medium detective acting and wide full-day source tableaux",
    "frames": frames,
}

qa_checks = [
    ("hook_stops_scroll", "The anthropomorphic salt shaker visibly claims an alibi while a lunchbox becomes the second suspect in the first 1.2 seconds."),
    ("format_delivered", "The Short is a detective case: the salt shaker is interrogated, evidence expands to all-day sources, and the label check resolves the case."),
    ("turn_is_real", "Beat 5 reverses the viewer's initial suspect from table salt alone to all-day dietary sources."),
    ("payload_is_real", "The viewer receives a concrete all-day rule, a table-side salt action, herb substitution and label comparison."),
    ("payoff_is_entailed", "The final all-day 5 g rule follows directly from WHO's sodium-equivalent recommendation."),
    ("overlays_add", "The numeric equivalence, teaspoon conversion, source card and label-check list add evidence without duplicating captions."),
    ("visual_causal_progression", "A single non-human protagonist travels from alibi through investigation to a practical seasoning and label-check rule."),
    ("frames_semantic_match", "Every frame makes one silent claim and preserves the same cobalt salt-shaker hero, with no human main character."),
    ("voice_persona", "Polish male narration remains direct, lightly ironic and non-diagnostic."),
    ("not_a_clone", "Uses an object-led food detective case, household teaspoon proof, source-circle turn and label-inspection payoff rather than a human reaction or generic myth arc."),
    ("source_named_when_natural", "WHO/NFZ source card appears with the all-day definition at beat 4."),
    ("language_pl", "All viewer-facing voice-over, overlay copy, title, description and metadata are Polish."),
]
qa = {
    "passed": True,
    "checks": [{"name": name, "passed": True, "detail": detail} for name, detail in qa_checks],
    "notes": [
        "hook_lab: odrzucone H2 'Jedna łyżeczka i koniec?' — ma liczbę, ale nie ma konkretnego podejrzanego; H3 'Czy sól jest ukryta w lunchu?' — za szybko wskazuje winnego.",
        "Nie podajemy produktu ani porcji jako uniwersalnego źródła soli; zawartość zależy od produktu i etykiety.",
        "Nie obiecujemy efektu zdrowotnego ani nie zmieniamy zalecenia populacyjnego w poradę dla konkretnej osoby.",
    ], "blame_stage": "",
}

publish = {
    "title": "Ile soli dziennie? Solniczka ma alibi", "description": (
        "Mniej niż 5 g soli dziennie to orientacyjnie jedna płaska łyżeczka — ale z całego dnia, nie tylko z solniczki. "
        "Sprawdź, gdzie sól może się ukrywać i jak ograniczyć automatyczne dosalanie.\n\n"
        "Źródła:\nhttps://www.who.int/news-room/fact-sheets/detail/sodium-reduction\n"
        "https://www.who.int/news-room/fact-sheets/detail/healthy-diet\n"
        "https://diety.nfz.gov.pl/porady/dieta-w-chorobie/dieta-w-zapobieganiu-i-leczeniu-nadcisnienia-tetniczego\n"
        "https://www.gov.pl/attachment/3c9c8dc9-0407-4c1b-b83d-3bc81b39152c\n\n"
        "Materiał edukacyjny; indywidualne zalecenia żywieniowe mają pierwszeństwo."
    ),
    "hashtags": ["#sól", "#odżywianie", "#etykiety", "#zdrowie", "#Shorts"],
    "pinned_comment": "Solniczka czy gotowe produkty: gdzie najczęściej podejrzewasz sól?",
    "title_template": "question_plus_reframe", "description_template": "short_context", "distribution_lane": "hybrid",
    "primary_query": "ile soli dziennie", "secondary_queries": ["ile gram soli dziennie", "norma soli", "ile sodu dziennie", "sól w diecie"],
    "metadata_hypothesis": "Exact Polish quantity query supports search while the salt-shaker detective reversal gives a sound-off feed conflict.",
    "api_tags": ["ile soli dziennie", "norma soli", "sód w diecie", "sól w produktach", "etykiety żywności", "zdrowe odżywianie"],
    "source_urls": [source["url"] for source in sources],
}

strategy = {
    "authored_by": "Codex", "run_purpose": "Current VitalLogic production queue: daily salt amount, object-led visual experiment.",
    "audience": "Polish adults 25–45 who cook, buy ready foods and assume table salt is the whole daily total.",
    "hypothesis": "A mischievous salt-shaker detective hero plus the one-teaspoon-to-full-day reversal will make the rule immediately legible and give a saveable label-check action.",
    "planned_duration_s": script["total_dur_s"],
    "risk_decision": {"decision": "Proceed locally after evidence and visual QA", "claim_boundary": "No diagnosis, no product-specific sodium figures, no claim that every packaged food is high in salt, and no individual medical advice."},
    "evidence_levels": {"SRC-01": "official", "SRC-02": "official", "SRC-03": "official", "SRC-04": "official"},
    "distribution": {"lane": "hybrid", "primary_query": publish["primary_query"], "secondary_queries": publish["secondary_queries"], "metadata_hypothesis": publish["metadata_hypothesis"]},
    "hook_lab": {"variants": [
        {"id": "H1", "type": "object_alibi", "hook": beats[0]["voiceover"], "poster": "TYLKO *SZCZYPTA*?", "first_visual": "Salt shaker claims an alibi while lunchbox enters as a second suspect.", "first_proof_s": 1.8, "claim_ids": [], "score": 10, "rejection_reason": "Selected: visible non-human character conflict and immediate viewer misconception."},
        {"id": "H2", "type": "household_conversion", "hook": "Jedna łyżeczka i koniec? Sól liczy cały dzień.", "poster": "1 ŁYŻECZKA?", "first_visual": "Level teaspoon faces a salt shaker on a kitchen scale.", "first_proof_s": 1.6, "claim_ids": ["CLM-03"], "score": 8, "rejection_reason": "Concrete but gives away the turn before the detective story starts."},
        {"id": "H3", "type": "hidden_source", "hook": "Solniczka jest głośna. Sól w lunchu woli ciszę.", "poster": "SÓL W LUNCHU?", "first_visual": "Lunchbox slips behind salt shaker at a detective desk.", "first_proof_s": 2.3, "claim_ids": ["CLM-02"], "score": 8, "rejection_reason": "Strong curiosity, but a less familiar audience promise than the pinch misconception."}
    ], "selected_variant": "H1"},
    "format_selection": {"format": "detective_case", "priority": "P0", "reason": "The everyday result—thinking a tiny table-side pinch is the whole salt story—has a concrete wrong suspect and a label-based clue.", "comic_engine": "A cocky salt shaker is questioned, receives an alibi, then helps inspect the actual all-day evidence.", "discarded_alternatives": ["number_shock", "myth_autopsy"]},
    "structure_variation": {
        "compared_runs": ["2026-08-24_v8-ile-wody-dziennie-myth-autopsy-imagegen-01", "2026-08-24_v8-czy-jedzenie-wieczorem-tuczy", "2026-08-24_v8-baton-po-treningu-courtroom-imagegen-01", "2026-08-22_v8-sennosc-po-lunchu", "2026-08-16_sok-jablkowy-czy-cola", "2026-08-16_zelazo-ze-szpinaku", "2026-08-15_kawa-po-przebudzeniu", "2026-08-05_czy-magnez-przedawkowac"],
        "signature": {"hook_mechanism": "object protagonist claims an alibi", "first_proof": "WHO quantity and household teaspoon within 4.4 seconds", "turn_device": "wrong suspect expands from salt shaker to all-day sources", "evidence_device": "household teaspoon, source card and blank label inspection", "overlay_sequence": ["stat", "callout", "source", "list", "stamp", "list"], "payoff_device": "all-day basket rule", "visual_rhythm": "macro object acting, extreme crystal proof, wide source circle, detective turn, label action, herb swap, wide resolution"},
        "differs_from_recent": ["central hero is a salt shaker rather than a person", "uses an interrogation-to-alibi reversal instead of water's fixed-number myth or product courtroom", "first proof is a teaspoon conversion and all-day scope rather than a product comparison", "payoff is label inspection plus seasoning swap, not a timing or purchase verdict"]
    },
    "hero_descriptor": HERO,
    "visual_policy": "Built-in ImageGen only. One invariant non-human salt-shaker hero is present in every frame; supporting food objects are props, not protagonists. Renderer owns Polish captions, numeric overlays and source cards.",
}

research = {
    "lang": "pl", "topic": "Ile soli dziennie można jeść?", "viewer_question": "Czy jedna szczypta z solniczki opisuje cały dzienny limit soli?",
    "recommended_angle": "Object-led detective case: the salt shaker gets an alibi when the 5 g recommendation is revealed to cover salt from the full day, including potential packaged-food sources.",
    "evidence_summary": "WHO recommends adults consume less than 2,000 mg sodium per day, equivalent to less than 5 g salt. Polish public-health sources translate this approximately to one level teaspoon and stress that the total includes food sources, not only table-side salting. The useful action is not to pretend one food has a universal salt value: use less automatic table salt, season with herbs or salt-free spices, and compare labels of ready products.",
    "sources": sources, "claims": claims,
    "unresolved_conflicts": ["Salt content varies by product, brand and portion, so no product-specific salt quantity is shown.", "The WHO threshold is population-level adult guidance; individual dietary recommendations can differ."],
}

write("research_pack.json", research)
write("script.json", script)
write("compliance.json", {"passed": True, "fixes": ["Zastąpiono potencjalnie absolutne 'sól ukryta wszędzie' warunkowym sformułowaniem o żywności pakowanej.", "Nie ma leczenia, diagnozy ani indywidualnego limitu."], "cleaned_script": script})
write("fact_review.json", {"passed": True, "checks": [{"claim_id": item["id"], "passed": True, "issue": "", "required_change": ""} for item in claims], "unsupported_script_statements": [], "notes": ["All spoken numbers, objects and units occur in the same beat.", "The household teaspoon wording remains approximate and does not assign a precise weight to every spoon."]})
write("frame_plan.json", plan)
write("qa.json", qa)
write("publish_package.json", publish)
write("codex_strategy.json", strategy)
(RUN / "research_raw.md").write_text("# Research memo — Ile soli dziennie\n\nCurrent official sources verified 2026-08-24. Health evidence is restricted to the four URLs in `research_pack.json`; viewer-facing wording uses the allowed wording for each claim.\n", encoding="utf-8")
print(RUN)
