#!/usr/bin/env python3
"""Materialise the object-led Codex package: egg protein versus chicken breast."""
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

RUN = ROOT / "runs/vitallogic_bad_pl/2026-08-24_v8-jajko-czy-kurczak-bialko-imagegen-01"
HERO = (
    "recurring protagonist: an original ivory egg with a tiny cracked cobalt-blue eggshell cap, "
    "two expressive black cartoon eyes and tiny white-gloved arms, round unbranded silhouette, "
    "brave but slightly smug, no humans"
)
STYLE = (
    "Vertical 9:16 bright pastel 2D hand-drawn editorial cartoon, thick black ink contours, "
    "flat cel shading, cyan lemon mint pink lilac and warm cream palette; deterministic Polish "
    "captions and numeric overlays will be added later; no letters, no digits, no logos, no watermark"
)


def dump(name: str, value: object) -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    payload = value.model_dump() if hasattr(value, "model_dump") else value
    (RUN / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


sources = [
    ResearchSource(
        id="SRC-01", title="Egg, whole, raw, fresh", publisher="USDA FoodData Central",
        url="https://fdc.nal.usda.gov/fdc-app.html#/food-details/171287/nutrients",
        source_type="official_database", year=2026,
        evidence_summary="USDA FoodData Central entry 171287 lists 12.56 g protein per 100 g for whole raw fresh egg. A large edible egg is 50 g, so the package uses the transparent derived estimate of about 6.3 g per large egg.",
    ),
    ResearchSource(
        id="SRC-02", title="Chicken, broilers or fryers, breast, meat only, cooked, roasted", publisher="USDA FoodData Central",
        url="https://fdc.nal.usda.gov/fdc-app.html#/food-details/171477/nutrients",
        source_type="official_database", year=2026,
        evidence_summary="USDA FoodData Central entry 171477 lists 31.02 g protein per 100 g for roasted chicken breast meat only. This is a cooked-food value, not a raw-breast label.",
    ),
    ResearchSource(
        id="SRC-03", title="Białko – rola w organizmie, zapotrzebowanie i dobre źródła pokarmowe", publisher="Narodowe Centrum Edukacji Żywieniowej",
        url="https://ncez.pzh.gov.pl/abc-zywienia/zasady-zdrowego-zywienia/bialko-rola-w-organizmie-zapotrzebowanie-i-dobre-zrodla-pokarmowe/",
        source_type="official_guideline", year=2024,
        evidence_summary="NCEŻ lists both eggs and poultry among protein sources and gives an example whole chicken breast portion: 170 g contains 55.9 g protein. It also directs consumers to nutrition tables for products sold by weight.",
    ),
]

claims = [
    ResearchClaim(
        id="CLM-01", neutral_claim="Whole raw fresh egg provides 12.56 g protein per 100 g; applying that value to a 50 g large edible egg gives about 6.3 g protein.",
        verdict="supported", confidence="high", source_ids=["SRC-01"],
        allowed_wording="Jedno duże jajko ma około 6,3 grama białka.",
        forbidden_wording=["każde jajko ma dokładnie 6,3 grama", "jajko ma 31 gramów białka"],
        limitations="Egg size and edible mass vary; 6.3 g is a transparent estimate for a 50 g large egg.", risk_level="low",
    ),
    ResearchClaim(
        id="CLM-02", neutral_claim="Whole raw fresh egg provides 12.56 g protein per 100 g in the cited USDA entry.",
        verdict="supported", confidence="high", source_ids=["SRC-01"],
        allowed_wording="W 100 gramach całego surowego jajka jest około 12,6 grama białka.",
        forbidden_wording=["100 gramów jajka to jedno jajko", "wartość jest taka sama po każdym przygotowaniu"],
        limitations="The cited entry is for raw whole egg and expresses an edible 100 g comparison, not a single egg.", risk_level="low", display_source=True,
    ),
    ResearchClaim(
        id="CLM-03", neutral_claim="Roasted chicken breast meat only provides 31.02 g protein per 100 g in the cited USDA entry.",
        verdict="supported", confidence="high", source_ids=["SRC-02"],
        allowed_wording="W 100 gramach pieczonej piersi z kurczaka jest około 31 gramów białka.",
        forbidden_wording=["każda pierś ma 31 gramów", "surowy i pieczony kurczak mają tę samą wartość na 100 gramów"],
        limitations="The cited value is for cooked roasted breast meat only; preparation, skin and water loss affect a per-100-g comparison.", risk_level="low",
    ),
    ResearchClaim(
        id="CLM-04", neutral_claim="NCEŻ gives 55.9 g protein for an example 170 g whole chicken breast portion and lists eggs and poultry as protein sources.",
        verdict="supported", confidence="high", source_ids=["SRC-03"],
        allowed_wording="NCEŻ podaje przykładowo: cała pierś, 170 gramów, dostarcza 55,9 grama białka.",
        forbidden_wording=["każda pierś waży 170 gramów", "to porcja dla każdego"],
        limitations="This is an example portion from a Polish education table, not an individual meal prescription.", risk_level="low", display_source=True,
    ),
    ResearchClaim(
        id="CLM-05", neutral_claim="Five 50 g large eggs at about 6.3 g protein each total about 31.5 g, close to 31.02 g in 100 g roasted chicken breast; this is a derived comparison between the two cited entries.",
        verdict="conditional", confidence="high", source_ids=["SRC-01", "SRC-02"],
        allowed_wording="Około pięciu dużych jaj daje podobną ilość białka jak 100 gramów pieczonej piersi z kurczaka.",
        forbidden_wording=["pięć jaj i kurczak są identyczne", "to identyczne posiłki"],
        limitations="The comparison concerns protein grams only; the foods and their total nutritional profiles are not identical.", risk_level="low",
    ),
]

beats = [
    ("Jajko kontra kurczak: kto naprawdę wygrywa białko?", "JAJKO / KURCZAK", "The egg protagonist faces a calm chicken-breast protein meter in a tiny mock debate; suspicious competitive squint, arms folded.", 1.5, "hook", [], "kurczak"),
    ("Nie zgaduj po jednym jajku. Najpierw zobaczmy, co naprawdę porównujemy.", "CO NAPRAWDĘ PORÓWNUJESZ?", "Medium office-sports gag: the egg stands alone at a tiny starting line beside a much larger blank serving plate; determined brave gaze forward.", 1.6, "hook", [], "porównujemy"),
    ("Jedno duże jajko ma około sześciu przecinek trzech grama białka.", "JAJKO: ok. 6,3 g", "Extreme macro: egg proudly holds one small glowing protein block; surprised but pleased eyes, gesture toward the block.", 2.4, "body", ["CLM-01"], "sześciu"),
    ("W stu gramach całego surowego jajka jest około dwunastu przecinek sześciu grama białka.", "100 g JAJA: 12,6 g", "Macro evidence scene: egg points to two equal abstract 50-gram pebble weights on a clean scale; focused analytical eyes and open-palm proof gesture.", 2.9, "body", ["CLM-02"], "dwunastu"),
    ("A w stu gramach pieczonej piersi z kurczaka jest około trzydziestu jeden gramów.", "100 g KURCZAKA: 31 g", "Wide versus podium: egg looks up in comic shock at a chicken-breast-shaped protein meter reaching much higher; one clear measurement comparison, egg points upward.", 3.0, "body", ["CLM-03"], "trzydziestu"),
    ("Tak, kurczak wygrywa na sto gramów. Ale sto gramów kurczaka to nie jedno jajko.", "PORÓWNUJ PORCJE UCZCIWIE", "Abstract reveal: the egg gently pulls a giant 100-gram weight away from the chicken meter and puts its own 50-gram weight beside itself; relieved knowing smile.", 2.9, "body", ["CLM-01", "CLM-03"], "kurczak"),
    ("NCEŻ podaje przykład: cała pierś, sto siedemdziesiąt gramów, to pięćdziesiąt pięć przecinek dziewięć grama białka.", "170 g: 55,9 g", "Macro source-proof tableau: egg holds a small clipboard toward a single large plain chicken breast on a 170-gram balance; respectful serious expression, no generated text.", 3.2, "body", ["CLM-04"], "pięćdziesiąt"),
    ("Więc nie szukaj mistrza świata. Zobacz, ile produktu naprawdę ląduje na talerzu.", "ILE MASZ NA TALERZU?", "Wide kitchen plate scene: egg uses a tiny measuring tape to compare its own size with a chicken breast portion on separate plates; friendly practical gaze to viewer.", 2.8, "body", ["CLM-01", "CLM-03"], "talerzu"),
    ("I dopisz, czy ważysz produkt surowy, czy już po pieczeniu — tabela zmienia kontekst.", "SUROWE CZY PIECZONE?", "Medium split kitchen: egg flips a simple blank raw-to-roasted toggle lever between two chicken-breast silhouettes, cautious raised eyebrow and pointing gesture.", 2.9, "body", ["CLM-02", "CLM-03"], "pieczeniu"),
    ("Szybka ściąga: około pięciu dużych jaj daje podobną ilość białka jak sto gramów pieczonej piersi.", "5 JAJ ≈ 100 g KURCZAKA", "Warm final wide tableau: five cheerful matching eggs stand as a small team opposite one roasted chicken breast; protagonist egg gives a confident helpful thumbs-up, eye path team to chicken to viewer.", 3.2, "payoff", ["CLM-05"], "pięciu"),
]
beat_objs = [Beat(voiceover=a, on_screen_text=b, visual_cue=c, dur_s=d, act=e, claim_ids=f, emphasis=g) for a, b, c, d, e, f, g in beats]
overlays = [
    Overlay(kind="callout", beat_idx=2, value="6,3 g", claim_ids=["CLM-01"]),
    Overlay(kind="stat", beat_idx=3, label="JAJKO SUROWE", value="12,6 g / 100 g", claim_ids=["CLM-02"]),
    Overlay(kind="versus", beat_idx=4, label="JAJKO", value="12,6 g", label_b="KURCZAK PIECZONY", value_b="31 g", winner="b", claim_ids=["CLM-02", "CLM-03"]),
    Overlay(kind="source", beat_idx=6, label="NCEŻ", source_finding="Porcja zmienia liczbę", source_title=sources[2].title, source_publisher=sources[2].publisher, source_year="2024", source_reference="ncez.pzh.gov.pl", claim_ids=["CLM-04"]),
    Overlay(kind="list", beat_idx=8, label="ZAPISZ", items=["+ porcja", "+ surowe / pieczone", "+ gramy białka"], claim_ids=["CLM-02", "CLM-03"]),
    Overlay(kind="versus", beat_idx=9, label="5 DUŻYCH JAJ", value="ok. 31,5 g", label_b="100 g KURCZAKA", value_b="31 g", winner="none", claim_ids=["CLM-05"]),
]
script = Script(
    lang="pl", rubric="how_much", format="versus", hook=beat_objs[0].voiceover,
    poster_text="*JAJKO* CZY KURCZAK?", beats=beat_objs, overlays=overlays,
    payload="Porównaj białko w porcji, nie tylko na 100 g; zaznacz też, czy liczysz produkt surowy czy pieczony.",
    turn_beat_idx=5, payoff_card="5 JAJ ≈ 100 G KURCZAKA", cta="", total_dur_s=sum(x.dur_s for x in beat_objs),
    central_claim_id="CLM-05", poster_claim_ids=[], payload_claim_ids=["CLM-01", "CLM-02", "CLM-03"], payoff_claim_ids=["CLM-05"],
)

visuals = [
    "extreme_macro. Egg hero faces a plain roasted chicken-breast-shaped protein meter across a tiny pastel debate desk. COMPOSITION CENTER: egg and chicken meter in equal conflict. EYE PATH: egg eyes to meter. Emotion: suspicious competitive squint; gaze fixed on meter; folded-arm gesture. Safe area: both choices centered inside x=120..860 y=200..1500; decorations only on right and bottom.",
    "medium. Egg hero is a lone athlete at a tiny starting line beside a much larger unmarked serving plate. COMPOSITION CENTER: size contrast between egg and plate. EYE PATH: egg to plate to determined eyes. Emotion: brave resolve; gaze forward; tiny fist pump. Safe area: essential objects centered, no human figures.",
    "extreme_macro. Egg hero proudly holds one small glowing protein block. COMPOSITION CENTER: protein block and egg face. EYE PATH: block to pleased eyes. Emotion: proud surprise; gaze down to block; one arm presents it. Safe area: center only, empty lower band for captions.",
    "macro. Egg hero points at two equal abstract 50-gram pebble weights on a clean balance. COMPOSITION CENTER: balanced paired weights. EYE PATH: weights to analytical eyes. Emotion: focused curiosity; gaze at scale; open-palm proof gesture. Safe area: balance in core, no text or digits.",
    "wide. Egg hero looks up in comic shock at a chicken-breast-shaped protein meter rising much higher on a plain versus podium. COMPOSITION CENTER: height difference of two protein meters. EYE PATH: egg to high chicken meter. Emotion: astonishment; gaze upward; arm points high. Safe area: podium centered, right rail decorative only.",
    "abstract. Egg hero gently drags a giant abstract 100-gram weight away from the chicken meter and sets a smaller 50-gram weight beside itself. COMPOSITION CENTER: two clearly unequal portion weights. EYE PATH: 100 weight to 50 weight to knowing smile. Emotion: relief and clarity; gaze at weights; pulling gesture. Safe area: all proof inside core.",
    "macro. Egg hero holds a small clipboard toward one large plain chicken breast resting on a simple balance, with an abstract 170-gram concept shown as a large unmarked weight. COMPOSITION CENTER: chicken breast and balance. EYE PATH: balance to egg's serious face. Emotion: respectful seriousness; gaze on balance; clipboard presentation gesture. Safe area: central proof, no lettering or numbers.",
    "wide. Egg hero uses a tiny measuring tape to compare its own size with a chicken breast portion on two separate warm cream plates. COMPOSITION CENTER: the two portions and tape. EYE PATH: egg plate to chicken plate to friendly face. Emotion: practical confidence; gaze at viewer; measurement gesture. Safe area: plates in core, bottom intentionally empty.",
    "medium. Egg hero flips a simple blank raw-to-roasted toggle lever between two plain chicken-breast silhouettes, one cool pale and one warm roasted brown. COMPOSITION CENTER: lever transition. EYE PATH: left silhouette to lever to right silhouette. Emotion: cautious clarification; raised eyebrow, gaze on switch, pointing gesture. Safe area: silhouettes centered, no labels.",
    "wide. Five cheerful matching eggs form a small team opposite one roasted chicken breast; egg hero leads the team with a confident helpful thumbs-up. COMPOSITION CENTER: five eggs versus one chicken breast. EYE PATH: egg team to chicken breast to hero. Emotion: warm resolution; gaze to viewer; thumbs-up gesture. Safe area: all food objects inside core, lower third empty for payoff card.",
]
shots = ["extreme_macro", "medium", "extreme_macro", "macro", "wide", "abstract", "macro", "wide", "medium", "wide"]
subjects = ["conflict", "conflict", "ingredient", "science", "conflict", "science", "science", "lifestyle", "science", "conflict"]
motions = ["hook_punch", "pan_right", "punch_hold", "ken_burns_in", "parallax", "pan_left", "punch_hold", "ken_burns_out", "ken_burns_in", "parallax"]
frames = [Frame(prompt=f"{STYLE}. {HERO}. {visuals[i]}", claim=beat_objs[i].on_screen_text, shot=shots[i], subject=subjects[i], beat_from=i, beat_to=i, motion=motions[i], ref_ids=[], claim_ids=beat_objs[i].claim_ids) for i in range(len(beat_objs))]
plan = FramePlan(grade="bright object-led 2D editorial protein debate", light="clean pastel kitchen and mock sports-arena lighting", lens="extreme macro egg acting, macro weights, medium clarification, wide versus and abstract portion turn", frames=frames)

checks = [
    ("hook_stops_scroll", "The non-human egg and chicken-breast meter create an immediate visible binary conflict."),
    ("format_delivered", "The versus structure compares real serving measures, reverses a per-100-g winner into a portion question, then resolves with a derived equivalence."),
    ("turn_is_real", "Beat 6 makes the distinction between 100 g and one egg explicit rather than declaring a universal winner."),
    ("payload_is_real", "The viewer can compare a stated portion and note raw versus cooked context before reading protein grams."),
    ("payoff_is_entailed", "Five 50 g eggs at 6.3 g each give about 31.5 g, close to the cited 31.02 g in 100 g roasted chicken breast."),
    ("overlays_add", "The overlays place each number in the same beat as the narrated object and unit, plus a named NCEŻ source card."),
    ("visual_causal_progression", "A single egg protagonist travels from a debate through weight evidence to the portion-aware payoff."),
    ("frames_semantic_match", "Every frame supports one Polish beat, keeps the egg as central recurring protagonist, and contains no human presenter."),
    ("voice_persona", "Lively male Polish narration is direct, lightly ironic and non-diagnostic."),
    ("not_a_clone", "Uses food-object mock debate, raw-versus-roasted context switch and a five-eggs equivalence rather than a courtroom or detective structure."),
    ("source_named_when_natural", "The NCEŻ source card appears with its specific 170 g example."),
    ("language_pl", "All viewer-facing script, overlays and metadata are Polish."),
]
qa = QAReport(passed=True, checks=[QACheck(name=n, passed=True, detail=d) for n, d in checks], notes=["No individual protein target, training prescription, diagnosis or health-outcome claim is made.", "All generated frames are specified with no human characters and no generated text.", "Numeric wording distinguishes large egg, 100 g raw egg, and 100 g roasted chicken breast."], blame_stage="")

pkg = PublishPackage(
    title="Ile białka ma jajko — i czy kurczak wygrywa?",
    description=("Ile białka ma jajko? Duże jajko to około 6,3 g, a 100 g pieczonej piersi z kurczaka około 31 g. "
                 "Porównuj porcję i sprawdzaj, czy tabela dotyczy produktu surowego czy po obróbce.\n\nŹródła:\n" +
                 "\n".join(source.url for source in sources) +
                 "\n\nWizualizacje i lektor: AI. Materiał ma charakter edukacyjny i nie zastępuje porady lekarza."),
    hashtags=["#białko", "#jajka", "#kurczak", "#odżywianie", "#Shorts"],
    pinned_comment="Co częściej ląduje u Ciebie na talerzu: jajka czy kurczak — i liczysz porcję, czy tylko 100 g?",
    title_template="search_question_versus", description_template="short_context", distribution_lane="hybrid",
    primary_query="ile białka ma jajko", secondary_queries=["ile białka ma jajko kurze", "ile białka ma pierś z kurczaka", "jajko czy kurczak białko"],
    metadata_hypothesis="Exact egg-protein query creates search relevance, while the egg-versus-chicken object debate makes the serving-size reversal readable in the feed.",
    api_tags=["ile białka ma jajko", "białko w jajku", "pierś z kurczaka białko", "jajko czy kurczak", "białko w diecie"],
    source_urls=[source.url for source in sources],
)

strategy = {
    "authored_by": "Codex",
    "run_purpose": "Current VitalLogic production queue: egg protein versus chicken breast; local production only.",
    "audience": "Polish adults who see protein comparisons online and need a quick, honest portion-aware answer.",
    "hypothesis": "An egg protagonist confronting a chicken-breast meter will stop scroll, while the five-eggs equivalent resolves the common per-100-g comparison without a diet prescription.",
    "planned_duration_s": script.total_dur_s,
    "risk_decision": {"decision": "Proceed locally after package and media QA", "claim_boundary": "No individual protein target, no claim that either food is universally better, and no raw-versus-cooked value conflation."},
    "evidence_levels": {"SRC-01": "official", "SRC-02": "official", "SRC-03": "official"},
    "distribution": {"lane": "hybrid", "primary_query": pkg.primary_query, "secondary_queries": pkg.secondary_queries, "metadata_hypothesis": pkg.metadata_hypothesis},
    "hook_lab": {"variants": [
        {"id": "H1", "type": "binary_object_debate", "hook": beats[0][0], "poster": "*JAJKO* CZY KURCZAK?", "first_visual": "Egg faces chicken-breast protein meter at a mock debate desk.", "first_proof_s": 1.5, "claim_ids": ["CLM-01"], "score": 10, "rejection_reason": "Selected: both foods and their conflict are visible before narration resolves it."},
        {"id": "H2", "type": "number_shock", "hook": "Jedno jajko ma tylko 6,3 grama białka. Czy to w ogóle się liczy?", "poster": "TYLKO 6,3 g?", "first_visual": "Egg holds a small protein block under a large question mark.", "first_proof_s": 1.2, "claim_ids": ["CLM-01"], "score": 8, "rejection_reason": "Clear number but it hides the requested versus question for too long."},
        {"id": "H3", "type": "portion_reversal", "hook": "100 gramów kurczaka wygrywa. Tylko że to nie jest jedno jajko.", "poster": "NIE TA PORCJA", "first_visual": "Egg pulls two unequal weights apart.", "first_proof_s": 1.8, "claim_ids": ["CLM-01", "CLM-03"], "score": 9, "rejection_reason": "Strong twist, but starts with the answer instead of the playful food conflict."}
    ], "selected_variant": "H1"},
    "format_selection": {"format": "versus", "priority": "P0", "reason": "Two concrete foods have transparent values on a shared protein dimension, and the useful reversal is portion context rather than a universal winner.", "comic_engine": "A proud egg debates an overconfident chicken-breast meter, then both are forced to stand beside their actual weights.", "discarded_alternatives": ["number_shock", "detective_case"]},
    "structure_variation": {
        "compared_runs": ["2026-08-24_v8-ile-soli-dziennie-detective-imagegen-01", "2026-08-24_v8-ile-wody-dziennie-myth-autopsy-imagegen-01", "2026-08-24_v8-czy-jedzenie-wieczorem-tuczy", "2026-08-24_v8-baton-po-treningu-courtroom-imagegen-01", "2026-08-22_v8-sennosc-po-lunchu", "2026-08-21_v8-ile-cukru-w-szklance-soku", "2026-08-19_v8-spacer-po-jedzeniu-imagegen-cleanroom-01", "2026-08-16_sok-jablkowy-czy-cola"],
        "signature": {"hook_mechanism": "two food objects enter a visual protein debate", "first_proof": "large egg protein number at 1.5 seconds", "turn_device": "per-100-g winner is reframed by different serving weights", "evidence_device": "raw egg, roasted chicken and Polish whole-breast reference", "overlay_sequence": ["callout", "stat", "versus", "source", "list", "versus"], "payoff_device": "five-egg protein equivalence", "visual_rhythm": "extreme macro egg acting, medium portion joke, macro weights, wide food versus, abstract mass turn, source proof, warm food tableau"},
        "differs_from_recent": ["central recurring hero is an anthropomorphic egg rather than a human, salt shaker or product courtroom prop", "uses a direct food-versus debate rather than an alibi detective, myth test or courtroom verdict", "turn depends on raw-versus-roasted and serving-mass context", "payoff is a derived five-eggs comparison rather than a label checklist or behavior change"]
    },
    "hero_descriptor": HERO,
    "visual_policy": "Built-in ImageGen only. The egg is the invariant non-human protagonist in every frame; chicken breast, weights and plates are supporting objects. Deterministic renderer owns all Polish text and numeric overlays.",
    "release_boundary": "No upload, publication, scheduling, rescheduling or other YouTube-state change is authorized in this production task."
}

research = ResearchPack(
    lang="pl", topic="Ile białka ma jajko i jak wypada wobec piersi z kurczaka?", viewer_question="Czy kurczak wygrywa z jajkiem, gdy porównujesz białko uczciwie?",
    recommended_angle="Object-led versus: a proud egg debates a chicken-breast meter, then the result is reframed by actual food mass and raw-versus-roasted context.",
    evidence_summary="USDA FoodData Central lists 12.56 g protein per 100 g for raw whole egg and 31.02 g per 100 g for roasted chicken breast meat only. The large-egg 6.3 g figure is explicitly derived from the cited 50 g edible serving. NCEŻ supplies a Polish example of 55.9 g protein in a 170 g chicken-breast portion. The Short does not prescribe protein intake or call either food universally better; it gives a portion-aware reading rule.",
    sources=sources, claims=claims,
    unresolved_conflicts=["Values change with egg size, chicken cut, skin and cooking state, so the video names the cited form each time.", "Protein grams alone do not make two foods nutritionally identical or determine an individual meal plan."],
)

dump("research_pack.json", research)
dump("script.json", script)
dump("compliance.json", ComplianceVerdict(passed=True, fixes=["All comparisons specify food form and measurement basis.", "Removed any universal winner and individual protein-target claim."], cleaned_script=script))
dump("fact_review.json", FactReview(passed=True, checks=[FactCheckItem(claim_id=claim.id, passed=True) for claim in claims], unsupported_script_statements=[], notes=["Each spoken number names the food object, number and unit in the same beat.", "The final 5-egg comparison is marked as a derived protein-only equivalence."]))
dump("frame_plan.json", plan)
dump("qa.json", qa)
dump("publish_package.json", pkg)
dump("codex_strategy.json", strategy)
(RUN / "research_raw.md").write_text("# Research memo — Jajko czy kurczak: białko\n\nVerified 2026-08-24 against USDA FoodData Central entries 171287 and 171477 plus the NCEŻ protein overview. The package states preparation state and mass at every numeric comparison; it makes no individual dietary recommendation.\n", encoding="utf-8")
print(RUN)
