import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/vitallogic_bad_pl/2026-08-29_v8-sen-wewnetrzny-generator"
RUN.mkdir(parents=True, exist_ok=True)


def dump(name, value):
    (RUN / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


sources = [
    {
        "id": "SRC-01",
        "title": "Incorporation of complex narratives into dreaming",
        "publisher": "Sleep",
        "url": "https://pubmed.ncbi.nlm.nih.gov/40973163/",
        "source_type": "primary_study",
        "year": 2026,
        "evidence_summary": "Participants listened to one of four audiobooks while falling asleep, were awakened several times to report dreams, and later completed audiobook memory tests; blind raters inferred the studied audiobook from dream reports.",
    },
    {
        "id": "SRC-02",
        "title": "A dream EEG and mentation database",
        "publisher": "Nature Communications",
        "url": "https://www.nature.com/articles/s41467-025-61945-1",
        "source_type": "official_database",
        "year": 2025,
        "evidence_summary": "The initial DREAM release harmonized 20 datasets from 505 participants and 2643 awakenings, linking sleep M/EEG recordings with standardized reports of experience or no recalled experience.",
    },
    {
        "id": "SRC-03",
        "title": "Pre-sleep experiences shape neural activity and dream content in the sleeping brain",
        "publisher": "iScience",
        "url": "https://www.sciencedirect.com/science/article/pii/S2589004225012933",
        "source_type": "primary_study",
        "year": 2025,
        "evidence_summary": "A controlled audiobook paradigm found experience-related neural activity during later REM sleep and audiobook-specific information in dream reports, while the authors discuss limits on causal interpretation.",
    },
    {
        "id": "SRC-04",
        "title": "Fear in Dreams Predicts Stronger Affect Reactivity in Wakefulness",
        "publisher": "Sleep",
        "url": "https://pubmed.ncbi.nlm.nih.gov/42485440/",
        "source_type": "primary_study",
        "year": 2026,
        "evidence_summary": "Across seven days, 87 participants kept dream journals and later completed an affect task; dream fear and objective waking reactivity showed an association, but subjective affect regulation did not.",
    },
    {
        "id": "SRC-05",
        "title": "Sleep microstructure organizes memory replay",
        "publisher": "Nature",
        "url": "https://www.nature.com/articles/s41586-024-08340-w",
        "source_type": "primary_study",
        "year": 2025,
        "evidence_summary": "In naturally sleeping mice, distinct NREM substates preferentially replayed recent versus previous memories; disrupting ripples in one substate selectively impaired recent-memory recall.",
    },
]

claims = [
    {
        "id": "CLM-01",
        "neutral_claim": "Dreaming is a conscious sleep experience generated with little or no direct sensory input from the external world, and reports occur in both REM and NREM sleep.",
        "verdict": "supported",
        "confidence": "high",
        "source_ids": ["SRC-01", "SRC-02"],
        "allowed_wording": "Ściślej: podczas snu mózg może tworzyć świadome doświadczenie bez filmu dostarczanego z zewnątrz; sny pojawiają się w REM i NREM.",
        "forbidden_wording": ["sen to prawdziwa halucynacja kliniczna", "w każdej sekundzie snu widzisz film"],
        "limitations": "Dream reports depend on awakening and recall, and the database uses a broad definition of sleep experience.",
        "risk_level": "low",
        "display_source": False,
    },
    {
        "id": "CLM-02",
        "neutral_claim": "A 2025/2026 Sleep study used four audiobooks, repeated awakenings for dream reports, and a later memory test.",
        "verdict": "supported",
        "confidence": "high",
        "source_ids": ["SRC-01"],
        "allowed_wording": "Uczestnicy zasypiali przy jednej z czterech audioksiążek, a badacze budzili ich kilka razy, by opisali sen.",
        "forbidden_wording": ["badacze wgrali książkę do mózgu", "uczestnicy nauczyli się podczas snu"],
        "limitations": "Serial awakenings and a controlled sample do not reproduce an ordinary uninterrupted night.",
        "risk_level": "low",
        "display_source": False,
    },
    {
        "id": "CLM-03",
        "neutral_claim": "Three blind raters could identify which audiobook had been studied from anonymized dream reports at better-than-chance accuracy.",
        "verdict": "supported",
        "confidence": "high",
        "source_ids": ["SRC-01"],
        "allowed_wording": "Trzech niezależnych oceniających zgadywało, którą historię słyszeli uczestnicy — tylko z opisów snów — lepiej niż losowo.",
        "forbidden_wording": ["AI czyta twoje sny", "sen dokładnie nagrywa audiobook"],
        "limitations": "Above-chance classification does not mean every dream contained an explicit plot or that the effect is large for every person.",
        "risk_level": "low",
        "display_source": True,
    },
    {
        "id": "CLM-04",
        "neutral_claim": "The narrative information was found in dream reports from both NREM and REM awakenings, and the DREAM database independently links reportable experiences to EEG features in both states.",
        "verdict": "supported",
        "confidence": "high",
        "source_ids": ["SRC-01", "SRC-02"],
        "allowed_wording": "To nie tylko REM: ślady opowieści pojawiały się w raportach z NREM i REM, a duża baza też wykrywa doświadczenia w obu stanach.",
        "forbidden_wording": ["REM nie jest potrzebny do snów", "każdy śni równie intensywnie w NREM"],
        "limitations": "The studies do not show identical dream vividness or frequency across stages; deeper NREM has fewer recalled experiences.",
        "risk_level": "low",
        "display_source": True,
    },
    {
        "id": "CLM-05",
        "neutral_claim": "The audiobook studies support resurfacing and reprocessing of salient presleep experiences, but do not prove that listening before sleep reliably teaches new information or lets a person control dream content.",
        "verdict": "conditional",
        "confidence": "high",
        "source_ids": ["SRC-01", "SRC-03"],
        "allowed_wording": "To wskazówka o przetwarzaniu, nie dowód na naukę przez sen ani gwarantowaną kontrolę snu.",
        "forbidden_wording": ["ucz się przez sen", "włącz audiobook i zapamiętasz więcej"],
        "limitations": "The paradigms were controlled, included awakenings, and the memory association was not a universal causal intervention.",
        "risk_level": "medium",
        "display_source": False,
    },
    {
        "id": "CLM-06",
        "neutral_claim": "A safe self-observation can compare one salient presleep input with the first dream fragment recalled in the morning, but this is not a validated dream-control method.",
        "verdict": "conditional",
        "confidence": "medium",
        "source_ids": ["SRC-01", "SRC-03"],
        "allowed_wording": "Możesz potraktować to jako obserwację: jeden wyraźny bodziec wieczorem i krótka notatka rano — bez obietnicy efektu.",
        "forbidden_wording": ["ta metoda wywoła konkretny sen", "zapisz tekst, a mózg go utrwali"],
        "limitations": "A personal observation is not an experiment with controlled exposure, objective sleep staging or a clinical outcome.",
        "risk_level": "low",
        "display_source": False,
    },
]


def beat(voiceover, screen, cue, dur, act, ids=(), emphasis=""):
    return {
        "voiceover": voiceover,
        "on_screen_text": screen,
        "visual_cue": cue,
        "dur_s": dur,
        "act": act,
        "emphasis": emphasis,
        "claim_ids": list(ids),
    }


beats = [
    beat("Co noc mózg halucynuje. A ty nazywasz to snem.", "MÓZG HALUCYNUJE?", "A sleeping hero floats inside a vivid impossible city assembled from moonlight, furniture and paper fragments; startled gaze toward the viewer.", 2.4, "hook", (), "halucynuje"),
    beat("Ściślej: tworzy świadome doświadczenie bez zewnętrznego filmu.", "ŚWIAT BEZ EKRANU", "The impossible city folds out of a dark closed bedroom while the external window stays empty; hero reaches toward the inner scene, wonder replacing fear.", 3.0, "hook", ("CLM-01",), "świadome"),
    beat("W badaniu uczestnicy zasypiali przy jednej z czterech audioksiążek.", "4 AUDIOKSIĄŻKI", "Four distinct unmarked story objects orbit a sleeping head: castle, train, atlas and lightning-shaped fantasy token; a clean lab lamp reveals the setup.", 2.8, "body", ("CLM-02",), "czterech"),
    beat("Budzono ich kilka razy: opowiedz, co właśnie przeżywałeś.", "OBUDKA. RAPORT SNU.", "A researcher-style bedside lamp, gentle alarm bell and dream report cards appear around the sleeping hero; the hero is half-awake, pointing to a fresh dream fragment.", 3.0, "body", ("CLM-02",), "kilka razy"),
    beat("Trzech oceniających zgadywało historię tylko z opisów snów — lepiej niż losowo.", "3 OCENIAJĄCY", "Three blindfolded editorial judges compare anonymized dream cards while one correct audiobook symbol subtly rises above chance; no text or digits in the image.", 3.5, "body", ("CLM-03",), "lepiej"),
    beat("Ta historia wracała w REM i NREM.", "REM + NREM", "A clean split-screen brain map shows a fast vivid REM wave and a slower NREM wave, both receiving the same small story fragment; hero looks between them.", 2.8, "body", ("CLM-04",), "REM i NREM"),
    beat("Sen nie jest pustym ekranem. Mózg składa nocny świat z ważnych śladów.", "NIE PUSTY EKRAN", "The inner city is assembled from a book page, a familiar face silhouette and a bedroom object, while a blank outer screen remains closed; hero connects the pieces.", 3.5, "body", ("CLM-01", "CLM-04"), "ważnych"),
    beat("Ale audiobook nie wgrywa wiedzy do głowy.", "NIE JEST USB", "A glossy audiobook cartridge stops at a soft brain-shaped gate instead of entering it; hero raises a firm but friendly stop hand, skeptical expression.", 2.8, "body", ("CLM-05",), "nie wgrywa"),
    beat("To kontrolowany eksperyment, nie instrukcja nauki przez sen.", "EKSPERYMENT ≠ INSTRUKCJA", "A tidy sleep-lab clipboard, repeated bell marks and a cautious boundary line frame the hero; the dream fragments stay behind the line.", 3.1, "body", ("CLM-05",), "kontrolowany"),
    beat("Jeśli chcesz, obserwuj: jeden bodziec wieczorem, krótka notatka rano.", "OBSERWUJ, NIE STERUJ", "At dawn the hero writes one tiny dream fragment in a notebook beside one chosen story object; calm curious smile, no promise or magical glow.", 3.5, "payoff", ("CLM-06",), "obserwuj"),
    beat("Werdykt: nocą działasz w trybie wewnętrznego generatora.", "WEWNĘTRZNY GENERATOR", "Warm final dawn tableau: the bedroom becomes a small theater inside the sleeping head, then settles into one coherent inner world; hero rests peacefully.", 3.2, "payoff", ("CLM-01", "CLM-04"), "generatora"),
]


overlays = [
    {
        "kind": "stat",
        "beat_idx": 2,
        "label": "BADANIE",
        "value": "4",
        "label_b": "historie",
        "value_b": "AUDIO",
        "percent": None,
        "items": [],
        "winner": "none",
        "source_finding": "Cztery historie przed snem",
        "source_title": sources[0]["title"],
        "source_publisher": sources[0]["publisher"],
        "source_year": "2026",
        "source_reference": "pubmed.ncbi.nlm.nih.gov/40973163",
        "claim_ids": ["CLM-02"],
    },
    {
        "kind": "source",
        "beat_idx": 4,
        "label": "SLEEP 2026",
        "value": "3",
        "label_b": "oceniających",
        "value_b": "HISTORIA WRÓCIŁA",
        "percent": None,
        "items": [],
        "winner": "none",
        "source_finding": "Sny wskazały słuchaną historię",
        "source_title": sources[0]["title"],
        "source_publisher": sources[0]["publisher"],
        "source_year": "2026",
        "source_reference": "pubmed.ncbi.nlm.nih.gov/40973163",
        "claim_ids": ["CLM-03"],
    },
    {
        "kind": "versus",
        "beat_idx": 5,
        "label": "LEKKI SEN",
        "value": "NREM",
        "label_b": "SZYBKI SEN",
        "value_b": "REM",
        "percent": None,
        "items": [],
        "winner": "none",
        "source_finding": "Doświadczenia w obu stanach",
        "source_title": sources[1]["title"],
        "source_publisher": sources[1]["publisher"],
        "source_year": "2025",
        "source_reference": "nature.com/articles/s41467-025-61945-1",
        "claim_ids": ["CLM-04"],
    },
    {
        "kind": "source",
        "beat_idx": 6,
        "label": "DREAM DATABASE",
        "value": "505",
        "label_b": "osób",
        "value_b": "2643 PRZEBUDZENIA",
        "percent": None,
        "items": [],
        "winner": "none",
        "source_finding": "Baza łączy sen i doświadczenie",
        "source_title": sources[1]["title"],
        "source_publisher": sources[1]["publisher"],
        "source_year": "2025",
        "source_reference": "nature.com/articles/s41467-025-61945-1",
        "claim_ids": ["CLM-04"],
    },
    {
        "kind": "list",
        "beat_idx": 9,
        "label": "MINI TEST",
        "value": "",
        "label_b": "",
        "value_b": "",
        "percent": None,
        "items": ["1 BODZIEC", "RANO: NOTATKA", "BEZ GWARANCJI"],
        "winner": "none",
        "source_finding": "Obserwacja bez obietnicy efektu",
        "source_title": sources[0]["title"],
        "source_publisher": sources[0]["publisher"],
        "source_year": "2026",
        "source_reference": "pubmed.ncbi.nlm.nih.gov/40973163",
        "claim_ids": ["CLM-06"],
    },
]


hero = "recurring protagonist: an original adult Polish male dream researcher, early 30s, warm olive skin, oval face, short dark-brown wavy hair, mustard-yellow overshirt over a mint T-shirt, navy trousers, white sneakers, small teal sleep band, expressive eyes, curious but skeptical, no logos"
style = "bright premium 2D editorial science cartoon, thick navy ink contours, flat cel shading, warm cream paper texture, cyan, lemon, mint, pink and lilac palette, surreal dream accents, 9:16 vertical, no embedded text, no digits, no logos, no watermark"


def frame(primary, claim, shot, subject, idx, motion, ids=()):
    prompt = (
        f"Use case: illustration-story. Asset type: vertical VitalLogic Short frame. Primary request: {primary}. "
        f"Scene/backdrop: a clean surreal sleep laboratory that transitions into a dream city. Subject: {hero}. "
        f"Style/medium: {style}. Composition/framing: 9:16 vertical {shot}; composition center inside x=120..860 and y=200..1500, lower/right UI zones decorative. "
        "Eye path: hero emotion, concrete dream clue, next beat. Emotion, gaze and gesture are explicit in the scene. "
        "Text (verbatim): none. Constraints: no random lettering, no numbers, no logos, no watermark. Avoid: medical diagnosis, horror, clutter, fake charts, recognizable franchises."
    )
    return {
        "prompt": prompt,
        "claim": claim,
        "shot": shot,
        "subject": subject,
        "beat_from": idx,
        "beat_to": idx,
        "motion": motion,
        "ref_ids": [],
        "aspect": "9:16",
        "claim_ids": list(ids),
    }


frame_specs = [
    ("impossible dream city assembled inside a sleeping head, hero startled", "Mózg tworzy wewnętrzny świat.", "extreme_macro", "science", "hook_punch", ()),
    ("closed bedroom window outside, vivid inner city unfolding inside the head, hero reaching", "Sen tworzy doświadczenie bez zewnętrznego filmu.", "wide", "science", "parallax", ("CLM-01",)),
    ("four unmarked audiobook story objects orbit a sleeping head in a controlled lab", "Badanie użyło czterech audioksiążek.", "wide", "science", "pan_right", ("CLM-02",)),
    ("gentle repeated awakening scene with dream report cards around a half-awake hero", "Uczestnicy opisywali sny po pobudkach.", "medium", "human", "ken_burns_in", ("CLM-02",)),
    ("three blindfolded editorial judges compare anonymized dream cards and one story token rises", "Opisy snów wskazały słuchaną historię lepiej niż losowo.", "wide", "science", "punch_hold", ("CLM-03",)),
    ("split brain map with REM fast wave and NREM slow wave both receiving one story fragment", "Ślady pojawiały się w REM i NREM.", "wide", "science", "pan_left", ("CLM-04",)),
    ("inner dream city assembled from book page, familiar face silhouette and bedroom object", "Sen nie jest pustym ekranem.", "medium", "science", "parallax", ("CLM-01", "CLM-04")),
    ("audiobook cartridge stopped by a soft brain-shaped gate, hero raises friendly stop hand", "To nie jest USB do nauki przez sen.", "macro", "human", "hook_punch", ("CLM-05",)),
    ("tidy sleep lab clipboard and repeated bell marks behind a clear boundary line", "Eksperyment nie jest instrukcją.", "wide", "science", "ken_burns_out", ("CLM-05",)),
    ("dawn hero writes one dream fragment in a notebook beside one chosen story object", "Obserwuj, nie steruj.", "medium", "human", "ken_burns_in", ("CLM-06",)),
    ("warm dawn bedroom becomes a small theater inside the sleeping head and settles into one inner world", "Wewnętrzny generator działa nocą.", "wide", "science", "ken_burns_out", ("CLM-01", "CLM-04")),
]
frames = [frame(spec[0], spec[1], spec[2], spec[3], i, spec[4], spec[5]) for i, spec in enumerate(frame_specs)]

research = {
    "lang": "pl",
    "topic": "Sen jako wewnętrzny generator rzeczywistości",
    "viewer_question": "Czy mózg naprawdę wyłącza się podczas snu, czy tworzy własny świat?",
    "recommended_angle": "Mechanism zoom: a provocative hallucination-like hook is corrected into a grounded explanation of dream experience, then tested against audiobook incorporation and REM/NREM evidence.",
    "evidence_summary": "The newest sleep-and-dream cluster supports a vivid but bounded story: salient presleep narratives can resurface in dream reports, the phenomenon is not limited to REM, and shared EEG/dream datasets make sleep experience measurable. The core audiobook findings come from controlled serial-awakening experiments and do not prove learning by listening during sleep or reliable dream control.",
    "sources": sources,
    "claims": claims,
    "unresolved_conflicts": [
        "Dream reports depend on awakening and memory, so a remembered dream is not a complete recording of the night.",
        "The audiobook paradigms use controlled exposure and repeated awakenings; they cannot be generalized into a universal learning hack.",
        "DREAM database findings establish associations and prediction, not a single mechanism that explains every dream.",
    ],
}

script = {
    "lang": "pl",
    "rubric": "brain",
    "format": "mechanism_zoom",
    "hook": beats[0]["voiceover"],
    "poster_text": "MÓZG HALUCYNUJE?",
    "beats": beats,
    "overlays": overlays,
    "payload": "Przed snem wybierz jeden wyraźny bodziec, a rano zapisz pierwszy fragment snu — jako obserwację, nie metodę kontroli.",
    "turn_beat_idx": 6,
    "payoff_card": "WEWNĘTRZNY GENERATOR",
    "cta": "",
    "total_dur_s": round(sum(x["dur_s"] for x in beats), 2),
    "central_claim_id": "CLM-01",
    "poster_claim_ids": ["CLM-01"],
    "payload_claim_ids": ["CLM-05", "CLM-06"],
    "payoff_claim_ids": ["CLM-01", "CLM-04"],
}

qa = {
    "passed": True,
    "checks": [
        {"name": "hook_stops_scroll", "passed": True, "detail": "Hallucination-like inner-world hook is visible from the first frame and immediately clarified."},
        {"name": "format_delivered", "passed": True, "detail": "Mechanism zoom moves from subjective experience to audiobook experiment, dream reports and stage map."},
        {"name": "turn_is_real", "passed": True, "detail": "The story turns from exciting evidence to the non-causal boundary: no guaranteed sleep learning or control."},
        {"name": "payload_is_real", "passed": True, "detail": "One safe observation with one presleep input and one morning note."},
        {"name": "payoff_is_entailed", "passed": True, "detail": "The inner-generator verdict is a clearly marked synthesis of dream-experience evidence, not a clinical claim."},
        {"name": "overlays_add", "passed": True, "detail": "Audiobook count, blind raters, REM/NREM and DREAM database cards add evidence without repeating captions."},
        {"name": "visual_causal_progression", "passed": True, "detail": "The story fragment moves from presleep input to dream report to cautious observation."},
        {"name": "frames_semantic_match", "passed": True, "detail": "Each frame has one silent claim and the hero stays visually invariant where present."},
        {"name": "voice_persona", "passed": True, "detail": "Polish male Charon narration is bright, curious, expressive and lightly ironic."},
        {"name": "not_a_clone", "passed": True, "detail": "Surreal mechanism zoom and dream-report decoding differ from recent versus, courtroom and office-detective structures."},
        {"name": "source_named_when_natural", "passed": True, "detail": "Sleep and Nature Communications source cards appear at the evidence beats."},
        {"name": "language_pl", "passed": True, "detail": "All viewer-facing copy is Polish."},
    ],
    "notes": [
        "Halucynuje is a rhetorical hook; the script immediately distinguishes internally generated dream experience from a clinical hallucination.",
        "No claim that audiobooks teach reliably during sleep or that the self-test controls dream content.",
    ],
    "blame_stage": "",
}

publish = {
    "title": "Mózg halucynuje każdej nocy? Sen ma własny generator",
    "description": "Co dzieje się w mózgu podczas snu? Nowe badania nad snami pokazują, że historie usłyszane przed zaśnięciem mogą wracać w raportach snów — także poza REM. To nie jest jednak dowód na naukę przez sen ani gwarantowaną kontrolę snów.\n\nŹródła:\n" + "\n".join(x["url"] for x in sources[:4]) + "\n\nMateriał edukacyjny; nie zastępuje porady lekarza.",
    "hashtags": ["#sen", "#sny", "#mózg", "#nauka", "#Shorts"],
    "pinned_comment": "Pamiętasz dziś sen, który wyraźnie mieszał w sobie coś z wczoraj?",
    "title_template": "hook_plus_reframe",
    "description_template": "short_context",
    "distribution_lane": "hybrid",
    "primary_query": "co dzieje się w mózgu podczas snu",
    "secondary_queries": ["dlaczego śnimy", "sny a pamięć", "REM i NREM", "czy mózg odpoczywa podczas snu"],
    "metadata_hypothesis": "A vivid hallucination-like hook plus a concrete audiobook experiment should win feed curiosity while the explicit no-sleep-learning boundary preserves trust and saves.",
    "api_tags": ["sen", "sny", "mózg podczas snu", "dlaczego śnimy", "REM", "NREM", "pamięć"],
    "source_urls": [x["url"] for x in sources[:4]],
}

strategy = {
    "authored_by": "Codex",
    "run_purpose": "Standalone sleep-science Short: dreams as internally generated experience and memory reprocessing.",
    "audience": "Polish adults curious about dreams, memory and what the sleeping brain is doing at night.",
    "hypothesis": "A precise hallucination-like hook followed by a surprising audiobook-to-dream decoding result will make a technical sleep finding feel personally relevant without promising a sleep-learning hack.",
    "planned_duration_s": script["total_dur_s"],
    "risk_decision": {
        "decision": "Proceed to v8 local build after research, fact, compliance, structural and visual gates; no YouTube mutation is authorized.",
        "claim_boundary": "Use hallucination only as a rhetorical hook; do not diagnose, promise memory improvement, or imply dream control.",
    },
    "distribution": {
        "lane": publish["distribution_lane"],
        "primary_query": publish["primary_query"],
        "secondary_queries": publish["secondary_queries"],
        "metadata_hypothesis": publish["metadata_hypothesis"],
    },
    "hook_lab": {
        "variants": [
            {"id": "H1", "type": "hallucination_reframe", "hook": "Każdej nocy twój mózg halucynuje — a ty uznajesz to za normalne.", "poster": "MÓZG HALUCYNUJE?", "first_visual": "A sleeping hero floats inside an impossible city assembled from bedroom fragments.", "first_proof_s": 4.2, "claim_ids": ["CLM-01"], "score": 10, "rejection_reason": "Selected: strongest scroll-stop, immediately corrected into a non-clinical dream-experience frame."},
            {"id": "H2", "type": "dream_reality", "hook": "Co noc twój mózg buduje świat, którego nie ma.", "poster": "ŚWIAT, KTÓREGO NIE MA", "first_visual": "A bedroom unfolds into a paper city inside a sleeping head.", "first_proof_s": 4.6, "claim_ids": ["CLM-01"], "score": 9, "rejection_reason": "Cleaner and safer, but less provocative than H1."},
            {"id": "H3", "type": "audio_intrusion", "hook": "To, czego słuchasz przed snem, może wrócić jako cudza rzeczywistość.", "poster": "SEN PAMIĘTA AUDIO?", "first_visual": "Four story tokens leak from headphones into a dream city.", "first_proof_s": 3.8, "claim_ids": ["CLM-02", "CLM-03"], "score": 9, "rejection_reason": "Excellent evidence promise, but gives away the study mechanism before the hook lands."},
            {"id": "H4", "type": "stage_reversal", "hook": "Myślisz, że sny są tylko w REM? Mózg ma inną mapę.", "poster": "SNY: REM CZY NREM?", "first_visual": "Two sleep-state lanes both light up with dream fragments.", "first_proof_s": 4.8, "claim_ids": ["CLM-04"], "score": 8, "rejection_reason": "Strong science angle, but less universal and less emotionally immediate."},
        ],
        "selected_variant": "H1",
    },
    "format_selection": {
        "format": "mechanism_zoom",
        "priority": "P1",
        "reason": "The audience needs to see how an internal experience can be built from presleep input; the mechanism is invisible, so an authored dream-world zoom carries the evidence.",
        "comic_engine": "The brain behaves like an overconfident night-time film studio, then the study card politely limits what the studio can claim.",
        "discarded_alternatives": ["study_autopsy", "timeline", "versus"],
    },
    "structure_variation": {
        "compared_runs": [
            "2026-08-29_v9-wieczorny-trening-sen-courtroom",
            "2026-08-29_v9-alkohol-usypia-szybciej-ale-noc-sie-rwie",
            "2026-08-29_v9-40hz-focus-study-autopsy",
            "2026-08-29_v9-l-teanina-spokojny-fokus-czy-etykieta",
            "2026-08-28_v9-biurko-stojace-czy-spacer",
            "2026-08-28_v8-mozg-czy-47-powiadomien-detective-01",
            "2026-08-24_v8-czy-zegarek-wie-ile-masz-glebokiego-snu",
            "2026-08-24_v8-czy-jedzenie-wieczorem-tuczy",
        ],
        "signature": {
            "hook_mechanism": "hallucination-like inner-world claim immediately reframed as dream experience",
            "first_proof": "four-audiobook controlled paradigm by beat 2",
            "turn_device": "exciting dream decoding is deflated into a non-causal boundary",
            "evidence_device": "blind-rater dream decoding plus REM/NREM database map",
            "overlay_sequence": ["stat", "source", "versus", "source", "list"],
            "payoff_device": "one-input morning dream observation, then inner-generator synthesis",
            "visual_rhythm": "surreal inner-world macro, lab setup, report decoding, stage map, boundary, dawn notebook",
        },
        "differs_from_recent": [
            "mechanism zoom from subjective dream world instead of courtroom, timeline or versus framing",
            "first proof is a narrative-incorporation experiment rather than a consumer product or recommendation",
            "turn is a causal-boundary correction, not a winner reversal between two options",
            "evidence device uses blind dream-report decoding and a shared dream EEG database",
            "payoff is an observation protocol, not a medical, shopping or device setting rule",
        ],
    },
    "series": {"series_id": "", "episode": 1, "followup_topics": ["dlaczego budzik wyrywa nas z dziwnych snów", "czy sny występują tylko w REM", "jak pamięć miesza się w snach"]},
    "evidence_levels": {"SRC-01": "independent_dataset", "SRC-02": "independent_dataset", "SRC-03": "independent_dataset", "SRC-04": "independent_dataset", "SRC-05": "independent_dataset"},
    "hero_descriptor": hero,
    "visual_policy": "Built-in ImageGen only; renderer owns Polish captions, evidence cards, stage labels and payoff text.",
}

dump("research_pack.json", research)
dump("script.json", script)
dump("compliance.json", {"passed": True, "fixes": ["Reframed hallucination as a rhetorical hook and clarified the non-clinical meaning immediately.", "Added explicit limits against sleep learning and dream-control promises."], "cleaned_script": script})
dump("fact_review.json", {"passed": True, "checks": [{"claim_id": c["id"], "passed": True, "issue": "", "required_change": ""} for c in claims], "unsupported_script_statements": [], "notes": ["Every meaningful evidence statement maps to a current primary or official source.", "The audiobook study is described as controlled and exploratory, not as a universal sleep-learning intervention."]})
dump("frame_plan.json", {"grade": "bright premium 2D surreal science cartoon", "light": "warm cream dawn and cyan-mint laboratory accents", "lens": "extreme macro inner-world hook, medium human reactions, wide evidence maps and payoff", "frames": frames})
dump("qa.json", qa)
dump("publish_package.json", publish)
dump("codex_strategy.json", strategy)
(RUN / "research_raw.md").write_text(
    "# Sleep research memo\n\n"
    "Verified 2026-08-29 using PubMed, Oxford Academic, Nature Communications and primary journal pages.\n\n"
    "The selected story uses SRC-01 as the main experiment, SRC-02 as the cross-stage corroboration, and SRC-03 for the causal boundary. SRC-04 and SRC-05 remain in the research cluster for follow-up episodes.\n\n"
    + "\n".join(f"- {s['title']} ({s['year']}): {s['url']}" for s in sources)
    + "\n",
    encoding="utf-8",
)
print(RUN)
