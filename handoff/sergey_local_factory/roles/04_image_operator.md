# Роль: Оператор генерации изображений (стадия 4)

Инструкция для кода-оператора ComfyUI (не LLM). Вход: `FramePlan` (JSON). Выход: `frames/*.png` 9:16.
**Читай docs/IMAGE_PROMPTING.md** (параметры по моделям, консистентность, safe-зоны).

Задачи:
- Загрузить сохранённый ComfyUI-workflow под выбранную модель; дёргать через HTTP API (`POST /prompt` на :8188).
- Для каждого `frame` подставить: `prompt`, `seed`, разрешение (нативное для модели, см. IMAGE_PROMPTING §3),
  параметры (steps/CFG/sampler/scheduler из таблицы §2). Для FLUX/Qwen/Z-Image negative — пустой.
- Запуск ComfyUI на Mac: `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 python main.py --force-fp16 --highvram`.
- Тяжёлые модели (FLUX-dev, Qwen) — через GGUF-ноду, иначе сброс на CPU и OOM.
- **Консистентность**: держать общий seed для статичных сцен / применять Style-LoRA канала (IP-Adapter на MPS
  для FLUX медленный — по возможности LoRA). Стиль-якорь уже в промптах от visual_director.
- Если модель ломает 9:16 (режет головы) — генерировать 1024×1024 и центрированно кропать в 9:16 (ffmpeg/PIL).
- Опц. апскейл ×2 (Real-ESRGAN / Upscayl) при генерации в 512×896.
- Писать кадры в `runs/<...>/frames/frame_XX.png` атомарно; логировать модель+seed+параметры в `runs/<...>/frames/manifest.json` (воспроизводимость).
