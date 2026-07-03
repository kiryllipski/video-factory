# README — video-factory для Codex (Сергею)

Привет! Это самодостаточный порт нашего навыка **video-factory** — фабрики одного вертикального
ролика (9:16, Reels/Shorts/TikTok) под монетизацию. Он завёлся и проверен на моём стеке; тебе —
адаптировать провайдеров кадров/голоса под свой. Ниже: что внутри, как запустить как есть, и где
именно менять код под себя.

---

## 1. TL;DR — как это работает

Модель-агент (в Codex — твоя) пишет **весь текст**: сценарий, комплаенс, план кадров, QA — по правилам
ретеншена из ресёрча. Наружу уходит только то, что модель не умеет: **кадры** (image-модель) и
**голос** (TTS). Сборка (Ken Burns + караоке-субтитры + мукс) — локально через hyperframes + ffmpeg.

Точка входа для Codex — `AGENTS.md` (Codex читает его сам). Полные правила письма — `skill/`.

## 2. Структура бандла

```
AGENTS.md                     # ← точка входа Codex: роль, пайплайн, гейты, окружение
README_SERGEY.md              # ← этот файл
requirements.txt / .env.example
skill/                        # оригинальный навык (правила — НЕ выбрасывать)
  SKILL.md
  references/authoring_guide.md      # КАК писать script.json + frame_plan.json
  references/qa_and_compliance.md    # правила комплаенса + чек-лист QA
  scripts/build_media.py             # единственная «тратящая» стадия (кадры+голос+сборка)
  scripts/validate_run.py            # валидация JSON схемами ДО трат
  scripts/_common.py                 # находит корень (autopilot_factory/ + orchestration/)
autopilot_factory/
  schemas.py        # Pydantic-контракты (Script/FramePlan/…) — ЗАКОН, менять осторожно
  engine.py         # synth_audio (per-beat TTS+whisper) + assemble; CHANNEL_VOICE
  assembly.py       # hyperframes HTML → mp4 (Ken Burns, караоке) — провайдер-независим
  cost_tracker.py   # учёт токенов → runs/<run>/cost.json
  prompts/          # системные роли для текстовых стадий (в Codex их пишешь ты; оставлены для справки)
  channels/<ch>/    # studio_context.md (тон/визуал/стоп-листы) + media_plan.md (очередь тем)
  runs/             # сюда пишутся прогоны
orchestration/
  image_agent.py    # ← КАДРЫ (сейчас Gemini Nano Banana). ТОЧКА ЗАМЕНЫ №1
  audio_agent.py    # ← ГОЛОС (сейчас Gemini TTS).          ТОЧКА ЗАМЕНЫ №2
  gemini_agent.py   # текстовый раннер Gemini (в Codex не нужен, импортируется engine — оставить)
examples/           # валидные артефакты реального ролика (FedEx) — образец контрактов
```

## 3. Запуск «как есть» (на нашем стеке — Gemini)

```bash
# 0) окружение
cp .env.example .env && $EDITOR .env         # вписать GEMINI_API_KEY
pip3 install -r requirements.txt
export PATH="$HOME/.nvm/versions/node/v22.x/bin:$PATH"   # Node >= 20 обязателен, см. §6

# 1) агент (Codex) пишет script.json / compliance.json / frame_plan.json / qa.json
#    в autopilot_factory/runs/<date>_<slug>/  — по правилам из skill/references/*.md

# 2) валидация до трат
python3 skill/scripts/validate_run.py autopilot_factory/runs/<date>_<slug>

# 3) медиа + сборка (тратит деньги)
python3 skill/scripts/build_media.py autopilot_factory/runs/<date>_<slug> --channel biz_failures
# → out.mp4 + cost.json в папке прогона
```

## 4. Точки замены под свой стек

Контракты (`schemas.py`) и сборка (`assembly.py`) от провайдера **не зависят**. Меняешь только два
файла — сохраняя сигнатуры, чтобы `engine`/`build_media` не трогать:

**№1 — Кадры: `orchestration/image_agent.py`**
```python
def generate_image(model: str, prompt: str, aspect_ratio: str = "9:16",
                   out: str = "", refs=None) -> bytes:
    # refs: список путей к референс-кадрам (консистентность стиля, hybrid anchor). Верни PNG-байты;
    # если out задан — запиши файл. Формат 9:16 задавать НА УРОВНЕ КОНФИГА провайдера, не текстом.
```
Замени тело на свой провайдер (SDXL/Flux/DALLE/Midjourney-API/локальный ComfyUI). Требования:
9:16, поддержка reference-изображений для консистентности (иначе style-drift между кадрами).
Есть ретрай ×3 на пустой ответ — оставь аналог, иначе пакетная сборка падает на одном кадре.

**№2 — Голос: `orchestration/audio_agent.py`**
```python
def generate_speech(text: str, voice="Charon", style="", model="tts", out="", speed=1.0) -> bytes:
    # верни WAV-байты (моно ок). speed — постпроцесс ffmpeg atempo. Верни валидный WAV на диск (out).
```
Замени на ElevenLabs/OpenAI TTS/локальный XTTS и т.п. Голоса/подача заданы per-channel в
`engine.CHANNEL_VOICE` — поправь под голоса своего провайдера:
```python
CHANNEL_VOICE = {
  "biz_failures": ("Charon", "wise, cynical baritone, sharp", 1.25),
  "psychology":   ("Kore",   "intriguing, insightful, energetic", 1.15),
  "wealth_viz":   ("Orus",   "confident, clear, authoritative", 1.15),
}
```
⚠️ В `style` НЕ пиши tired/slow/measured — модели читают это буквально и замедляют речь.

**Текстовые стадии** (scriptwriter/compliance/visual/qa): в Codex их пишет твоя модель по
`AGENTS.md` + `skill/references/*.md`. `prompts/*.md` и `gemini_agent.py` оставлены только для справки/
совместимости импорта — звать Gemini на текст не нужно.

## 5. Контракты (schemas.py) — коротко

- `Script`: `hook` (≤200), `beats[3..20]` (`voiceover`, `on_screen_text` 2–4 слова, `visual_cue`,
  `dur_s` 0.8–4.0), `cta` (≤160), `total_dur_s` 15–90 (оптимум 30–50).
  ⚠️ TTS читает только `beats[].voiceover` — текст хука должен быть в `beats[0].voiceover`.
- `FramePlan`: единые `grade`/`light`/`lens` на весь ролик; `frames` — РОВНО один на бит, тот же
  порядок и тайминг; `motion` из {ken_burns_in/out, pan_left/right, parallax, static_hold}.
- `ComplianceVerdict`: `passed`, `fixes[]`, `cleaned_script` (дальше в дело идёт он).
- `QAReport`: advisory, не блокирует.

Смотри рабочие образцы в `examples/fedex_*.json`.

## 6. Окружение и грабли (проверено болью)

- **Node ≥ 20 (лучше 22).** `hyperframes render` под Node 18 падает `SyntaxError ... styleText` —
  причём в самом конце, когда кадры и озвучка УЖЕ оплачены. Всегда `node -v` перед `build_media`.
  `nvm alias default 22` у нас в неинтерактивном шелле не всегда подхватывался — надёжнее
  `export PATH=".../v22.x/bin:$PATH"`.
- **Если рендер (стадия 6) упал, а кадры+озвучка готовы** — не гоняй `build_media` заново (переплатишь
  за TTS). Пересобери только сборку на готовых `runs/<run>/frames/` + `runs/<run>/audio/voice.wav`,
  вызвав `engine.assemble(...)` (durations бери из `engine._wav_dur` по `audio/beatN.wav`,
  караоке-тайминг — `engine._transcribe_words`, это локальный whisper, бесплатно).
- **Тяжёлую сборку — строго последовательно**, один прогон за раз (каждый поднимает headless-Chrome).
- Python 3.9 ок; `google-genai`, `pydantic>=2`, `requests`. ffmpeg 8.x.

## 7. Что править под свою нишу

`channels/<channel>/studio_context.md` — тон, рубрики, формулы хука, визуальный код, стоп-листы, CTA.
`channels/<channel>/media_plan.md` — очередь тем. Заведи свой канал = новая папка с этими двумя файлами
+ строчка в `CHANNEL_VOICE`. Комплаенс-правила ниши держи в `studio_context.md` §7 (их читает стадия 4).

Вопросы — пиши. Погнали 🚀
