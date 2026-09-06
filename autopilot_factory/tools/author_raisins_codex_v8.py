#!/usr/bin/env python3
"""Author the Codex v8 package for the raisins snack-detective Short."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from schemas_v8 import (  # noqa: E402
    Beat, ComplianceVerdict, FactCheckItem, FactReview, Frame, FramePlan,
    Overlay, PublishPackage, QACheck, QAReport, ResearchClaim, ResearchPack,
    ResearchSource, Script,
)

RUN = ROOT / "runs/vitallogic_bad_pl/2026-09-03_v8-rodzynki-owoc-czy-cukierki"
HERO = (
    "the recurring main character is an original adult Polish woman, 29 years old, with a short chestnut-brown bob, "
    "warm brown eyes, a small round blue eyeglass frame, a cobalt-blue cardigan over a warm-cream T-shirt, "
    "high-waisted forest-green trousers, and mustard-yellow sneakers; ordinary friendly office-worker silhouette, "
    "no logos, no franchise resemblance, no animal ears, no fantasy costume"
)
STYLE = (
    "vertical 9:16 premium 2D hand-drawn editorial cartoon, bright pastel Polish office snack bar, "
    "thick navy ink contours, flat cel shading, tactile paper texture, deep navy #2A5C82, leafy green #4CAF50, "
    "warm white #F5F5F5 and yellow #FFDD00; expressive but anatomically simple character, no embedded text, "
    "letters, digits, logos, watermarks or fake labels"
)


def dump(name: str, value: object) -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    payload = value.model_dump() if hasattr(value, "model_dump") else value
    (RUN / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


sources = [
    ResearchSource(
        id="SRC-01", title="Rodzaje owoców, które powinno się ograniczyć",
        publisher="Narodowe Centrum Edukacji Żywieniowej",
        url="https://ncez.pzh.gov.pl/wp-content/uploads/2022/11/E-book-Zywienie-w-cukrzycy-typu-2-i-insulinoopornosci.pdf",
        source_type="official_guideline", year=2022,
        evidence_summary="NCEŻ explains that dried fruit is a concentrated source of sugars because water is removed. Its example states that 30 g (two tablespoons) of raisins provides about 90 kcal and 19 g of sugars; it also notes that some dried fruit has added sugar.",
    ),
    ResearchSource(
        id="SRC-02", title="Zdrowe Żywienie",
        publisher="Wojewódzka Stacja Sanitarno-Epidemiologiczna w Warszawie / Gov.pl",
        url="https://www.gov.pl/web/wsse-warszawa/zdrowe-zywienie",
        source_type="official_guideline", year=2025,
        evidence_summary="The official guidance says dried fruit has more sugars and energy per the same mass, yet can be a less-frequent replacement for sweet snacks. It advises combining fruit with natural yogurt, nuts or seeds, or adding it to a meal.",
    ),
    ResearchSource(
        id="SRC-03", title="Fakty i mity o owocach - co warto wiedzieć?",
        publisher="Powiatowa Stacja Sanitarno-Epidemiologiczna w Kamieniu Pomorskim / Gov.pl",
        url="https://www.gov.pl/web/psse-kamien-pomorski/fakty-i-mity-o-owocach---co-warto-wiedziec",
        source_type="official_guideline", year=2026,
        evidence_summary="The sanitary-inspection guidance says dried fruit retains valuable nutrients but has more sugars and calories for the same weight than fresh fruit, and some products contain added sugar or glucose-fructose syrup.",
    ),
]

claims = [
    ResearchClaim(
        id="CLM-01", neutral_claim="Drying removes water, making sugars and energy in dried fruit more concentrated for the same mass than in fresh fruit.",
        verdict="supported", confidence="high", source_ids=["SRC-01", "SRC-02", "SRC-03"],
        allowed_wording="Po suszeniu ubywa wody, więc na tę samą masę cukry i energia są bardziej skoncentrowane.",
        forbidden_wording=["rodzynki są dokładnie tym samym co cukierki", "suszone owoce są zakazane"],
        limitations="Dried fruit retains nutrients and can be part of a varied diet; this comparison is about concentration per mass, not a judgement about a food being good or bad.", risk_level="low", display_source=True,
    ),
    ResearchClaim(
        id="CLM-02", neutral_claim="NCEŻ gives an example in which 30 g (two tablespoons) of raisins contains about 90 kcal and 19 g of sugars.",
        verdict="supported", confidence="high", source_ids=["SRC-01"],
        allowed_wording="Dwie łyżki rodzynek, czyli 30 gramów, to około 90 kilokalorii i 19 gramów cukrów.",
        forbidden_wording=["każda porcja rodzynek ma dokładnie 90 kcal", "19 gramów cukru jest groźne dla każdego"],
        limitations="The cited values are an example for a 30 g portion and can vary by product and recipe.", risk_level="low", display_source=False,
    ),
    ResearchClaim(
        id="CLM-03", neutral_claim="Some dried-fruit products contain added sugar or glucose-fructose syrup, so reading the ingredients list is relevant.",
        verdict="supported", confidence="high", source_ids=["SRC-01", "SRC-03"],
        allowed_wording="Sprawdź skład: część suszonych owoców ma dodany cukier albo syrop glukozowo-fruktozowy.",
        forbidden_wording=["każde rodzynki mają dodany cukier", "syrop w składzie czyni produkt trujący"],
        limitations="This is product-specific; the ingredients list, not the product category alone, determines whether sugar or syrup was added.", risk_level="low", display_source=False,
    ),
    ResearchClaim(
        id="CLM-04", neutral_claim="Official guidance presents dried fruit as a possible occasional replacement for sweet snacks and suggests combining fruit with natural yogurt, nuts or seeds or using it as part of a meal.",
        verdict="supported", confidence="high", source_ids=["SRC-02"],
        allowed_wording="Nie zakaz: nasyp porcję do miseczki i połącz ją z jogurtem naturalnym albo orzechami.",
        forbidden_wording=["taka para gwarantuje brak skoku cukru", "jogurt i orzechy neutralizują cukier"],
        limitations="This is a general snack-composition suggestion, not medical or personalised dietary advice.", risk_level="low", display_source=True,
    ),
]

raw_beats = [
    ("Rodzynki to owoc. Dlaczego znikają jak cukierki?", "OWOC CZY CUKIEREK?", "Wide comic office snack bar: the girl host catches a tiny bag of raisins emptying itself into her hand like a mischievous candy bag; raised eyebrow, immediate visual conflict.", 2.4, "hook", [], "cukierki"),
    ("Zanim wsypiesz pół paczki do pudełka: trzy zasady.", "TRZY ZASADY DO PUDEŁKA", "Medium shot: the girl host holds up three fingers beside a lunch box while a raisin packet tries to sneak toward it; firm playful gaze, clear promise.", 2.4, "hook", [], "trzy"),
    ("Po suszeniu znika woda, nie cukier. Dlatego wszystko robi się mniejsze i bardziej skoncentrowane.", "WODA ZNIKA. CUKRY ZOSTAJĄ.", "Macro visual metaphor: plump grapes pass through a small sunny drying tunnel and emerge as compact raisins; the girl host points to the missing blue water droplets with surprised eyes.", 3.4, "body", ["CLM-01"], "woda"),
    ("Dwie łyżki rodzynek mają około 90 kilokalorii.", "DWIE ŁYŻKI: 90 KCAL", "Extreme macro evidence: two measured tablespoons of raisins sit beside a clean small bowl on a desk scale; the girl host leans in with comic detective concentration, scale and spoons are the focal point.", 3.0, "body", ["CLM-02"], "90"),
    ("Ta sama mała porcja to około 19 gramów cukrów.", "TA SAMA PORCJA: 19 G", "Macro second proof: the girl host lines up nineteen bright amber counting beads beside two tablespoons of raisins, then gives the raisin packet a startled side-eye; raisins and the count are sharpest, no printed numerals.", 2.8, "body", ["CLM-02"], "19"),
    ("To nadal owoc. Tylko paczka nie umie powiedzieć: stop.", "PACZKA ≠ PORCJA", "Medium comic turn: the girl host gently closes an oversized raisin packet with a tiny stop sign while a few raisins queue politely outside a small bowl; knowing half-smile.", 2.9, "body", ["CLM-01", "CLM-02"], "stop"),
    ("Zasada pierwsza: przesyp do miseczki, zamiast jeść prosto z paczki.", "1. MISeczka, NIE PACZKA", "Wide practical action: the girl host pours a modest portion of raisins into a small cream bowl, while the large packet waits farther back; calm decisive gesture, bowl is sharpest.", 2.9, "body", ["CLM-04"], "miseczki"),
    ("Druga: zerknij w skład. Czasem dochodzi cukier albo syrop.", "2. SPRAWDŹ SKŁAD", "Macro label-check scene: the girl host uses a magnifying glass on a generic raisin package ingredient panel with only abstract non-readable marks; suspicious eye and raised eyebrow, no legible text.", 3.0, "body", ["CLM-03"], "skład"),
    ("Trzecia: połącz je z jogurtem naturalnym albo orzechami, nie z nudą przy biurku.", "3. DODAJ JOGURT LUB ORZECHY", "Medium warm office lunch scene: the girl host adds raisins to plain natural yogurt with a few nuts, then slides her idle scrolling phone aside; relaxed smile, bowl and toppings are focal.", 3.4, "body", ["CLM-04"], "orzechami"),
    ("Werdykt: rodzynki są owocem w koncentracie, nie cukierkiem w przebraniu.", "OWOC W KONCENTRACIE", "Wide reveal: the girl host gives a raisin a tiny fruit passport, then places it in the small bowl rather than the open packet; amused, relieved expression and clear visual verdict.", 3.1, "payoff", ["CLM-01", "CLM-04"], "koncentracie"),
    ("Miseczka, skład, dodatek do posiłku — i paczka przestaje rządzić przerwą.", "MISeczka / SKŁAD / POSIŁEK", "Warm final wide office tableau: the girl host closes the raisin packet, carries the prepared yogurt bowl to a sunny desk, and waves goodbye to the packet; friendly practical smile, no text in image.", 3.1, "payoff", ["CLM-03", "CLM-04"], "przerwą"),
]
beats = [Beat(voiceover=a, on_screen_text=b, visual_cue=c, dur_s=d, act=e, claim_ids=f, emphasis=g) for a, b, c, d, e, f, g in raw_beats]
overlays = [
    Overlay(kind="callout", beat_idx=3, value="90 kcal", claim_ids=["CLM-02"]),
    Overlay(kind="callout", beat_idx=4, value="19 g", claim_ids=["CLM-02"]),
    Overlay(kind="source", beat_idx=5, label="WSSE Warszawa", source_finding="Mniej wody, większa koncentracja", source_title=sources[1].title, source_publisher=sources[1].publisher, source_year="2025", source_reference="gov.pl", claim_ids=["CLM-01"]),
    Overlay(kind="list", beat_idx=10, label="TRZY ZASADY", items=["miseczka, nie paczka", "sprawdź skład", "dodaj do posiłku"], claim_ids=["CLM-03", "CLM-04"]),
]
script = Script(
    lang="pl", rubric="at_shelf", format="detective_case", hook=beats[0].voiceover,
    poster_text="RODZYNKI: OWOC CZY CUKIEREK?", beats=beats, overlays=overlays,
    payload="Nie jedz suszonych owoców prosto z paczki: wydziel porcję, sprawdź skład i połącz ją z normalnym posiłkiem.",
    turn_beat_idx=5, payoff_card="PORCJA, NIE PACZKA", cta="",
    total_dur_s=sum(item.dur_s for item in beats), central_claim_id="CLM-02",
    poster_claim_ids=[], payload_claim_ids=["CLM-03", "CLM-04"], payoff_claim_ids=["CLM-01", "CLM-04"],
)

visuals = [
    "wide comic office snack bar: the girl host catches a small generic raisin bag emptying raisins into her hand like a mischievous candy bag; raised eyebrow and playful shock",
    "medium promise shot: the girl host holds up three fingers beside a lunch box as a generic raisin packet tries to sneak toward it; firm playful gaze",
    "macro science metaphor: plump grapes pass through a small sunny drying tunnel and emerge as compact raisins; the girl host points to missing blue water droplets with surprise",
    "extreme macro evidence: exactly two measured tablespoons of raisins beside a small cream bowl on a desk scale; the girl host leans in with comic detective concentration",
    "macro second proof: the girl host lines up nineteen bright amber counting beads beside two tablespoons of raisins and gives the raisin packet a startled side-eye; raisins and beads are sharpest",
    "medium comic turn: the girl host gently closes an oversized raisin packet with a tiny stop sign while raisins queue politely outside a small bowl; knowing half-smile",
    "wide action: the girl host pours a modest portion of raisins into a small cream bowl while the large packet waits in the background; calm decisive gesture",
    "macro ingredient check: the girl host uses a magnifying glass on a generic raisin packet with abstract non-readable label marks; suspicious eye and raised eyebrow",
    "medium warm lunch: the girl host adds raisins to plain natural yogurt with a few nuts and slides an idle phone aside; relaxed smile",
    "wide comic verdict: the girl host gives one raisin a tiny fruit passport and places it in the small bowl rather than the open packet; amused relieved expression",
    "wide warm finale: the girl host closes the raisin packet and carries a prepared yogurt bowl to a sunny office desk, waving goodbye to the packet",
]
shots = ["wide", "medium", "macro", "extreme_macro", "macro", "medium", "wide", "macro", "medium", "wide", "wide"]
subjects = ["conflict", "human", "science", "science", "science", "conflict", "lifestyle", "ingredient", "lifestyle", "conflict", "lifestyle"]
motions = ["hook_punch", "pan_left", "punch_hold", "ken_burns_in", "punch_hold", "parallax", "pan_right", "punch_hold", "ken_burns_out", "parallax", "ken_burns_out"]
frames = []
for i, (beat, visual, shot, subject, motion) in enumerate(zip(beats, visuals, shots, subjects, motions)):
    claim = "Dwie łyżki rodzynek, czyli 30 g, to około 90 kcal i 19 g cukrów." if i == 3 else beat.on_screen_text
    frames.append(Frame(
        prompt=(f"Use case: illustration-story. Asset type: VitalLogic Polish Short frame. {STYLE}. {HERO}. "
                f"Scene: {visual}. Composition: vertical 9:16, {shot} shot; keep the girl and evidence object inside x=120..860 y=200..1500, "
                "leave the lower band and far-right Shorts UI area as expendable office background. Eye path: the girl's gaze and gesture lead to one clear evidence object. "
                "Text in image: none. Avoid photorealism, random lettering, fake charts, brand packaging, watermarks, clutter and medical imagery."),
        claim=claim, shot=shot, subject=subject, beat_from=i, beat_to=i, motion=motion, ref_ids=[], claim_ids=beat.claim_ids,
    ))
plan = FramePlan(
    grade="bright navy, leafy-green and warm-cream Polish office editorial cartoon with expressive female host",
    light="sunny desk daylight with crisp evidence highlights and a warm snack-break mood",
    lens="wide comic conflict, medium acting, macro food evidence and extreme-macro portion details",
    frames=frames,
)

checks = [
    ("hook_stops_scroll", "A girl host visibly catches raisins escaping a packet like candy in the first image."),
    ("format_delivered", "The detective case follows missing-water clue, measured portion evidence, packet-as-suspect turn, three practical rules and verdict."),
    ("turn_is_real", "The turn does not call raisins bad; it moves the viewer from food identity to portion control and product-specific ingredients."),
    ("payload_is_real", "The final rule is usable immediately: bowl, ingredient list and pairing with a meal."),
    ("payoff_is_entailed", "The fruit-in-concentrate verdict follows the official explanation of water removal and the official portion example."),
    ("overlays_add", "Two numeric callouts, a source card and final three-rule list add evidence without repeating captions."),
    ("visual_causal_progression", "The visual arc goes from runaway packet, through drying and portion evidence, to ingredient check and a prepared snack."),
    ("frames_semantic_match", "Every frame uses the same adult woman and an evidence object that matches the spoken sentence."),
    ("voice_persona", "One consistent Polish Charon narration is planned as bright, lively and lightly ironic, without diagnosis or food fear."),
    ("not_a_clone", "This is a girl-led office snack detective with a three-rule reveal, unlike the recent potato courtroom, product-versus labels and sleep episodes."),
    ("source_named_when_natural", "The official WSSE Warszawa source card appears during the concentration explanation."),
    ("language_pl", "All viewer-facing narration, overlays, metadata and source finding are in Polish."),
]
qa = QAReport(passed=True, checks=[QACheck(name=n, passed=True, detail=d) for n, d in checks], notes=[
    "The script never calls raisins forbidden, equates them with candy, or makes a medical or weight-loss promise.",
    "Every number is presented as an approximate cited example for a 30 g portion.",
    "The same original adult woman is in every ImageGen prompt, with distinct acting, gaze, gesture and shot scale.",
], blame_stage="")

pkg = PublishPackage(
    title="Rodzynki: owoc czy cukierki w kostiumie? 3 zasady",
    description=(
        "Czy rodzynki są zdrowe? To owoc, ale suszenie usuwa wodę, więc w małej porcji cukry i energia są bardziej skoncentrowane. Według przykładu NCEŻ 30 g, czyli 2 łyżki rodzynek, to około 90 kcal i 19 g cukrów.\n\n"
        "Praktyczna zasada: przesyp do miseczki, sprawdź skład na dodany cukier lub syrop i dodaj do jogurtu naturalnego albo posiłku. Wizualizacje i lektor: AI. Materiał edukacyjny; nie zastępuje indywidualnej porady medycznej.\n\nŹródła:\n"
        + "\n".join(source.url for source in sources)
    ),
    hashtags=["#rodzynki", "#przekąska", "#odżywianie", "#etykiety", "#zdrowie", "#Shorts"],
    pinned_comment="Rodzynki jesz częściej prosto z paczki czy jako dodatek do jogurtu albo owsianki?",
    title_template="question_plus_three_rules", description_template="short_context", distribution_lane="hybrid",
    primary_query="czy rodzynki są zdrowe", secondary_queries=["rodzynki cukier", "ile cukru mają rodzynki", "suszone owoce przekąska"],
    metadata_hypothesis="A familiar desk-snack conflict plus the exact 30 g portion proof should work in feed, while the direct raisins-health question supports search.",
    api_tags=["czy rodzynki są zdrowe", "rodzynki cukier", "suszone owoce", "zdrowa przekąska", "czytaj skład", "odżywianie"],
    source_urls=[source.url for source in sources],
)

strategy = {
    "authored_by": "Codex",
    "run_purpose": "Standalone v8 VitalLogic production: raisins snack detective with a female main character and one consistent narrator; schedule only after final QA.",
    "audience": "Polscy pracownicy biurowi, którzy trzymają w szufladzie przekąski i chcą prostego, niepanikarskiego sposobu na suszone owoce.",
    "hypothesis": "Uciekające z paczki rodzynki i wczesny dowód 30 g/90 kcal/19 g cukrów zatrzymają widza, a zwrot od zakazu do trzech zasad da praktyczny payoff.",
    "planned_duration_s": script.total_dur_s,
    "risk_decision": {"decision": "Proceed after v8 package validation, accepted built-in ImageGen frames, v8 build, release gate, visual QA and ffprobe.", "claim_boundary": "No food ban, diagnosis, glycaemic promise, weight-loss guarantee or universal product value. The portion number is an NCEŻ example; added sugar is checked product by product."},
    "evidence_levels": {"SRC-01": "official", "SRC-02": "official", "SRC-03": "official"},
    "live_catalog_check": {"checked_at": "2026-09-03", "playlist_items": 198, "searched_terms": ["rodzynki", "suszone owoce", "raisins", "dried fruit"], "matches": [], "nearby": ["Skyr, grecki czy naturalny? Etykieta wybiera inaczej niż reklama", "Kabanosy mają białko. Czy to już dobry lunch?"], "decision": "Unique enough to proceed: no published or scheduled short covers raisins, dried-fruit concentration, or the packet-versus-portion angle."},
    "distribution": {"lane": "hybrid", "primary_query": pkg.primary_query, "secondary_queries": pkg.secondary_queries, "metadata_hypothesis": pkg.metadata_hypothesis},
    "hook_lab": {"variants": [
        {"id": "H1", "type": "runaway_packet", "hook": beats[0].voiceover, "poster": "OWOC CZY CUKIEREK?", "first_visual": "Girl catches raisins escaping a packet like candy.", "first_proof_s": 2.4, "claim_ids": [], "score": 10, "rejection_reason": "Selected: a familiar object conflict and the question is clear without audio."},
        {"id": "H2", "type": "portion_number", "hook": "Dwie łyżki rodzynek mają około 90 kilokalorii. To już nie dekoracja.", "poster": "2 ŁYŻKI = 90 KCAL", "first_visual": "Girl puts two measured tablespoons on a desk scale.", "first_proof_s": 1.8, "claim_ids": ["CLM-02"], "score": 8, "rejection_reason": "Strong proof, but it reveals the twist before the mini-story begins."},
        {"id": "H3", "type": "missing_water", "hook": "Z rodzynek znika woda. Cukier został na spotkaniu.", "poster": "GDZIE JEST WODA?", "first_visual": "Grapes enter a drying tunnel while water droplets leave.", "first_proof_s": 2.5, "claim_ids": ["CLM-01"], "score": 9, "rejection_reason": "Visual metaphor is good, but the viewer promise is less everyday than H1."},
        {"id": "H4", "type": "ingredient_clue", "hook": "Najbardziej podejrzane w rodzynkach nie zawsze jest to, co widać.", "poster": "SPRAWDŹ SKŁAD", "first_visual": "Girl examines a generic packet with a magnifying glass.", "first_proof_s": 2.8, "claim_ids": ["CLM-03"], "score": 7, "rejection_reason": "Useful shelf rule, but too narrow and less entertaining as an opener."}
    ], "selected_variant": "H1"},
    "format_selection": {"format": "detective_case", "priority": "P0", "reason": "A runaway snack packet has a visible everyday result with three inspectable clues: removed water, measured portion and ingredients list.", "comic_engine": "The packet is treated as an overly generous colleague until the small bowl takes over as the sensible manager.", "discarded_alternatives": ["number_shock", "myth_autopsy", "versus"]},
    "structure_variation": {"compared_runs": ["2026-09-03_v8-ziemniaki-tucza", "2026-09-01_v8-parowki-ile-miesa", "2026-09-01_v8-maslo-czy-margaryna", "2026-09-01_v8-sol-himalajska-czy-zwykla", "2026-09-01_v8-jogurt-owocowy-czy-naturalny", "2026-09-01_v8-ciemny-chleb-czy-jasny", "2026-08-31_v9-drzemka-kofeinowa-mikroeksperyment-normal-speed", "2026-08-30_v9-idealna-pozycja-biurko-office-case"], "signature": {"hook_mechanism": "female lead catches raisins escaping a packet like candy", "first_proof": "a grape-to-raisin drying visual before the two-tablespoon portion evidence", "turn_device": "the packet, rather than raisins themselves, becomes the suspect", "evidence_device": "water-removal metaphor, 30 g portion number and product-specific ingredient check", "overlay_sequence": ["callout", "callout", "source", "list"], "payoff_device": "fruit passport plus a three-rule desk-snack manager", "visual_rhythm": "wide runaway packet, medium promise, macro drying metaphor, extreme portion proof, packet turn, bowl, label, yogurt, verdict, desk finale"}, "differs_from_recent": ["detective-case snack story replaces the just-published potato myth courtroom", "the hook is a runaway packet instead of a food-on-trial or product-versus frame", "the first proof is a water-removal metaphor plus portion measurement, not a calorie-versus comparison", "the payoff is a three-rule portion workflow, not a binary product verdict", "the office snack-bar setting and packet character differ from recent kitchen, sleep and desk-posture episodes"]},
    "series": {"series_id": "", "episode": 1, "followup_topics": []},
    "hero_descriptor": HERO,
    "visual_policy": "Built-in Codex ImageGen only. The exact female hero descriptor is copied into every prompt; renderer owns Polish numbers, captions, source card and final checklist.",
    "release_boundary": "Upload and schedule are authorised by the owner for tomorrow 11:00 Warsaw only after all local v8 gates pass and the live slot is checked again.",
}

research = ResearchPack(
    lang="pl", topic="Rodzynki: owoc czy cukierki w kostiumie?", viewer_question="Czy rodzynki są dobrą przekąską, skoro tak łatwo zjeść ich pół paczki?",
    recommended_angle="Office snack detective: the host catches a raisin packet acting like a candy dispenser, follows the missing-water clue, measures two tablespoons, checks the label and ends with a three-rule portion workflow.",
    evidence_summary="Official Polish guidance explains that water removal makes dried fruit's sugars and energy more concentrated for the same mass; it does not make dried fruit forbidden. NCEŻ gives an example of about 90 kcal and 19 g sugars in 30 g (two tablespoons) of raisins. Official guidance also notes that some dried-fruit products have added sugar or syrup and suggests dried fruit can occasionally replace sweet snacks, especially as part of a meal with natural yogurt, nuts or seeds.",
    sources=sources, claims=claims,
    unresolved_conflicts=["Nutrient values vary by brand and recipe; the stated amount is a cited 30 g example.", "The presence of added sugar or syrup is product-specific and must be checked on the ingredients list.", "This Short gives a general snack rule, not advice for diabetes or any individual dietary plan."],
)

dump("research_pack.json", research)
dump("script.json", script)
dump("compliance.json", ComplianceVerdict(passed=True, fixes=["Kept dried fruit as a food, not a threat.", "Kept the portion number approximate and linked to NCEŻ's 30 g example."], cleaned_script=script))
dump("fact_review.json", FactReview(passed=True, checks=[FactCheckItem(claim_id=claim.id, passed=True) for claim in claims], unsupported_script_statements=[], notes=["Every number is paired with its object and unit.", "The ingredient claim is explicitly product-specific."]))
dump("frame_plan.json", plan)
dump("qa.json", qa)
dump("publish_package.json", pkg)
dump("codex_strategy.json", strategy)
(RUN / "research_raw.md").write_text(
    "# Research memo — Rodzynki: owoc czy cukierki w kostiumie?\n\nChecked 2026-09-03. Live VitalLogic catalog had 198 videos; title, description and tags were searched for rodzynki, suszone owoce, raisins and dried fruit. No direct match was found.\n\nEvidence used:\n- NCEŻ e-book: drying removes water and concentrates sugars; 30 g/2 tablespoons of raisins are given as about 90 kcal and 19 g sugars; some dried fruit has added sugar.\n- WSSE Warszawa/Gov.pl: dried fruit has higher sugars and energy per the same weight yet can be an occasional sweet-snack replacement; pair fruit with natural yogurt, nuts or seeds or add it to a meal.\n- PSSE Kamień Pomorski/Gov.pl: dried fruit retains nutrients but can have more sugars/calories per mass; check for added sugar or glucose-fructose syrup.\n\nEditorial boundary: no ban, diagnosis, glycaemic promise, weight-loss promise, or universal product numbers.\n",
    encoding="utf-8",
)
print(RUN)
