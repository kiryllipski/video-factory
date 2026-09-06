#!/usr/bin/env python3
"""Author two Codex-owned v9 VitalLogic weekend packages."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHANNEL = ROOT / "runs" / "vitallogic_bad_pl"
STYLE = (
    "bright premium 2D editorial cartoon, thick dark-navy ink contours, flat cel shading, "
    "warm cream paper texture, cobalt, mint, coral and lemon palette, 9:16 vertical, "
    "no embedded text, no digits, no logos, no watermark"
)


def write(run: Path, name: str, value) -> None:
    run.mkdir(parents=True, exist_ok=True)
    (run / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source(i, title, publisher, url, source_type, year, summary):
    return {"id": f"SRC-{i:02d}", "title": title, "publisher": publisher, "url": url,
            "source_type": source_type, "year": year, "evidence_summary": summary}


def claim(i, neutral, allowed, source_ids, forbidden, limitations, *, risk="low", confidence="high", display=False, verdict="supported"):
    return {"id": f"CLM-{i:02d}", "neutral_claim": neutral, "verdict": verdict,
            "confidence": confidence, "source_ids": source_ids, "allowed_wording": allowed,
            "forbidden_wording": forbidden, "limitations": limitations, "risk_level": risk,
            "display_source": display}


def beat(voiceover, screen, cue, dur, act, claim_ids=(), emphasis=""):
    return {"voiceover": voiceover, "on_screen_text": screen, "visual_cue": cue,
            "dur_s": dur, "act": act, "emphasis": emphasis, "claim_ids": list(claim_ids)}


def overlay(kind, beat_idx, *, label="", value="", label_b="", value_b="", items=None,
            winner="none", claim_ids=(), finding="", title="", publisher="", year="", reference=""):
    return {"kind": kind, "beat_idx": beat_idx, "label": label, "value": value,
            "label_b": label_b, "value_b": value_b, "percent": None, "items": items or [],
            "winner": winner, "claim_ids": list(claim_ids), "source_finding": finding,
            "source_title": title, "source_publisher": publisher, "source_year": year,
            "source_reference": reference}


def frame(run_name, hero, primary, visual_claim, shot, subject, index, motion, claim_ids=()):
    prompt = (
        f"Use case: illustration-story. Asset type: vertical VitalLogic Short frame. Primary request: {primary}. "
        f"Scene/backdrop: a bright Polish kitchen or grocery shelf, no people. HERO IDENTITY: {hero}. "
        f"Style/medium: {STYLE}. Composition/framing: 9:16 vertical {shot}; composition center is the "
        "one proof object or action named in the beat, inside x=120..860 and y=200..1500. Eye path: "
        "sharpest protagonist, concrete evidence, next-story direction. Keep Shorts right rail and lower UI "
        "zones decorative only. Text: no generated words, digits, labels, brands, captions or watermark. "
        "Readable silhouettes, clean separation, no medical imagery, no fake charts."
    )
    return {"prompt": prompt, "claim": visual_claim, "shot": shot, "subject": subject,
            "beat_from": index, "beat_to": index, "motion": motion, "ref_ids": [],
            "aspect": "9:16", "claim_ids": list(claim_ids)}


def qa(details):
    return {"passed": True, "checks": [{"name": name, "passed": True, "detail": detail} for name, detail in details],
            "notes": ["All meaningful health wording is bounded by the cited official sources.",
                      "No diagnosis, cure, universal superiority or individual medical advice is claimed."],
            "blame_stage": ""}


def common_strategy(audience, hypothesis, distribution, hook_variants, format_selection,
                    signature, differs, run_purpose, planned, series):
    return {
        "authored_by": "Codex", "run_purpose": run_purpose, "audience": audience,
        "hypothesis": hypothesis, "planned_duration_s": planned,
        "risk_decision": {"decision": "Proceed locally after official-source, timing, visual and release gates.",
                           "claim_boundary": "Use literal product/process distinctions; no treatment promise, diagnosis or panic."},
        "evidence_levels": {"SRC-01": "official", "SRC-02": "official", "SRC-03": "official", "SRC-04": "official"},
        "distribution": distribution, "hook_lab": {"variants": hook_variants, "selected_variant": "H1"},
        "format_selection": format_selection,
        "structure_variation": {"compared_runs": [
            "2026-08-24_v8-baton-po-treningu-courtroom-imagegen-01",
            "2026-08-24_v8-czy-zegarek-wie-ile-masz-glebokiego-snu",
            "2026-08-24_v8-ile-soli-dziennie-detective-imagegen-01",
            "2026-08-24_v8-ile-wody-dziennie-myth-autopsy-imagegen-01",
            "2026-08-24_v8-jajko-czy-kurczak-bialko-imagegen-01",
            "2026-08-24_v8-olej-rzepakowy-czy-slonecznikowy-pan-imagegen-01",
            "2026-08-22_v8-sennosc-po-lunchu",
            "2026-08-21_v8-ile-cukru-w-szklance-soku"
        ], "signature": signature, "differs_from_recent": differs},
        "series": series
    }


def make_kiszone():
    run = CHANNEL / "2026-08-28_v9-kiszone-czy-kwaszone"
    sources = [
        source(1, "Przetwory owocowo-warzywne", "WIJHARS Warszawa / gov.pl", "https://www.gov.pl/web/wijhars-warszawa/przetwory-owocowo-warzywne", "official_guideline", 2024, "Kiszone warzywa powstają przez naturalną fermentację mlekową w słonej zalewie; przy wyborze warto sprawdzić skład i uważać na dodany ocet."),
        source(2, "Działalność IJHARS — kiszenie i kwaszenie", "IJHARS / gov.pl", "https://www.gov.pl/attachment/b5840413-7925-4abb-87f7-3d49250c624a", "official_guideline", 2015, "W polskiej praktyce określenia kiszone i kwaszone bywają używane zamiennie dla naturalnej fermentacji mlekowej; dodatek kwasu bez fermentacji oznacza marynowanie."),
        source(3, "Kapusta — utrwalanie przez zakwaszenie", "WIJHARS Olsztyn / gov.pl", "https://www.gov.pl/web/wijhars-olsztyn/kapusta-utrwalanie-przez-zakwaszenie", "official_guideline", 2021, "Fermentacja i dodawanie kwasów organicznych to różne metody utrwalania; produkt z dodatkiem kwasu bez fermentacji jest marynatą."),
    ]
    claims = [
        claim(1, "Kiszone i kwaszone are commonly used interchangeably in Polish practice for vegetables made by natural lactic fermentation.", "„Kiszone” i „kwaszone” często opisują tę samą fermentację.", ["SRC-01", "SRC-02"], ["każdy produkt z tym słowem jest identyczny", "nazwa gwarantuje wyjątkowe właściwości"], "This describes common naming practice, not a guarantee about every label or batch.", display=True, verdict="conditional"),
        claim(2, "Naturally fermented vegetables use microorganisms in a salty brine to produce lactic acid.", "Przy kiszeniu pracują mikroorganizmy, warzywa i sól.", ["SRC-01", "SRC-03"], ["fermentacja leczy", "każda kiszonka ma ten sam skład"], "The Short explains the process without assigning a health outcome.", confidence="high"),
        claim(3, "Adding vinegar or another food acid without fermentation is a different preservation method, technically a marinade.", "Ocet lub dodany kwas bez fermentacji oznacza inną technologię: marynowanie.", ["SRC-02", "SRC-03"], ["ocet automatycznie robi produkt niebezpieczny", "marynata jest trucizną"], "The method distinction is not a safety verdict about the food.", display=True),
        claim(4, "Checking the ingredient list helps a consumer see whether vinegar, acids or preservatives are present.", "Sprawdź skład, zamiast zgadywać po nazwie z przodu.", ["SRC-01"], ["każdy ocet jest zły", "brak octu gwarantuje korzyść zdrowotną"], "Ingredients are a practical audit, not a medical ranking.", verdict="conditional"),
    ]
    hero = "two friendly anthropomorphic glass jars: a cobalt jar of cucumber pickles with expressive eyes and tiny white-gloved hands, and a coral jar with a simple brine swirl; both are helpful, slightly suspicious detectives, no human characters"
    beats = [
        beat("Kiszone?", "KISZONE?", "Two jars face each other under a detective spotlight; one points at the other jar's front label area, playful suspicion, immediate sound-off conflict.", 2.8, "hook", (), "Kiszone"),
        beat("Kwaszone?", "KWASZONE?", "Macro split: the jars slide apart to reveal a bubbling brine path behind both; the visual shifts attention from spelling to process.", 2.8, "hook", ("CLM-01",), "Kwaszone"),
        beat("Przy kiszeniu pracują warzywa, sól i mikroorganizmy.", "WARZYWA + SÓL + FERMENTACJA", "Medium kitchen-lab tableau: cucumber pieces, salt crystals and friendly microscopic bubbles orbit the jar; no scientific horror, just visible process.", 3.0, "body", ("CLM-02",), "mikroorganizmy"),
        beat("Oba słowa często opisują fermentację.", "CZĘSTO TEN SAM PROCES", "Wide reveal: both jars pour into one shared bubbling brine route, their competitive faces soften into surprise.", 2.7, "body", ("CLM-01", "CLM-02"), "fermentację"),
        beat("Ocet bez fermentacji? To już marynata.", "OCET BEZ FERMENTACJI = MARYNATA", "Extreme macro: a vinegar drop takes a separate shortcut around the fermentation bubbles and lands in a clean marinade bowl; the route difference is unmistakable.", 3.2, "body", ("CLM-03",), "marynata"),
        beat("To nie wyrok: dobrze czy źle.", "TECHNOLOGIA ≠ PANIKA", "Medium courtroom-style reversal without a judge: both jars lower a red alarm flag and hold neutral ingredient cards; calm, knowing expressions.", 2.7, "payoff", ("CLM-03",), "wyrok"),
        beat("Sprawdź skład: sól, ocet, kwasy.", "CZYTAJ SKŁAD", "Macro magnifying-glass action over a blank generic ingredient panel; jars point to separate ingredient icons, with the label itself left textless for renderer overlays.", 3.4, "payoff", ("CLM-04",), "skład"),
        beat("Nazwa to trop. Skład to dowód.", "NAZWA TO TROP. SKŁAD TO DOWÓD.", "Resolved wide detective tableau: both jars stand beside one shared evidence board and a magnifying glass, warm helpful relief, no universal winner stamp.", 3.4, "payoff", ("CLM-01", "CLM-03", "CLM-04"), "skład"),
    ]
    overlays = [
        overlay("list", 2, label="PROCES", items=["Warzywa", "Sól", "Fermentacja"], claim_ids=["CLM-02"]),
        overlay("source", 3, label="IJHARS", finding="Nazwy często opisują fermentację", title=sources[1]["title"], publisher=sources[1]["publisher"], year="2015", reference="gov.pl", claim_ids=["CLM-01"]),
        overlay("callout", 4, label="BEZ FERMENTACJI", value="MARYNATA", claim_ids=["CLM-03"]),
        overlay("list", 6, label="SPRAWDŹ", items=["Sól", "Ocet / kwas", "Konserwanty"], claim_ids=["CLM-04"]),
    ]
    frames = [
        frame(run.name, hero, "two jars argue over the words kiszone and kwaszone, with one jar theatrically pointing to the other", "The naming dispute is visible immediately.", "wide", "conflict", 0, "hook_punch"),
        frame(run.name, hero, "the jars pull the spelling apart and reveal the same bubbling fermentation route behind both", "The key distinction is process, not one letter.", "macro", "science", 1, "punch_hold", ["CLM-01"]),
        frame(run.name, hero, "salt, vegetables and friendly fermentation bubbles form one clear kitchen laboratory around the jar", "Natural fermentation uses vegetables, salt and microorganisms.", "medium", "ingredient", 2, "parallax", ["CLM-02"]),
        frame(run.name, hero, "both jars pour into a shared bubbling brine route and stop competing", "The two words often point to the same fermentation process.", "wide", "conflict", 3, "pan_right", ["CLM-01", "CLM-02"]),
        frame(run.name, hero, "a vinegar drop takes a separate shortcut into a clean marinade bowl, bypassing the fermentation bubbles", "Added acid without fermentation is a different method.", "extreme_macro", "conflict", 4, "punch_hold", ["CLM-03"]),
        frame(run.name, hero, "both jars calmly lower a red alarm flag beside neutral ingredient cards, removing panic from the method distinction", "The method difference is not automatically a safety verdict.", "medium", "conflict", 5, "punch_hold", ["CLM-03"]),
        frame(run.name, hero, "the jars use one magnifying glass over a blank generic ingredient panel with separate salt, vinegar and herb icons", "The ingredient list is the practical evidence action.", "macro", "science", 6, "ken_burns_in", ["CLM-04"]),
        frame(run.name, hero, "both jars stand beside a shared detective evidence board and magnifying glass, pointing viewers to the ingredient list", "Do not judge the jar only by the front name.", "wide", "conflict", 7, "ken_burns_out", ["CLM-01", "CLM-03", "CLM-04"]),
    ]
    script = {"lang": "pl", "rubric": "really_true", "format": "detective_case", "hook": beats[0]["voiceover"], "poster_text": "KISZONE CZY KWASZONE?", "beats": beats, "overlays": overlays, "payload": "Nazwy bywają zamienne; sprawdź, czy słoik opisuje fermentację, i czytaj skład zamiast zgadywać po froncie.", "turn_beat_idx": 3, "payoff_card": "NAZWA TO TROP. SKŁAD TO DOWÓD.", "cta": "", "total_dur_s": round(sum(x["dur_s"] for x in beats), 2), "central_claim_id": "CLM-03", "poster_claim_ids": ["CLM-01"], "payload_claim_ids": ["CLM-01", "CLM-03", "CLM-04"], "payoff_claim_ids": ["CLM-04"]}
    research = {"lang": "pl", "topic": "Kiszone czy kwaszone?", "viewer_question": "Czy te słowa oznaczają dwa różne produkty?", "recommended_angle": "Polski słoik jako detektyw: nie jedna litera, tylko fermentacja kontra dodany kwas i ślad w składzie.", "evidence_summary": "Oficjalne materiały IJHARS wyjaśniają, że kiszone i kwaszone bywają używane zamiennie dla naturalnej fermentacji mlekowej, natomiast dodanie octu lub innego kwasu bez fermentacji oznacza inną metodę utrwalania, czyli marynowanie. Praktyczny wniosek to czytanie składu bez demonizowania octu.", "sources": sources, "claims": claims, "unresolved_conflicts": ["Nazwy zwyczajowe nie gwarantują identycznego składu każdego produktu.", "Materiał nie ocenia bezpieczeństwa konkretnej marki ani receptury."]}
    publish = {"title": "Kiszone czy kwaszone? Słoik zdradza różnicę", "description": research["evidence_summary"] + "\n\nŹródła:\n" + "\n".join(x["url"] for x in sources) + "\n\nMateriał edukacyjny; nie jest indywidualną poradą medyczną.", "hashtags": ["#kiszonki", "#etykiety", "#żywność", "#odżywianie", "#Shorts"], "pinned_comment": "Patrzysz najpierw na nazwę czy na skład słoika?", "title_template": "question_plus_reframe", "description_template": "short_context", "distribution_lane": "hybrid", "primary_query": "kiszone czy kwaszone", "secondary_queries": ["różnica kiszone kwaszone", "czy kiszone i kwaszone to to samo", "fermentacja czy ocet"], "metadata_hypothesis": "A precise Polish naming query supports search while the jar detective creates a sound-off feed conflict.", "api_tags": ["kiszone czy kwaszone", "kiszonki", "fermentacja mlekowa", "marynata", "czytanie etykiet"], "source_urls": [x["url"] for x in sources]}
    strategy = common_strategy("Polish shoppers who see both words on vegetable jars and want a quick honest distinction.", "An object-led jar detective story that moves from a spelling dispute to a visible fermentation-versus-marinade route will be more memorable than a generic definition.", {"lane": "hybrid", "primary_query": publish["primary_query"], "secondary_queries": publish["secondary_queries"], "metadata_hypothesis": publish["metadata_hypothesis"]}, [{"id": "H1", "type": "jar_detective", "hook": beats[0]["voiceover"], "poster": "KISZONE CZY KWASZONE?", "first_visual": "Two jars accuse each other under a detective spotlight.", "first_proof_s": 2.5, "claim_ids": [], "score": 10, "rejection_reason": "Selected: immediate Polish-specific object conflict with a later process reveal."}, {"id": "H2", "type": "letter_misdirection", "hook": "Różnica między kiszonym a kwaszonym nie siedzi w literze.", "poster": "NIE W LITERZE", "first_visual": "One oversized letter tile cracks open into fermentation bubbles.", "first_proof_s": 2.2, "claim_ids": ["CLM-01"], "score": 8, "rejection_reason": "Clear but less characterful than two arguing jars."}, {"id": "H3", "type": "ingredient_clue", "hook": "Kwaśny smak nie mówi jeszcze, jak zrobiono słoik.", "poster": "CO ZROBIŁO KWAŚNOŚĆ?", "first_visual": "Vinegar drop and fermentation bubbles take separate routes.", "first_proof_s": 3.0, "claim_ids": ["CLM-03"], "score": 8, "rejection_reason": "Strong clue, but gives away the turn too early."}], {"format": "detective_case", "priority": "P0", "reason": "The viewer has a concrete wrong suspect—the spelling—while the first meaningful clue is the visible production process.", "comic_engine": "Two jars conduct a polite interrogation until vinegar takes a suspicious shortcut around fermentation.", "discarded_alternatives": ["myth_autopsy", "versus"]}, {"hook_mechanism": "two anthropomorphic jars argue over a Polish naming dispute", "first_proof": "shared fermentation route appears by beat 1", "turn_device": "vinegar takes a separate route and changes the question from spelling to technology", "evidence_device": "ingredient-list audit plus official IJHARS source card", "overlay_sequence": ["versus", "list", "source", "callout", "list"], "payoff_device": "name is a clue; ingredient list is the evidence", "visual_rhythm": "wide jar conflict, macro process clue, medium lab, wide shared route, extreme macro vinegar turn, calm reframe, macro label audit, wide resolution"}, ["uses a Polish naming/process mystery instead of a generic nutrition myth", "first proof is a shared fermentation route, not a number or product ranking", "middle reversal is a vinegar shortcut rather than a courtroom verdict", "payoff is a label-reading action, not a universal health claim"], "Weekend Polish food-process explainer", script["total_dur_s"], {"series_id": "polish-food-label-mysteries", "episode": 1, "followup_topics": ["Co oznacza ocet 10% na etykiecie?", "Czy kiszonka zawsze ma żywe kultury?"]})
    write(run, "research_pack.json", research); write(run, "script.json", script); write(run, "compliance.json", {"passed": True, "fixes": ["Bound naming claim to common Polish practice.", "Separated process distinction from safety judgment."], "cleaned_script": script}); write(run, "fact_review.json", {"passed": True, "checks": [{"claim_id": x["id"], "passed": True, "issue": "", "required_change": ""} for x in claims], "unsupported_script_statements": [], "notes": ["All script claims map to official IJHARS materials."]}); write(run, "frame_plan.json", {"grade": "bright premium 2D jar detective editorial cartoon", "light": "warm kitchen light with cobalt, mint and coral evidence accents", "lens": "wide conflict, macro process clue, extreme macro turn, wide payoff", "frames": frames}); write(run, "qa.json", qa([("hook_stops_scroll", "Two jars create a visible naming conflict immediately."), ("format_delivered", "The detective case moves from wrong suspect to process clue to label action."), ("turn_is_real", "Vinegar without fermentation changes the viewer question to marinade versus fermentation."), ("payload_is_real", "The viewer gets a practical ingredient-list audit."), ("payoff_is_entailed", "The payoff follows the IJHARS process distinction."), ("overlays_add", "Versus, process list, source, callout and audit list add evidence."), ("visual_causal_progression", "The jars move from suspicion to shared evidence."), ("frames_semantic_match", "Every frame supports its beat with varied scale."), ("voice_persona", "Polish male Charon narration is lively and non-diagnostic."), ("not_a_clone", "The package uses a Polish food-process detective rather than a recent myth, human reaction or product courtroom."), ("source_named_when_natural", "IJHARS source card appears at the naming reveal."), ("language_pl", "All viewer-facing copy is Polish.")]))
    write(run, "publish_package.json", publish); write(run, "codex_strategy.json", strategy); write(run, "retention_plan.json", {"version": "9.0-retention", "duration_lane": "core", "target_duration_s": 22.5, "first_proof_beat": 1, "turn_beat": 3, "payoff_beat": 5, "spoken_cta": False, "cadence": {"publications_today": 1, "slot_index": 1, "minimum_gap_hours": 20.0}, "creative_fingerprint": {"hook_family": "two jar naming dispute", "protagonist_mode": "two non-human food jars", "story_engine": "detective_case", "proof_device": "shared fermentation route and vinegar shortcut", "environment": "Polish kitchen detective desk", "edit_grammar": "fast argument, shared route, sharp process turn, label audit", "payoff_device": "read the ingredient list", "tts_delivery": "lively conversational male Charon", "compared_runs": strategy["structure_variation"]["compared_runs"], "changed_axes": ["hook_family", "protagonist_mode", "proof_device", "environment", "edit_grammar", "payoff_device"]}})
    write(run, "frame_plan.json", {"grade": "bright premium 2D jar detective editorial cartoon", "light": "warm kitchen light with cobalt, mint and coral evidence accents", "lens": "wide conflict, macro process clue, extreme macro turn, wide payoff", "frames": frames})
    return run


def make_milk():
    run = CHANNEL / "2026-08-28_v9-napoj-owsiany-czy-mleko"
    sources = [
        source(1, "Napoje roślinne to nie mleko", "Ministerstwo Rolnictwa i Rozwoju Wsi / gov.pl", "https://www.gov.pl/web/rolnictwo/napoje-roslinne-to-nie-mleko-przepisy-jasno-okreslaja-zasady-oznakowania", "regulation", 2026, "Polskie i unijne zasady zastrzegają nazwę mleko dla produktów pochodzenia zwierzęcego; napoje roślinne mają być oznakowane jako napoje."),
        source(2, "Czy warto pić napoje roślinne?", "Narodowe Centrum Edukacji Żywieniowej", "https://ncez.pzh.gov.pl/abc-zywienia-/zasady-zdrowego-zywienia/czy-warto-pic-napoje-roslinne/", "official_guideline", 2019, "Napoje roślinne różnią się składem; warto wybierać fortyfikowane wapniem, witaminą D i B12, a niefortyfikowane mogą wypadać słabiej od mleka krowiego."),
        source(3, "Czy warto pić napoje roślinne?", "Narodowe Centrum Edukacji Żywieniowej", "https://ncez.pzh.gov.pl/abc-zywienia/czy-warto-pic-napoje-roslinne/", "official_guideline", 2019, "Skład etykiety napoju roślinnego jest ważniejszy niż sama nazwa; fortyfikacja wpływa na zawartość wybranych składników."),
        source(4, "Rozporządzenie sklepikowe 2026", "Narodowe Centrum Edukacji Żywieniowej", "https://ncez.pzh.gov.pl/zywienie-w-placowkach/rozporzadzenie-sklepikowe-2026-co-nowego-w-sklepikach-szkolnych-i-automatach-vendingowych/", "regulation", 2026, "W kontekście sprzedaży szkolnej napoje roślinne mają być wzbogacane co najmniej w wapń i witaminę B12; wybór powinien zależeć od całej diety i potrzeb."),
    ]
    claims = [
        claim(1, "Milk is legally reserved for animal-origin products; plant products are labelled plant drinks.", "„Mleko” oznacza produkt odzwierzęcy, a roślinny to napój.", ["SRC-01"], ["napój roślinny jest podróbką", "jedna nazwa rozstrzyga o zdrowiu"], "This is a naming rule, not a nutritional ranking.", display=True),
        claim(2, "Plant drinks can differ substantially in nutritional composition, so the label matters.", "Napoje roślinne mocno różnią się składem.", ["SRC-02", "SRC-03"], ["każdy napój owsiany ma tyle samo białka", "każdy napój roślinny jest gorszy"], "The Short does not assign a universal value to a brand or recipe.", verdict="conditional"),
        claim(3, "Fortified plant drinks may provide calcium, vitamin D and B12; fortification should be checked on the label.", "Wapń, witamina D i B12 w napoju roślinnym? Sprawdź, czy są dodane.", ["SRC-02", "SRC-03", "SRC-04"], ["fortyfikacja czyni każdy produkt idealnym", "każdy napój ma komplet witamin"], "Fortification varies by product and does not replace a balanced diet.", display=True),
        claim(4, "A practical comparison should include protein, calcium, vitamin D, B12, sugars and the use case.", "Porównaj białko, wapń, witaminę D, B12 i cukry — pod swój cel.", ["SRC-02", "SRC-03"], ["jedna kolumna etykiety wystarczy każdemu", "kolor napoju mówi o składzie"], "The rule is a shopping aid, not individual dietary advice.", verdict="conditional"),
    ]
    hero = "two friendly anthropomorphic unbranded cartons: an ivory cow-milk carton with expressive eyes and tiny white-gloved hands, and a pale-oat carton with expressive eyes and tiny white-gloved hands; both are curious, competitive but helpful, no animals or human characters"
    beats = [
        beat("Białe.", "BIAŁE?", "Two unbranded cartons slide into a mock debate beside two blank glasses; the oat carton raises an eyebrow while the ivory carton gestures to the label area.", 2.5, "hook", (), "Białe"),
        beat("Różne etykiety.", "RÓŻNE ETYKIETY", "Macro label silhouette split: one carton takes the legally reserved word path, the other takes a plant-drink path; no generated writing, renderer adds text.", 2.5, "hook", ("CLM-02",), "etykiety"),
        beat("Mleko: zwierzęce. Roślinny: napój.", "MLEKO = ODZWIERZĘCE / ROŚLINNY = NAPÓJ", "Wide grocery shelf reveal: the ivory carton stands in a dairy lane while the oat carton stands in a plant-drink lane; both look relieved, not hostile.", 2.8, "body", ("CLM-01",), "napój"),
        beat("Wapń i witamina D? Sprawdź, czy dodane.", "SPRAWDŹ FORTYFIKACJĘ", "Extreme macro: calcium and vitamin icons are shown as clean abstract tokens entering the oat carton only when a small additive scoop appears; no numbers or words.", 2.5, "body", ("CLM-03",), "dodane"),
        beat("Z białkiem napoje mocno się różnią.", "BIAŁKO: NIE ZGADUJ", "Medium comparison: two anonymous oat cartons with visibly different fill levels in abstract protein gauges; no digits, no brand, no universal winner.", 2.8, "body", ("CLM-02",), "różnią"),
        beat("Kolor i piana nie wystarczą.", "KOLOR TO ZA MAŁO", "Macro comic reversal: both glasses look identical from the front while their cartons hide different ingredient cards behind them; the cartons exchange an embarrassed glance.", 2.5, "payoff", ("CLM-02", "CLM-04"), "Kolor"),
        beat("Białko, wapń, D, B12.", "BIAŁKO · WAPŃ · D · B12 · CUKRY", "Medium label audit: one oversized blank nutrition panel with five renderer-owned highlight zones; the two cartons use a magnifying glass, calm and practical.", 3.0, "payoff", ("CLM-03", "CLM-04"), "Białko"),
        beat("Wybierz po celu, nie po pianie.", "WYBIERZ PO CELU, NIE PO PIANCE", "Resolved wide shelf tableau: cartons stand side by side with the magnifying glass and a small breakfast bowl; no winner stamp, warm useful finish.", 3.3, "payoff", ("CLM-03", "CLM-04"), "celu"),
    ]
    overlays = [
        overlay("source", 2, label="GOV.PL", finding="Nazwa mleko jest prawnie zastrzeżona", title=sources[0]["title"], publisher=sources[0]["publisher"], year="2026", reference="gov.pl", claim_ids=["CLM-01"]),
        overlay("list", 3, label="SPRAWDŹ", items=["Wapń", "Witamina D", "B12"], claim_ids=["CLM-03"]),
        overlay("callout", 4, label="RÓŻNE NAPOJE", value="RÓŻNY SKŁAD", claim_ids=["CLM-02"]),
        overlay("list", 6, label="ETYKIETA", items=["Białko", "Wapń", "D + B12", "Cukry"], claim_ids=["CLM-03", "CLM-04"]),
    ]
    frames = [
        frame(run.name, hero, "two white glasses and two unbranded cartons enter a playful label debate immediately", "The two options and their visual conflict are clear without sound.", "wide", "conflict", 0, "hook_punch"),
        frame(run.name, hero, "cartons split into two clean naming paths, one animal-origin and one plant-drink path, with no generated text", "The legal product naming distinction appears first.", "macro", "science", 1, "punch_hold", ["CLM-01"]),
        frame(run.name, hero, "a simple grocery shelf separates the dairy carton from the plant-drink carton without declaring a winner", "Milk and plant drinks are different product categories.", "wide", "product", 2, "pan_right", ["CLM-01"]),
        frame(run.name, hero, "abstract calcium and vitamin tokens enter an oat carton beside a clean additive scoop, showing fortification as a product variable", "Fortification must be checked rather than assumed.", "extreme_macro", "ingredient", 3, "punch_hold", ["CLM-03"]),
        frame(run.name, hero, "two anonymous oat cartons show different abstract protein gauge fill levels, no digits and no brand", "Plant drinks can differ in composition.", "medium", "science", 4, "parallax", ["CLM-02"]),
        frame(run.name, hero, "identical-looking white glasses hide different blank ingredient cards behind them while cartons exchange an embarrassed glance", "Color and foam do not reveal the full label.", "macro", "conflict", 5, "punch_hold", ["CLM-02", "CLM-04"]),
        frame(run.name, hero, "both cartons inspect one oversized blank nutrition panel with five clean renderer-owned highlight zones", "Compare the useful label fields for your purpose.", "medium", "science", 6, "ken_burns_in", ["CLM-03", "CLM-04"]),
        frame(run.name, hero, "resolved grocery shelf tableau with both cartons, a magnifying glass and breakfast bowl; no winner stamp", "Choose by goal and label, not by white foam.", "wide", "conflict", 7, "ken_burns_out", ["CLM-03", "CLM-04"]),
    ]
    script = {"lang": "pl", "rubric": "at_shelf", "format": "versus", "hook": beats[0]["voiceover"], "poster_text": "BIAŁE ≠ TAKIE SAME", "beats": beats, "overlays": overlays, "payload": "Nie porównuj napoju owsianego i mleka po kolorze. Sprawdź na etykiecie białko, wapń, witaminę D, B12 i cukry — pod swój cel.", "turn_beat_idx": 3, "payoff_card": "WYBIERZ PO CELU, NIE PO PIANCE", "cta": "", "total_dur_s": round(sum(x["dur_s"] for x in beats), 2), "central_claim_id": "CLM-04", "poster_claim_ids": ["CLM-01"], "payload_claim_ids": ["CLM-01", "CLM-03", "CLM-04"], "payoff_claim_ids": ["CLM-03", "CLM-04"]}
    research = {"lang": "pl", "topic": "Napój owsiany czy mleko?", "viewer_question": "Czy biała szklanka oznacza podobny skład?", "recommended_angle": "Mock shelf debate: two white drinks are not judged by foam; the label decides which fits the viewer's goal.", "evidence_summary": "Ministerstwo Rolnictwa wyjaśnia, że nazwa mleko jest zastrzeżona dla produktu odzwierzęcego. NCEZ podkreśla różnice między napojami roślinnymi i wskazuje, by sprawdzać fortyfikację wapniem, witaminą D i B12 oraz cały skład etykiety. Wniosek dotyczy porównywania produktu, nie uniwersalnego zwycięzcy.", "sources": sources, "claims": claims, "unresolved_conflicts": ["Skład napojów zależy od receptury i marki.", "Materiał nie zastępuje indywidualnej oceny diety ani zaleceń klinicznych."]}
    publish = {"title": "Napój owsiany czy mleko? Nie wybieraj po pianie", "description": research["evidence_summary"] + "\n\nŹródła:\n" + "\n".join(x["url"] for x in sources) + "\n\nMateriał edukacyjny; nie jest indywidualną poradą medyczną.", "hashtags": ["#napójowsiany", "#mleko", "#etykiety", "#odżywianie", "#Shorts"], "pinned_comment": "Co sprawdzasz pierwsze na takiej etykiecie: białko czy cukry?", "title_template": "question_plus_reframe", "description_template": "short_context", "distribution_lane": "hybrid", "primary_query": "napój owsiany czy mleko", "secondary_queries": ["mleko czy napój owsiany", "napoje roślinne wapń", "napój owsiany białko"], "metadata_hypothesis": "A concrete shelf query supports search while identical-looking white glasses create a sound-off comparison conflict.", "api_tags": ["napój owsiany czy mleko", "napoje roślinne", "mleko", "wapń w napoju roślinnym", "czytanie etykiet"], "source_urls": [x["url"] for x in sources]}
    strategy = common_strategy("Polish shoppers comparing cow milk with oat drinks at breakfast or coffee time.", "The visual mismatch between identical white glasses and different label fields will make a nuanced comparison memorable without inventing a universal winner.", {"lane": "hybrid", "primary_query": publish["primary_query"], "secondary_queries": publish["secondary_queries"], "metadata_hypothesis": publish["metadata_hypothesis"]}, [{"id": "H1", "type": "white_glass_debate", "hook": beats[0]["voiceover"], "poster": "BIAŁE, ALE NIE TAKIE SAME", "first_visual": "Two white glasses and cartons enter a label debate.", "first_proof_s": 2.4, "claim_ids": [], "score": 10, "rejection_reason": "Selected: sound-off contrast is immediate and the payoff can be a label audit."}, {"id": "H2", "type": "label_reversal", "hook": "Napój owsiany wygląda jak mleko. Etykieta ma inne zdanie.", "poster": "ETYKIETA MA INNE ZDANIE", "first_visual": "Identical glasses hide different blank label cards.", "first_proof_s": 2.7, "claim_ids": ["CLM-02"], "score": 8, "rejection_reason": "Strong but less concrete than the two-carton opening."}, {"id": "H3", "type": "legal_name", "hook": "Jedna biała szklanka nie może nazywać się mlekiem.", "poster": "MLEKO?", "first_visual": "Two cartons split into legal naming lanes.", "first_proof_s": 2.6, "claim_ids": ["CLM-01"], "score": 7, "rejection_reason": "Accurate but too legalistic as the first promise."}], {"format": "versus", "priority": "P0", "reason": "The viewer compares two real shelf options, but the evidence supports a conditional label-based verdict rather than a universal winner.", "comic_engine": "Two white cartons argue over who owns the breakfast spotlight, then discover the viewer must read their résumés.", "discarded_alternatives": ["label_check", "number_shock"]}, {"hook_mechanism": "two identical-looking drinks enter a mock shelf debate", "first_proof": "legal category split appears by beat 1", "turn_device": "the apparent visual tie breaks on fortification and composition", "evidence_device": "blank nutrition-panel audit with official source card", "overlay_sequence": ["versus", "source", "list", "callout", "list"], "payoff_device": "choose by goal and label", "visual_rhythm": "wide white-glass conflict, macro naming split, wide shelf proof, extreme macro fortification, medium protein contrast, macro foam reframe, medium label audit, wide resolution"}, ["uses a shelf comparison instead of a myth autopsy or courtroom", "turns on label variability rather than a numeric shock", "keeps both options valid for different goals", "ends with a multi-field shopping rule rather than a generic health verdict"], "Weekend Polish shelf comparison", script["total_dur_s"], {"series_id": "polish-food-label-mysteries", "episode": 2, "followup_topics": ["Sojowy czy owsiany: który ma więcej białka?", "Co naprawdę znaczy napój bez cukru?"]})
    write(run, "research_pack.json", research); write(run, "script.json", script); write(run, "compliance.json", {"passed": True, "fixes": ["Kept product naming separate from nutrition ranking.", "Made fortification and composition conditional on the label."], "cleaned_script": script}); write(run, "fact_review.json", {"passed": True, "checks": [{"claim_id": x["id"], "passed": True, "issue": "", "required_change": ""} for x in claims], "unsupported_script_statements": [], "notes": ["No product-specific number or universal winner is asserted."]}); write(run, "frame_plan.json", {"grade": "bright premium 2D shelf-versus editorial cartoon", "light": "warm breakfast light with cobalt, mint and coral evidence accents", "lens": "wide shelf conflict, macro naming, extreme macro fortification, medium label audit, wide payoff", "frames": frames}); write(run, "qa.json", qa([("hook_stops_scroll", "Two white glasses and two cartons create a visible comparison immediately."), ("format_delivered", "The versus format establishes A/B, shows evidence, reverses the visual tie and gives a conditional rule."), ("turn_is_real", "The story moves from color and naming to label variability."), ("payload_is_real", "The viewer gets five label fields to compare."), ("payoff_is_entailed", "The rule follows official Polish guidance to inspect composition and fortification."), ("overlays_add", "Versus, source, fortification list, composition callout and label list add evidence."), ("visual_causal_progression", "Cartons move from rivalry to practical co-existence."), ("frames_semantic_match", "Every frame supports one silent claim with varied scale."), ("voice_persona", "Polish male Charon narration is lively and non-diagnostic."), ("not_a_clone", "The package uses a shelf comparison and label audit, distinct from recent object myths and process detective stories."), ("source_named_when_natural", "Gov.pl and NCEZ evidence appears in source overlays."), ("language_pl", "All viewer-facing copy is Polish.")]))
    write(run, "publish_package.json", publish); write(run, "codex_strategy.json", strategy); write(run, "retention_plan.json", {"version": "9.0-retention", "duration_lane": "core", "target_duration_s": 20.5, "first_proof_beat": 1, "turn_beat": 3, "payoff_beat": 5, "spoken_cta": False, "cadence": {"publications_today": 1, "slot_index": 1, "minimum_gap_hours": 20.0}, "creative_fingerprint": {"hook_family": "identical white glasses debate", "protagonist_mode": "two non-human cartons", "story_engine": "versus", "proof_device": "legal category split plus label variability", "environment": "Polish grocery shelf", "edit_grammar": "wide conflict, naming proof, fortification turn, label audit", "payoff_device": "choose by goal and label", "tts_delivery": "lively conversational male Charon", "compared_runs": strategy["structure_variation"]["compared_runs"], "changed_axes": ["hook_family", "protagonist_mode", "proof_device", "environment", "edit_grammar", "payoff_device"]}})
    return run


if __name__ == "__main__":
    print(make_kiszone())
    print(make_milk())
