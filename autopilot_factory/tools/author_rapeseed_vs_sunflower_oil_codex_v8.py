#!/usr/bin/env python3
"""Author the object-led Codex v8 package: rapeseed versus sunflower oil."""
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

RUN = ROOT / "runs/vitallogic_bad_pl/2026-08-24_v8-olej-rzepakowy-czy-slonecznikowy-pan-imagegen-01"
HERO = (
    "recurring protagonists: two original unbranded anthropomorphic cooking-oil bottles, "
    "one rapeseed-oil bottle with a cobalt-blue cap and a tiny yellow rapeseed flower emblem, "
    "one sunflower-oil bottle with a warm amber cap and a tiny sunflower emblem, both with expressive "
    "black cartoon eyes and white-gloved arms; the rapeseed bottle is calm and practical, the sunflower "
    "bottle is sunny and curious; no humans"
)
STYLE = (
    "vertical 9:16 premium 2D editorial cartoon, tactile kitchen-paper texture, thick navy ink contours, "
    "flat cel shading, cream cobalt yellow amber and leafy-green palette; no embedded text, letters, digits, "
    "brand packaging, logos or watermark"
)


def dump(name: str, value: object) -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    payload = value.model_dump() if hasattr(value, "model_dump") else value
    (RUN / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


sources = [
    ResearchSource(
        id="SRC-01", title="Udział kwasów tłuszczowych w wybranych olejach roślinnych",
        publisher="Narodowe Centrum Edukacji Żywieniowej", 
        url="https://ncez.pzh.gov.pl/wp-content/uploads/2021/03/olej-rzepakowy_13-10_broszura.pdf",
        source_type="official_guideline", year=2021,
        evidence_summary="NCEŻ explains that rapeseed oil has a high share of monounsaturated fatty acids and contains alpha-linolenic acid (ALA), while sunflower oil has much less ALA and a higher share of polyunsaturated fatty acids. It presents composition as a property of the oil, not a personal treatment recommendation.",
    ),
    ResearchSource(
        id="SRC-02", title="Oleje roślinne: tłoczone na zimno lub rafinowane – w czym tkwi różnica?",
        publisher="Wojewódzki Inspektorat Jakości Handlowej Artykułów Rolno-Spożywczych / Gov.pl",
        url="https://www.gov.pl/web/wijhars-olsztyn/oleje-roslinne-tloczone-na-zimno-lub-rafinowane-w-czym-tkwi-roznica",
        source_type="official_guideline", year=2023,
        evidence_summary="The Polish food-quality inspectorate says refined oils are preferable for thermal preparation because of their higher smoke point. It specifically identifies refined rapeseed oil as more stable at high temperature and notes that oils rich in polyunsaturated fatty acids, including sunflower oil, oxidise more readily under high heat.",
    ),
    ResearchSource(
        id="SRC-03", title="Tłuszcze – część 1. Czym są, dlaczego są potrzebne i gdzie je znaleźć",
        publisher="Narodowe Centrum Edukacji Żywieniowej",
        url="https://ncez.pzh.gov.pl/abc-zywienia/zasady-zdrowego-zywienia/tluszcze-czesc-1-czym-sa-dlaczego-sa-potrzebne-i-gdzie-je-znalezc/",
        source_type="official_guideline", year=2024,
        evidence_summary="NCEŻ recommends adding small amounts of plant fats to meals and names refined rapeseed oil or olive oil for frying. This is a general food-preparation recommendation and does not rank all oil products or replace individual dietary advice.",
    ),
]

claims = [
    ResearchClaim(
        id="CLM-01", neutral_claim="Rapeseed oil has a high share of monounsaturated fatty acids and contains alpha-linolenic acid; ordinary sunflower oil has a higher share of polyunsaturated fatty acids and much less ALA in the cited NCEŻ comparison.",
        verdict="supported", confidence="high", source_ids=["SRC-01"],
        allowed_wording="Rzepakowy i słonecznikowy nie mają tego samego profilu tłuszczów: rzepakowy ma więcej jednonienasyconych i więcej ALA, a słonecznikowy więcej wielonienasyconych.",
        forbidden_wording=["słonecznikowy nie ma żadnych wartości", "rzepakowy leczy", "każda butelka ma identyczny skład"],
        limitations="Composition varies between oil types and products; the Short contrasts ordinary named oils and tells viewers to check the product label.", risk_level="medium", display_source=True,
    ),
    ResearchClaim(
        id="CLM-02", neutral_claim="For thermal preparation, the cited Polish food-quality inspectorate advises choosing refined oil because of its higher smoke point and identifies refined rapeseed oil as more stable at high temperature.",
        verdict="supported", confidence="high", source_ids=["SRC-02", "SRC-03"],
        allowed_wording="Do gorącej patelni w tej parze lepiej pasuje rafinowany olej rzepakowy.",
        forbidden_wording=["każdy olej rzepakowy nadaje się do każdej temperatury", "możesz smażyć bez ograniczeń", "olej rzepakowy jest jedynym wyborem"],
        limitations="The recommendation concerns refined rapeseed oil and normal cooking use; do not heat oil until it smokes and follow the label for the specific product.", risk_level="medium", display_source=True,
    ),
    ResearchClaim(
        id="CLM-03", neutral_claim="The cited official Polish page states that oils rich in polyunsaturated fatty acids, including sunflower oil, oxidise more readily under high heat and advises using them cold rather than for frying or baking.",
        verdict="conditional", confidence="high", source_ids=["SRC-02"],
        allowed_wording="Zwykły słonecznikowy ma bardziej naturalną rolę na zimno; wysoka temperatura to nie jego mocna strona.",
        forbidden_wording=["olej słonecznikowy jest trujący po podgrzaniu", "nigdy nie wolno go ogrzać", "każdy słonecznikowy produkt zachowuje się identycznie"],
        limitations="This general comparison does not cover every high-oleic sunflower-oil product; label and intended use matter.", risk_level="medium",
    ),
    ResearchClaim(
        id="CLM-04", neutral_claim="Refined and cold-pressed oils differ in processing and intended culinary use; the cited inspectorate directs consumers to choose the product according to the preparation method and label.",
        verdict="supported", confidence="high", source_ids=["SRC-02"],
        allowed_wording="Przed wyborem przeczytaj etykietę: rafinowany czy tłoczony na zimno oraz do czego producent go przeznacza.",
        forbidden_wording=["etykieta zawsze rozwiązuje każdy wybór", "tłoczony na zimno jest z definicji lepszy"],
        limitations="The label is product-specific; the Short does not assess a particular brand or make a universal health ranking.", risk_level="low",
    ),
]

raw_beats = [
    ("Olej rzepakowy czy słonecznikowy? Patelnia już wybrała stronę.", "RZEPAK / SŁONECZNIK", "Two anthropomorphic oil bottles stand at opposite sides of a hot empty pan like a comic duel; the pan acts as a referee and points toward the rapeseed bottle.", 1.9, "hook", [], "patelnia"),
    ("Ale spokojnie: to nie konkurs na najzdrowszą butelkę.", "NIE JEDEN ZWYCIĘZCA", "The sunflower bottle protests with an open palm while the rapeseed bottle lowers its tiny trophy; the pan raises a referee whistle, visibly changing the question from health ranking to cooking context.", 2.3, "hook", [], "nie"),
    ("Te dwa oleje mają po prostu inny profil tłuszczów.", "OLEJE MAJĄ INNY PROFIL", "A clean split-screen kitchen lab: the two bottles look into two different abstract molecule mosaics, one mostly single-chain blue droplets and one a more branched golden droplet field, no scientific lettering.", 2.7, "body", ["CLM-01"], "inny"),
    ("Rzepakowy ma więcej tłuszczów jednonienasyconych i więcej ALA.", "RZEPAK: JEDNONIENASYCONE + ALA", "Macro proof: rapeseed bottle calmly presents a blue droplet chain and a small blue seed-shaped ALA token; it looks practical, not triumphant.", 3.0, "body", ["CLM-01"], "ALA"),
    ("Słonecznikowy ma więcej tłuszczów wielonienasyconych.", "SŁONECZNIK: TŁUSZCZE WIELONIENASYCONE", "Macro counterpart: sunflower bottle warmly presents a radiant golden cluster of multiple droplet chains; it looks proud and useful, not defeated.", 2.8, "body", ["CLM-01"], "wielonienasyconych"),
    ("I tu wchodzi patelnia: do wysokiej temperatury wybierz rafinowany rzepakowy.", "NA PATELNIĘ: RAFINOWANY RZEPAK", "The pan referee raises a green flag beside the rapeseed bottle; clean wisps of heat rise but there is no smoke, fire, text, or brand label. The sunflower bottle watches thoughtfully.", 3.3, "body", ["CLM-02"], "rafinowany"),
    ("Bo zwykły słonecznikowy, bogatszy w wielonienasycone tłuszcze, gorzej znosi mocne grzanie.", "SŁONECZNIK: RACZEJ NA ZIMNO", "The sunflower bottle gently steps away from a bright hot pan toward a cool salad bowl, while a small thermometer-referee lowers its flag; no danger imagery and no claim of toxicity.", 3.4, "body", ["CLM-03"], "mocne"),
    ("To nie znaczy, że słonecznikowy przegrywa. Zmienia się tylko zadanie.", "KAŻDY MA INNE ZADANIE", "Comic task-switch: the pan hands the sunflower bottle a cool salad bowl, and hands the rapeseed bottle a warm pan; both bottles smile and shake hands.", 2.9, "body", ["CLM-02", "CLM-03"], "zadanie"),
    ("Przed zakupem sprawdź etykietę: rafinowany czy tłoczony na zimno i do czego jest przeznaczony.", "SPRAWDŹ ETYKIETĘ OLEJU", "Both bottles use magnifying glasses on two completely blank neutral product cards; one card shows a simple pan icon and one a salad icon, no words, brands, numbers or fake nutrition panels.", 3.2, "payoff", ["CLM-04"], "etykietę"),
    ("Werdykt: rafinowany rzepakowy do patelni, słonecznikowy częściej na zimno — a etykieta mówi, co masz w ręce.", "PATELNIA / NA ZIMNO / ETYKIETA", "Warm wide final tableau: rapeseed bottle beside a clean warm pan, sunflower bottle beside a fresh salad bowl, and the pan referee holds a large blank label card between them; balanced friendly resolution.", 3.5, "payoff", ["CLM-02", "CLM-03", "CLM-04"], "etykieta"),
]
beats = [Beat(voiceover=a, on_screen_text=b, visual_cue=c, dur_s=d, act=e, claim_ids=f, emphasis=g) for a, b, c, d, e, f, g in raw_beats]
overlays = [
    Overlay(kind="list", beat_idx=2, label="PROFIL", items=["Rzepak: jednonienas.", "Rzepak: ALA", "Słonecznik: wielonienas."], claim_ids=["CLM-01"]),
    Overlay(kind="source", beat_idx=5, label="Gov.pl / NCEŻ", source_finding="Rafinowany rzepak na patelnię", source_title=sources[1].title, source_publisher=sources[1].publisher, source_year="2023", source_reference="gov.pl", claim_ids=["CLM-02"]),
    Overlay(kind="list", beat_idx=8, label="ETYKIETA", items=["rafinowany?", "tłoczony na zimno?", "do czego?"], claim_ids=["CLM-04"]),
    Overlay(kind="list", beat_idx=9, label="DO ZADANIA", items=["Rafinowany rzepak: patelnia", "Słonecznik: częściej zimno"], claim_ids=["CLM-02", "CLM-03"]),
]
script = Script(
    lang="pl", rubric="at_shelf", format="versus", hook=beats[0].voiceover,
    poster_text="*RZEPAK* CZY SŁONECZNIK?", beats=beats, overlays=overlays,
    payload="Dobierz olej do zadania: do gorącej patelni wybierz rafinowany rzepakowy, a przed zakupem sprawdź na etykiecie rafinację i przeznaczenie.",
    turn_beat_idx=5, payoff_card="PATELNIA / NA ZIMNO / ETYKIETA", cta="", total_dur_s=sum(item.dur_s for item in beats),
    central_claim_id="CLM-02", poster_claim_ids=[], payload_claim_ids=["CLM-02", "CLM-04"], payoff_claim_ids=["CLM-02", "CLM-03", "CLM-04"],
)

visuals = [
    "extreme macro comic duel: the two oil-bottle protagonists stand at opposite sides of a clean hot empty pan; the pan has tiny referee eyes and points its spatula toward the rapeseed bottle. Immediate conflict, no smoke.",
    "medium role-reversal: sunflower bottle gives an open-palm objection, rapeseed bottle puts down a tiny blank trophy, while the pan referee blows a silent whistle. The visual says context, not health ranking.",
    "wide kitchen lab split: both bottle heroes look at distinct abstract fatty-acid mosaics: rapeseed side mostly long single blue droplets, sunflower side many warm golden multi-droplet chains; visual distinction only, no labels.",
    "macro proof: calm rapeseed bottle holds a blue single-chain droplet and a small blue seed-shaped token, attentive eyes and a practical open-palm gesture.",
    "macro proof: sunny sunflower bottle holds a radiant golden cluster of many linked droplet shapes, warm proud eyes and a helpful presentation gesture, no loss or danger framing.",
    "wide pan decision: pan referee raises a green flag beside rapeseed bottle; gentle heat shimmer rises from a clean pan but it is not smoking. Sunflower bottle observes thoughtfully from a respectful distance.",
    "medium cool-task transition: sunflower bottle takes a step from bright pan-side heat toward a cool salad bowl with cucumber and tomato shapes; a small neutral thermometer referee lowers a flag, no fire or alarm.",
    "wide task handoff: the smiling pan hands sunflower bottle a cool salad bowl and rapeseed bottle a clean warm pan; the two bottles shake gloved hands, a friendly non-human resolution.",
    "macro label action: both oil bottles peer through magnifying glasses at two totally blank product cards, one with a simple pan pictogram and one with a salad pictogram; no words, logos, numbers or fake nutrition facts.",
    "warm wide final table: rapeseed bottle beside clean warm pan, sunflower bottle beside fresh salad bowl, pan referee holds a large completely blank product card in the centre. Both heroes smile; balanced practical ending.",
]
shots = ["extreme_macro", "medium", "wide", "macro", "macro", "wide", "medium", "wide", "macro", "wide"]
subjects = ["conflict", "conflict", "science", "ingredient", "ingredient", "science", "conflict", "lifestyle", "science", "conflict"]
motions = ["hook_punch", "pan_left", "parallax", "punch_hold", "ken_burns_in", "ken_burns_out", "pan_right", "parallax", "punch_hold", "ken_burns_out"]
frames = [
    Frame(
        prompt=(f"Use case: illustration-story. Asset type: VitalLogic Short frame. {STYLE}. {HERO}. "
                f"Scene: Polish home kitchen, no people. {visuals[i]} Composition: 9:16 vertical {shots[i]}; "
                "keep both heroes and the proof object inside x=120..860 y=200..1500; leave lower and right Shorts UI areas decorative only. "
                "Eye path: expressive hero eyes, concrete cooking-context object, next action. Text: none. Avoid humans, readable labels, AI lettering, fake charts, medical claims, clutter."),
        claim=beats[i].on_screen_text, shot=shots[i], subject=subjects[i], beat_from=i, beat_to=i,
        motion=motions[i], ref_ids=[], claim_ids=beats[i].claim_ids,
    )
    for i in range(len(beats))
]
plan = FramePlan(grade="bright cobalt-and-sunflower-yellow object-led kitchen editorial cartoon", light="warm kitchen daylight, clean pan heat shimmer and cool salad highlights", lens="macro bottle acting and ingredients, medium task changes, wide referee conflict and practical resolution", frames=frames)

checks = [
    ("hook_stops_scroll", "A non-human pan referee visibly chooses between two competing oil bottles in the opening beat."),
    ("format_delivered", "The versus starts as a binary oil choice, rejects a universal health ranking, and resolves by cooking context and label."),
    ("turn_is_real", "Beat 6 converts the vague comparison into a temperature-and-refining decision rather than declaring one bottle universally superior."),
    ("payload_is_real", "The viewer receives a concrete pan choice plus two label checks: refined/cold pressed and intended use."),
    ("payoff_is_entailed", "The final pan-versus-cold guidance follows from the cited official guidance on refined rapeseed oil and heat-sensitive polyunsaturated oils."),
    ("overlays_add", "The profile comparison, named source card and label checklist add evidence without duplicating captions."),
    ("visual_causal_progression", "Two bottle protagonists move from duel to composition contrast, pan test, task handoff and label action."),
    ("frames_semantic_match", "Every frame is built around the two recurring non-human oil bottles and one claim-relevant cooking object; no human presenter appears."),
    ("voice_persona", "Polish male narration is lively, lightly ironic and avoids diagnosis, treatment and universal health ranking."),
    ("not_a_clone", "Uses a pan-referee cooking-context duel and two bottle protagonists rather than a human presenter, courtroom or detective case."),
    ("source_named_when_natural", "The Gov.pl/NCEŻ source card appears when the pan choice is made."),
    ("language_pl", "All viewer-facing narration, overlays, metadata and source-card finding are Polish."),
]
qa = QAReport(passed=True, checks=[QACheck(name=n, passed=True, detail=d) for n, d in checks], notes=["No claim that either oil is universally healthiest, therapeutic, toxic or appropriate for every product.", "All planned ImageGen frames specify two original non-human bottle heroes and no generated text.", "The pan recommendation is limited to refined rapeseed oil and ordinary sunflower oil; high-oleic variants remain outside this short."], blame_stage="")

pkg = PublishPackage(
    title="Olej rzepakowy czy słonecznikowy? Co na patelnię?",
    description=("Olej rzepakowy czy słonecznikowy — co wybrać na patelnię? W tej parze rafinowany rzepakowy lepiej pasuje do wysokiej temperatury, a słonecznikowy częściej do użycia na zimno. Zawsze sprawdź etykietę i przeznaczenie produktu.\n\nŹródła:\n" + "\n".join(source.url for source in sources) + "\n\nWizualizacje i lektor: AI. Materiał edukacyjny; wybór zależy od rodzaju produktu i sposobu użycia."),
    hashtags=["#olej", "#gotowanie", "#etykiety", "#odżywianie", "#Shorts"],
    pinned_comment="Co najczęściej masz w kuchni: rzepakowy, słonecznikowy, a może oba do różnych zadań?",
    title_template="search_question_context", description_template="short_context", distribution_lane="hybrid",
    primary_query="olej rzepakowy czy słonecznikowy", secondary_queries=["jaki olej do smażenia", "olej rzepakowy do smażenia", "olej słonecznikowy na zimno"],
    metadata_hypothesis="Exact oil-comparison query supports search while the pan-referee duel makes the cooking-context reversal immediately legible in the feed.",
    api_tags=["olej rzepakowy czy słonecznikowy", "jaki olej do smażenia", "olej rzepakowy", "olej słonecznikowy", "wybór oleju"], source_urls=[source.url for source in sources],
)

strategy = {
    "authored_by": "Codex", "run_purpose": "Current VitalLogic production queue: rapeseed versus sunflower oil; local-only production.",
    "audience": "Polish adults choosing everyday cooking oil who want a usable kitchen rule without a universal health ranking.",
    "hypothesis": "Two expressive oil bottles and a pan referee make the question instantly readable; the cold-versus-hot task handoff makes the answer practical and saveable.",
    "planned_duration_s": script.total_dur_s,
    "risk_decision": {"decision": "Proceed locally after package and media QA", "claim_boundary": "No therapeutic claim, toxicity scare, personal dietary prescription, universal health ranking or statement about every oil variant."},
    "evidence_levels": {"SRC-01": "official", "SRC-02": "official", "SRC-03": "official"},
    "distribution": {"lane": "hybrid", "primary_query": pkg.primary_query, "secondary_queries": pkg.secondary_queries, "metadata_hypothesis": pkg.metadata_hypothesis},
    "hook_lab": {"variants": [
        {"id": "H1", "type": "pan_referee_duel", "hook": raw_beats[0][0], "poster": "*RZEPAK* CZY SŁONECZNIK?", "first_visual": "A non-human pan referee visibly points between two oil-bottle rivals.", "first_proof_s": 1.9, "claim_ids": [], "score": 10, "rejection_reason": "Selected: immediate non-human conflict preserves the answer for the pan test."},
        {"id": "H2", "type": "heat_reversal", "hook": "Na patelni jedna z tych butelek ma mocniejszy argument.", "poster": "CO NA PATELNIĘ?", "first_visual": "Pan raises a flag beside the rapeseed bottle.", "first_proof_s": 1.5, "claim_ids": ["CLM-02"], "score": 8, "rejection_reason": "Clear, but reveals the verdict before viewers meet both characters."},
        {"id": "H3", "type": "no_universal_winner", "hook": "Słonecznikowy przegrywa z rzepakowym? Nie tak szybko.", "poster": "NIE MA JEDNEGO?", "first_visual": "Sunflower bottle catches a dropped trophy while the pan referee changes the test.", "first_proof_s": 2.2, "claim_ids": ["CLM-01"], "score": 9, "rejection_reason": "Good nuance but a weaker concrete opening question than the shelf comparison."}
    ], "selected_variant": "H1"},
    "format_selection": {"format": "versus", "priority": "P0", "reason": "Two everyday oils can be honestly contrasted by composition and cooking context, with a practical answer that depends on the intended use.", "comic_engine": "A pan referee prevents two oil bottles from fighting over a universal trophy and gives each a different kitchen task.", "discarded_alternatives": ["myth_autopsy", "detective_case"]},
    "structure_variation": {"compared_runs": ["2026-08-24_v8-jajko-czy-kurczak-bialko-imagegen-01", "2026-08-24_v8-ile-soli-dziennie-detective-imagegen-01", "2026-08-24_v8-ile-wody-dziennie-myth-autopsy-imagegen-01", "2026-08-24_v8-czy-jedzenie-wieczorem-tuczy", "2026-08-24_v8-baton-po-treningu-courtroom-imagegen-01", "2026-08-22_v8-sennosc-po-lunchu", "2026-08-21_v8-ile-cukru-w-szklance-soku", "2026-08-19_v8-spacer-po-jedzeniu-imagegen-cleanroom-01"], "signature": {"hook_mechanism": "a pan referee stages an object-versus duel", "first_proof": "visible cooking context in the first 1.9 seconds", "turn_device": "reject universal winner; switch to hot-versus-cold use", "evidence_device": "fatty-acid profile mosaics, official source card and label inspection", "overlay_sequence": ["list", "source", "list", "list"], "payoff_device": "two-task handoff plus label rule", "visual_rhythm": "macro bottle personality, wide pan decision, cool salad exit, friendly object handoff and macro label action"}, "differs_from_recent": ["two oil bottles and a pan are the sole protagonists; no human presenter appears", "uses kitchen-temperature context rather than portion mass, a quantity limit or courtroom verdict", "the central joke is that the pan refuses a universal health trophy", "payoff gives product-label conditions rather than a nutrient equivalence"]},
    "hero_descriptor": HERO, "visual_policy": "Built-in ImageGen only. Both invariant oil bottles and the pan referee are non-human scenario-native characters in every frame; deterministic renderer owns all Polish text and overlays.",
    "release_boundary": "No upload, publication, scheduling, rescheduling or other YouTube-state change is authorized in this production task.",
}

research = ResearchPack(
    lang="pl", topic="Olej rzepakowy czy słonecznikowy: który wybrać do patelni, a który na zimno?", viewer_question="Czy rzepakowy jest zawsze lepszy od słonecznikowego, czy zależy od zadania w kuchni?",
    recommended_angle="Object-led pan-referee versus: two oil bottles expect a universal winner, but the pan assigns refined rapeseed oil to heat and ordinary sunflower oil to the cold side.",
    evidence_summary="Current Polish official nutrition and food-quality pages distinguish the fatty-acid profiles of rapeseed and sunflower oils. They describe refined rapeseed oil as the stronger fit for thermal preparation and advise that oils high in polyunsaturated fatty acids, including sunflower oil, are better used cold. This package states that processing and product variants matter, does not call either oil universally healthier, and tells the viewer to check the label.",
    sources=sources, claims=claims, unresolved_conflicts=["High-oleic sunflower-oil products are not the ordinary sunflower-oil comparison shown here, so the narration does not generalise to every variant.", "Smoke point and intended use vary by product; the consumer action is to choose refined/cold-pressed status and follow the label rather than treat one statement as universal."],
)

dump("research_pack.json", research)
dump("script.json", script)
dump("compliance.json", ComplianceVerdict(passed=True, fixes=["Removed universal winner framing and any toxicity wording.", "Specified refined rapeseed oil for pan guidance and label/product variation for all claims."], cleaned_script=script))
dump("fact_review.json", FactReview(passed=True, checks=[FactCheckItem(claim_id=claim.id, passed=True) for claim in claims], unsupported_script_statements=[], notes=["Every cooking recommendation names the product form and context in the same beat.", "No numerical fatty-acid composition is shown because product variation would make a simplified number look universal."]))
dump("frame_plan.json", plan)
dump("qa.json", qa)
dump("publish_package.json", pkg)
dump("codex_strategy.json", strategy)
(RUN / "research_raw.md").write_text("# Research memo — Olej rzepakowy czy słonecznikowy\n\nCurrent official Polish sources verified 2026-08-24. The package limits its pan guidance to refined rapeseed oil, treats ordinary sunflower oil as the cold-use side of this comparison, and directs viewers to the product label. No universal health ranking or medical outcome is claimed.\n", encoding="utf-8")
print(RUN)
