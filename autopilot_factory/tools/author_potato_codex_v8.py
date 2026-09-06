#!/usr/bin/env python3
"""Author the Codex v8 package for the potato myth Short."""
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

RUN = ROOT / "runs/vitallogic_bad_pl/2026-09-03_v8-ziemniaki-tucza"
HERO = (
    "the recurring main character is an original adult Polish woman, 29 years old, with a short chestnut-brown bob, "
    "warm brown eyes, a small round blue eyeglass frame, a cobalt-blue cardigan over a warm-cream T-shirt, "
    "high-waisted forest-green trousers, and mustard-yellow sneakers; ordinary friendly office-worker silhouette, "
    "no logos, no franchise resemblance, no animal ears, no fantasy costume"
)
STYLE = (
    "vertical 9:16 premium 2D hand-drawn editorial cartoon, clean bright Polish kitchen and small comic courtroom, "
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
        id="SRC-01", title="Czy ziemniaki tuczą?", publisher="Narodowe Centrum Edukacji Żywieniowej",
        url="https://ncez.pzh.gov.pl/abc-zywienia/czy-ziemniaki-tucza/", source_type="official_guideline", year=2018,
        evidence_summary="NCEŻ explains that 100 g of potatoes contains about 73 kcal, while preparation method and additions can substantially change the energy of the final dish. It recommends boiling or baking and limiting large amounts of fat, creamy sauces and cracklings.",
    ),
    ResearchSource(
        id="SRC-02", title="Jesień na talerzu-ziemniak", publisher="Powiatowa Stacja Sanitarno-Epidemiologiczna w Choszcznie / Gov.pl",
        url="https://www.gov.pl/web/psse-choszczno/jesien-na-talerzu-ziemniak", source_type="official_guideline", year=2023,
        evidence_summary="The official Polish sanitary-inspection page reports about 73 kcal per 100 g of boiled potatoes and about 280 kcal per 100 g of fries, presenting the values as a comparison of preparation forms.",
    ),
    ResearchSource(
        id="SRC-03", title="Czy można obniżyć zawartość akryloamidu w żywności? produkty ziemniaczane", publisher="Narodowe Centrum Edukacji Żywieniowej",
        url="https://ncez.pzh.gov.pl/abc-zywienia/czy-mozna-obnizyc-zawartosc-akryloamidu-w-zywnosci-produkty-ziemniaczane/", source_type="official_guideline", year=2018,
        evidence_summary="NCEŻ states that acrylamide formation in potato products depends on time, temperature and colour; more heavily fried or baked products are darker and contain more acrylamide. It advises aiming for a golden rather than very dark colour and following product instructions.",
    ),
    ResearchSource(
        id="SRC-04", title="Baza danych – wersja skrócona", publisher="Narodowy Instytut Zdrowia Publicznego PZH – PIB",
        url="https://www.pzh.gov.pl/uslugi/tabele-wartosci-odzywczej-produktow/baza-danych-wersja-skrocona/", source_type="official_database", year=2017,
        evidence_summary="The PZH food-composition database describes energy and nutrient values per 100 g edible portion and provides the official Polish reference context for food-composition comparisons.",
    ),
]

claims = [
    ResearchClaim(
        id="CLM-01", neutral_claim="The cited Polish official sources report about 73 kcal in 100 g of boiled potatoes.", verdict="supported", confidence="high", source_ids=["SRC-01", "SRC-02"],
        allowed_wording="Sto gramów gotowanych ziemniaków to około 73 kilokalorie.", forbidden_wording=["każdy ziemniak ma dokładnie 73 kcal", "ziemniaki nie mają kalorii"],
        limitations="The value is an approximate reference for boiled potatoes per 100 g, not a universal value for every dish or portion.", risk_level="low", display_source=True,
    ),
    ResearchClaim(
        id="CLM-02", neutral_claim="The cited Gov.pl page compares about 73 kcal per 100 g for boiled potatoes with about 280 kcal per 100 g for fries.", verdict="supported", confidence="high", source_ids=["SRC-02"],
        allowed_wording="W tej porcji frytki mają około 280 kilokalorii na sto gramów.", forbidden_wording=["każde frytki mają dokładnie 280 kcal", "frytki są zakazane"],
        limitations="The comparison is between reference preparation forms; recipes, serving sizes and products vary.", risk_level="low", display_source=False,
    ),
    ResearchClaim(
        id="CLM-03", neutral_claim="NCEŻ states that 10 g of oil adds about 88 kcal and that preparation method and fatty additions change the final dish energy.", verdict="supported", confidence="high", source_ids=["SRC-01"],
        allowed_wording="Dziesięć gramów oleju dodaje około 88 kilokalorii; liczą się też dodatki.", forbidden_wording=["olej zawsze tuczy", "każdy dodatkowy gram działa tak samo w każdym przepisie"],
        limitations="The arithmetic refers to the cited energy value for oil; the whole dish depends on all ingredients and their amounts.", risk_level="low", display_source=False,
    ),
    ResearchClaim(
        id="CLM-04", neutral_claim="For potato products, darker and more heavily fried or baked food tends to contain more acrylamide than golden food under the cited NCEŻ guidance.", verdict="conditional", confidence="high", source_ids=["SRC-03"],
        allowed_wording="Przy frytkach celuj w kolor złocisty, nie mocno przypieczony.", forbidden_wording=["złoty kolor usuwa całe ryzyko", "ciemna frytka jest trująca"],
        limitations="Colour is a practical visual indicator, not a measurement of acrylamide in an individual piece; product instructions and cooking conditions matter.", risk_level="medium", display_source=False,
    ),
    ResearchClaim(
        id="CLM-05", neutral_claim="NCEŻ advises boiling or baking potatoes and avoiding large amounts of butter, cream, sauces and cracklings when aiming for a less energy-dense dish.", verdict="supported", confidence="high", source_ids=["SRC-01"],
        allowed_wording="Gotuj albo piecz, odmierzaj tłuszcz i patrz na całą porcję, nie na samą bulwę.", forbidden_wording=["gotowanie gwarantuje odchudzanie", "ziemniaki trzeba całkiem wykluczyć"],
        limitations="This is a general cooking rule, not a personalised diet or weight-loss prescription.", risk_level="low", display_source=True,
    ),
]

raw_beats = [
    ("Ziemniak na ławie oskarżonych: tuczy czy został wrobiony?", "ZIEMNIAK NA SĄDZIE", "The girl host dramatically places one ordinary potato on a tiny witness stand while a cartoon frying pan points an accusing spatula at it; immediate comic courtroom conflict.", 2.3, "hook", [], "oskarżonych"),
    ("Wszyscy patrzą na bulwę, a patelnia udaje niewinną.", "PATELNIA MA ALIBI", "The same girl host squints suspiciously at the smug frying pan hiding behind a napkin while the potato looks offended; she points from potato to pan with raised eyebrow.", 2.2, "hook", [], "niewinną"),
    ("Sto gramów gotowanych ziemniaków to około 73 kilokalorie.", "GOTOWANE: 73 KCAL / 100 G", "The girl host weighs a boiled potato on a clean kitchen scale; a simple visual marker shows a small light portion while she looks surprised and points down at the scale.", 2.8, "body", ["CLM-01"], "73"),
    ("Ten sam ziemniak po frytkowej metamorfozie ma około 280 kilokalorii na sto gramów.", "FRYTKI: OKOŁO 280 KCAL", "Macro split scene: the girl host holds a boiled potato in one hand and a small basket of golden fries in the other, eyes wide at the dramatic size contrast; a neutral comparison board has no text.", 3.2, "body", ["CLM-02"], "280"),
    ("Dlaczego? Dziesięć gramów oleju dodaje około 88 kilokalorii.", "OLEJ: +88 KCAL", "The girl host catches a tiny measured spoon of oil pouring into the frying pan, mouth open in comic realization; the potato peeks from behind the pan, no smoke or danger.", 2.7, "body", ["CLM-03"], "88"),
    ("Czyli problemem często nie jest sam ziemniak, tylko tłuszcz i dodatki.", "WINNY: TŁUSZCZ I DODATKI", "The girl host turns from the potato toward a butter pat, creamy sauce jug and frying pan arranged like three guilty suspects; she holds a small detective notebook and gives the potato an apologetic glance.", 2.9, "body", ["CLM-03"], "dodatki"),
    ("NCEŻ pokazuje, że sposób przygotowania potrafi zmienić całe danie.", "SPOSÓB ZMIENIA DANIE", "The girl host slides three serving plates across a kitchen counter: boiled potato, baked potato and a small fried serving; she gestures along the progression with a calm explanatory smile.", 2.9, "body", ["CLM-05"], "sposób"),
    ("Przy frytkach patrz też na kolor: złocisty, nie spalony.", "ZŁOCISTE, NIE MOCNO PRZYPIECZONE", "Extreme macro: the girl host holds one golden fry up to daylight and gently moves a very dark fry aside with a careful grimace; the visual contrast is clear but not alarming.", 2.7, "body", ["CLM-04"], "złocisty"),
    ("Werdykt: bulwa nie jest złoczyńcą. Liczą się sposób, olej i porcja.", "BULWA UNIEWINNIONA", "The girl host removes the potato from the tiny witness stand and gives it a friendly high-five; the frying pan receives a comical invoice for oil and sauce, with no readable text.", 2.6, "payoff", ["CLM-03", "CLM-05"], "porcja"),
    ("Ziemniak wychodzi z sądu, a patelnia dostaje rachunek za dodatki.", "GOTUJ / PIECZ / ODMIERZAJ TŁUSZCZ", "Warm wide final kitchen tableau: the girl host carries the potato toward a simple plate, the pan stands beside a measured spoon of oil, and a golden fry sits in the foreground; relieved smile and practical ending.", 2.5, "payoff", ["CLM-04", "CLM-05"], "rachunek"),
]

beats = [Beat(voiceover=a, on_screen_text=b, visual_cue=c, dur_s=d, act=e, claim_ids=f, emphasis=g) for a, b, c, d, e, f, g in raw_beats]
overlays = [
    Overlay(kind="callout", beat_idx=2, value="73 kcal", claim_ids=["CLM-01"]),
    Overlay(kind="versus", beat_idx=3, label="Gotowane", value="73 kcal", label_b="Frytki", value_b="280 kcal", winner="b", claim_ids=["CLM-01", "CLM-02"]),
    Overlay(kind="callout", beat_idx=4, value="+88 kcal", claim_ids=["CLM-03"]),
    Overlay(kind="source", beat_idx=6, label="NCEŻ", source_finding="Sposób i dodatki zmieniają danie", source_title=sources[0].title, source_publisher=sources[0].publisher, source_year="2018", source_reference="ncez.pzh.gov.pl", claim_ids=["CLM-05"]),
    Overlay(kind="list", beat_idx=9, label="ŚCIĄGA", items=["+ gotuj albo piecz", "+ odmierzaj tłuszcz", "+ wybierz złocisty kolor"], claim_ids=["CLM-04", "CLM-05"]),
]

script = Script(
    lang="pl", rubric="really_true", format="myth_autopsy", hook=beats[0].voiceover,
    poster_text="*ZIEMNIAK* TUCZY?", beats=beats, overlays=overlays,
    payload="Gotuj albo piecz ziemniaki, odmierzaj olej i oceniaj całą porcję, nie samą bulwę.",
    turn_beat_idx=4, payoff_card="BULWA NIE JEST WINNA: LICZY SIĘ SPOSÓB", cta="",
    total_dur_s=sum(item.dur_s for item in beats), central_claim_id="CLM-03",
    poster_claim_ids=[], payload_claim_ids=["CLM-03", "CLM-05"], payoff_claim_ids=["CLM-03", "CLM-05"],
)

visuals = [
    "wide comic courtroom in a Polish kitchen: the girl host places one ordinary potato on a tiny witness stand while a cartoon frying pan points an accusing spatula at it; the potato is the only object on trial, clear immediate conflict",
    "medium reaction: the girl host suspiciously points from the offended potato toward a smug frying pan hiding behind a napkin; expressive raised eyebrow, the pan tries to look innocent",
    "macro evidence: the girl host weighs a boiled potato on a clean kitchen scale; a simple blank marker board sits behind it, the scale and potato are sharpest, her surprised face guides the eye down",
    "wide split comparison: the girl host holds boiled potato on the left and a small basket of golden fries on the right, eyes wide at the contrast; a blank comparison board, no text or digits",
    "extreme macro action: a tiny measured spoon of oil pours into the frying pan; the girl host catches the action with comic realization, the potato peeks from behind the pan, clean daylight, no smoke",
    "medium detective tableau: butter pat, creamy sauce jug and frying pan stand like three guilty suspects while the girl host holds a small blank notebook and apologises to the potato with her gaze",
    "wide kitchen progression: the girl host slides boiled, baked and fried potato plates across the counter and gestures along them like a calm courtroom explanation; distinct preparation forms, no labels",
    "extreme macro colour check: the girl host holds one golden fry toward daylight and moves one very dark fry aside; readable colour contrast, careful grimace, no horror or alarm",
    "medium verdict: the girl host removes the potato from the witness stand and gives it a friendly high-five while the frying pan receives a blank invoice card for oil and sauce",
    "wide warm final kitchen: the girl host carries the potato toward a simple plate, measured spoon of oil beside a clean pan, a golden fry in the foreground; relieved practical smile",
]
shots = ["wide", "medium", "macro", "wide", "extreme_macro", "medium", "wide", "extreme_macro", "medium", "wide"]
subjects = ["conflict", "human", "science", "conflict", "ingredient", "conflict", "ingredient", "science", "human", "lifestyle"]
motions = ["hook_punch", "pan_left", "punch_hold", "pan_right", "ken_burns_in", "parallax", "pan_left", "punch_hold", "ken_burns_out", "ken_burns_out"]
frames = []
for i, (beat, visual, shot, subject, motion) in enumerate(zip(beats, visuals, shots, subjects, motions)):
    if i == 2:
        claim = "Gotowany ziemniak ma 73 kcal na 100 g."
    elif i == 3:
        claim = "Frytki mają około 280 kcal na 100 g."
    elif i == 4:
        claim = "Dziesięć gramów oleju dodaje około 88 kcal."
    else:
        claim = beat.on_screen_text
    frames.append(Frame(
        prompt=(f"Use case: illustration-story. Asset type: VitalLogic Polish Short frame. {STYLE}. {HERO}. "
                f"Scene: {visual}. Composition: vertical 9:16, {shot} shot; keep the girl, potato and evidence object inside x=120..860 y=200..1500, "
                "leave the lower band and far-right Shorts UI area as expendable kitchen background. Eye path: the girl's gaze and gesture lead to the single evidence object, then to the potato. "
                "Text in image: none. Avoid photorealism, random lettering, fake charts, brand packaging, watermarks, clutter and medical imagery."),
        claim=("Bulwa wychodzi z sądu uniewinniona." if i == 8 else claim), shot=shot, subject=subject, beat_from=i, beat_to=i, motion=motion, ref_ids=[], claim_ids=beat.claim_ids,
    ))
plan = FramePlan(
    grade="bright navy, leafy-green and warm-cream Polish kitchen editorial cartoon with expressive female host",
    light="warm daylight with clear evidence highlights; gentle courtroom spot in the hook and gold fry colour check",
    lens="wide courtroom conflict, medium acting, macro food evidence and extreme-macro oil/colour details",
    frames=frames,
)

checks = [
    ("hook_stops_scroll", "A girl host immediately puts a potato on trial while a frying pan points an accusing spatula."),
    ("format_delivered", "The myth-autopsy structure moves from accusation to calorie evidence, hidden oil, cooking method, colour limit and verdict."),
    ("turn_is_real", "The turn moves blame from the potato itself to oil and additions, changing the viewer's question."),
    ("payload_is_real", "The viewer gets a concrete cooking rule: boil or bake, measure oil and judge the whole portion."),
    ("payoff_is_entailed", "The verdict follows the cited official calorie comparison and NCEŻ preparation guidance."),
    ("overlays_add", "Three compact numeric comparisons, one source card and a final checklist add evidence without repeating full captions."),
    ("visual_causal_progression", "The visual arc progresses from trial, to scale, to fries, oil suspects, method progression, colour check and acquittal."),
    ("frames_semantic_match", "Every frame keeps the same female host and uses a potato, pan or preparation form tied to the spoken claim."),
    ("voice_persona", "Polish male narration is planned as bright, lively and lightly ironic, without diagnosis or weight-loss promises."),
    ("not_a_clone", "This is a girl-led courtroom myth autopsy with preparation-form evidence, distinct from recent label versus and sleep-study packages."),
    ("source_named_when_natural", "The NCEŻ source card appears when the preparation-method claim is introduced."),
    ("language_pl", "All viewer-facing narration, overlays, metadata and source finding are in Polish."),
]
qa = QAReport(passed=True, checks=[QACheck(name=n, passed=True, detail=d) for n, d in checks], notes=[
    "No claim says potatoes must be eliminated, guarantees weight loss, or treats one reference calorie value as universal.",
    "Acrylamide is framed as a conditional preparation signal; no toxicity scare is used.",
    "The main human character is the same original adult woman in every ImageGen prompt, with changing acting and shot scale.",
], blame_stage="")

pkg = PublishPackage(
    title="Czy ziemniaki tuczą? Patelnia ma alibi",
    description=(
        "Czy ziemniaki tuczą? Sama bulwa nie opowiada całej historii: 100 g gotowanych ziemniaków to około 73 kcal, a frytki w przywołanym porównaniu około 280 kcal na 100 g. Różnicę robią metoda przygotowania, olej i dodatki.\n\n"
        "Praktyczna ściąga: gotuj albo piecz, odmierzaj tłuszcz, a przy frytkach celuj w kolor złocisty, nie mocno przypieczony. Wizualizacje i lektor: AI. Materiał edukacyjny; nie zastępuje porady lekarza.\n\nŹródła:\n"
        + "\n".join(source.url for source in sources)
    ),
    hashtags=["#ziemniaki", "#frytki", "#odżywianie", "#gotowanie", "#zdrowie", "#Shorts"],
    pinned_comment="Jak najczęściej jesz ziemniaki: gotowane, pieczone czy w formie frytek?",
    title_template="question_plus_myth_reframe", description_template="short_context", distribution_lane="hybrid",
    primary_query="czy ziemniaki tuczą", secondary_queries=["ziemniaki kalorie", "czy frytki tuczą", "ziemniaki gotowane czy frytki"],
    metadata_hypothesis="A familiar Polish food myth plus a visible courtroom and concrete 73-versus-280 kcal comparison should improve feed comprehension while the exact question supports search.",
    api_tags=["czy ziemniaki tuczą", "ziemniaki kalorie", "frytki kalorie", "ziemniaki gotowane", "zdrowe gotowanie", "odżywianie"],
    source_urls=[source.url for source in sources],
)

strategy = {
    "authored_by": "Codex",
    "run_purpose": "Standalone local VitalLogic v8 production: potato myth autopsy with female main character; no YouTube mutation.",
    "audience": "Dorośli w Polsce, którzy jedzą ziemniaki i słyszeli, że sama bulwa tuczy; chcą prostego kuchennego wyjaśnienia bez dietetycznej wojny.",
    "hypothesis": "Dziewczyna stawiająca ziemniaka przed sądem da natychmiastowy konflikt, a porównanie 73 kcal gotowanych ziemniaków z około 280 kcal frytek pokaże, że widz powinien patrzeć na przygotowanie, olej i porcję.",
    "planned_duration_s": script.total_dur_s,
    "risk_decision": {"decision": "Proceed locally after v8 package check, visual frame approval, build, release gate and ffprobe.", "claim_boundary": "No weight-loss promise, personal diet, universal calorie value, elimination advice or acrylamide scare; values are reference comparisons per 100 g and the cooking rule is general."},
    "evidence_levels": {"SRC-01": "official", "SRC-02": "official", "SRC-03": "official", "SRC-04": "official_database"},
    "live_catalog_check": {"checked_at": "2026-09-03", "playlist_items": 197, "searched_fields": ["title", "description", "tags"], "searched_terms": ["ziemniaki tuczą", "ziemniaki kalorie", "frytki kalorie"], "matches": [], "nearby": ["Banan czy ziemniak? Potas po treningu ma znaczenie", "Opuchnięte kostki wieczorem? Ten błąd z solą i potasem to powoduje."], "decision": "Unique enough to proceed: nearby episodes concern potassium/edema, not the potato-versus-preparation myth or calorie comparison."},
    "distribution": {"lane": "hybrid", "primary_query": pkg.primary_query, "secondary_queries": pkg.secondary_queries, "metadata_hypothesis": pkg.metadata_hypothesis},
    "hook_lab": {"variants": [
        {"id": "H1", "type": "myth_courtroom", "hook": beats[0].voiceover, "poster": "*ZIEMNIAK* TUCZY?", "first_visual": "A girl host puts one potato on a tiny witness stand while a frying pan accuses it.", "first_proof_s": 2.3, "claim_ids": [], "score": 10, "rejection_reason": "Selected: immediate visual conflict, female lead and the myth is readable without sound."},
        {"id": "H2", "type": "number_contrast", "hook": "Gotowany ziemniak: 73. Frytki: około 280.", "poster": "73 CZY 280?", "first_visual": "Girl host holds boiled potato and fries at the same time over a scale.", "first_proof_s": 2.4, "claim_ids": ["CLM-01", "CLM-02"], "score": 8, "rejection_reason": "Strong evidence, but the opening gives away the reversal before the comic accusation."},
        {"id": "H3", "type": "hidden_suspect", "hook": "Ziemniak twierdzi, że jest niewinny. Patelnia milczy.", "poster": "KTO JEST WINNY?", "first_visual": "Potato gestures toward a frying pan hiding behind a napkin while girl host investigates.", "first_proof_s": 2.0, "claim_ids": [], "score": 9, "rejection_reason": "Very entertaining, but the exact viewer question is less explicit than H1."},
        {"id": "H4", "type": "colour_boundary", "hook": "Frytka może być złocista albo zbyt przypieczona.", "poster": "ZŁOCISTA CZY CIEMNA?", "first_visual": "Girl host compares one golden fry and one very dark fry under daylight.", "first_proof_s": 3.0, "claim_ids": ["CLM-04"], "score": 7, "rejection_reason": "Useful safety visual, but too narrow for the broader potato myth."}
    ], "selected_variant": "H1"},
    "format_selection": {"format": "myth_autopsy", "priority": "P0", "reason": "A familiar belief can be tested with a visible accused object, direct calorie evidence and a precise preparation-based verdict.", "comic_engine": "The girl host prosecutes the potato, but the frying pan and oil are slowly exposed as the more relevant suspects.", "discarded_alternatives": ["versus", "number_shock", "detective_case"]},
    "structure_variation": {"compared_runs": ["2026-09-01_v8-parowki-ile-miesa", "2026-09-01_v8-maslo-czy-margaryna", "2026-09-01_v8-sol-himalajska-czy-zwykla", "2026-09-01_v8-jogurt-owocowy-czy-naturalny", "2026-09-01_v8-ciemny-chleb-czy-jasny", "2026-08-31_v9-drzemka-kofeinowa-mikroeksperyment-normal-speed", "2026-08-30_v9-idealna-pozycja-biurko-office-case", "2026-08-29_v8-sen-replay-pamieci"], "signature": {"hook_mechanism": "female host puts a potato on trial while the frying pan accuses it", "first_proof": "73 kcal per 100 g boiled potato appears at beat 2", "turn_device": "the question shifts from the bulba to oil and preparation method", "evidence_device": "73-versus-280 kcal comparison, +88 kcal oil callout and colour boundary", "overlay_sequence": ["callout", "versus", "callout", "source", "list"], "payoff_device": "potato acquittal plus a three-part kitchen rule", "visual_rhythm": "wide courtroom, medium suspicion, macro scale, wide split, extreme oil detail, suspect lineup, method progression, colour macro, verdict and warm practical tableau"}, "differs_from_recent": ["female human lead is present in every frame, rather than object-only packaging protagonists", "myth-autopsy courtroom replaces the recent versus-heavy product comparisons", "the first proof is a household calorie comparison rather than an ingredient-label or research result", "the turn exposes preparation and oil, then uses a colour boundary before the payoff", "the ending is an acquittal with a practical kitchen rule, not a shopping label verdict"]},
    "series": {"series_id": "", "episode": 1, "followup_topics": []},
    "hero_descriptor": HERO,
    "visual_policy": "Built-in Codex ImageGen only. The exact female hero descriptor is copied into every prompt; renderer owns all Polish numbers, captions, source card and final checklist.",
    "release_boundary": "No upload, publication, scheduling, rescheduling or other YouTube-state change is authorized in this production task.",
}

research = ResearchPack(
    lang="pl", topic="Czy ziemniaki tuczą? Kalorie zależą od przygotowania", viewer_question="Czy sama bulwa tuczy, czy większą różnicę robią frytki, olej i dodatki?",
    recommended_angle="Myth-autopsy courtroom: a girl host prosecutes an ordinary potato, but the 73-versus-280 kcal comparison and the oil reveal move attention to preparation method, additions and portion.",
    evidence_summary="Polish official sources report about 73 kcal per 100 g of boiled potatoes and about 280 kcal per 100 g of fries in a reference comparison. NCEŻ states that 10 g of oil adds about 88 kcal, recommends boiling or baking with restrained fatty additions, and advises aiming for a golden rather than very dark colour for potato products because darker, more heavily cooked products tend to contain more acrylamide. This package uses reference values, not a universal calorie verdict or personal weight-loss advice.",
    sources=sources, claims=claims,
    unresolved_conflicts=["The calorie values are reference values per 100 g and vary with recipe, product and portion.", "Colour is only a practical visual cue for cooking intensity, not a measurement of acrylamide in an individual fry.", "This Short does not assess a personal diet or make a weight-loss promise."],
)

dump("research_pack.json", research)
dump("script.json", script)
dump("compliance.json", ComplianceVerdict(passed=True, fixes=["Kept all calorie values approximate and tied to preparation form.", "Limited the practical advice to general cooking choices and removed any weight-loss promise."], cleaned_script=script))
dump("fact_review.json", FactReview(passed=True, checks=[FactCheckItem(claim_id=claim.id, passed=True) for claim in claims], unsupported_script_statements=[], notes=["Every number names its object and unit in the same beat.", "The acrylamide statement is conditional and sourced only to the official NCEŻ guidance."]))
dump("frame_plan.json", plan)
dump("qa.json", qa)
dump("publish_package.json", pkg)
dump("codex_strategy.json", strategy)
(RUN / "research_raw.md").write_text(
    "# Research memo — Czy ziemniaki tuczą?\n\nChecked 2026-09-03. Live VitalLogic catalog contained 197 playlist items; title, description and tags were searched for the exact potato-calorie myth and no exact match was found. Nearby matches concern potassium or edema, not preparation-form calories.\n\nEvidence used:\n- NCEŻ: 100 g boiled potatoes about 73 kcal; 10 g oil adds about 88 kcal; method and additions matter.\n- Gov.pl PSSE Choszczno: about 73 kcal per 100 g boiled potatoes and about 280 kcal per 100 g fries.\n- NCEŻ acrylamide guidance: darker, more heavily fried/baked potato products tend to have more acrylamide; prefer golden colour and follow instructions.\n- PZH official database page: Polish per-100-g food-composition reference context.\n\nEditorial boundary: no universal calorie value, no food elimination, no personal weight-loss advice, no toxicity scare.\n",
    encoding="utf-8",
)
print(RUN)
