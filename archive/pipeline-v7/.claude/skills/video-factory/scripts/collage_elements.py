#!/usr/bin/env python3
"""collage_elements.py — «стикер-лист» → отдельные вырезки с альфой (эксперимент v6-layers, T2).

Зачем именно так, а не «вырезать объект из готового кадра» (разведка 2026-08-05):
`hyperframes remove-background` работает локально и бесплатно (CoreML, ~1.4с/кадр), НО это
модель САЛИЕНТНОГО объекта — на многопредметной сцене она выделяет что-то одно и роняет
остальное (с полки с баночками вытащила только полотенце с эвкалиптом). Поэтому элементы
коллажа генерируются СРАЗУ раздельными: один запрос к Nano Banana 2 рисует лист из N
изолированных объектов на плоском фоне, а лист режется здесь — локально и бесплатно.

Экономика: 1 генерация ($0.045) = 4–6 анимируемых элементов вместо одного кадра на бит.

Как режем (никакого AI, только пиксели):
  1) цвет фона = медиана рамки листа шириной 6px;
  2) маска = |цвет − фон| выше порога, морфология на уменьшенной копии;
  3) связные компоненты (BFS по уменьшенной маске — scipy в окружении нет);
  4) сортировка row-major с кластеризацией по строкам, привязка к именам из плана;
  5) альфа = та же цветовая дистанция, растушёванная; despill не нужен — фон нейтральный.

⚠️ Прозрачные объекты (стекло, вода) на близком по яркости фоне кеятся плохо: дистанция
внутри стекла мала, и объект дырявится. Лечится либо контрастным фоном листа (см.
`SHEET_BG_HINT`), либо `--rmbg` на конкретный элемент — тогда для него зовём
hyperframes remove-background, где салиентность как раз работает (объект на листе один в кадре).

CLI (проверка листа до прогона):
    python3 scripts/collage_elements.py <sheet.png> --names kapsulka,proszek,szklanka --out elems/
"""
from __future__ import annotations
import argparse
import subprocess
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

# Подсказка для промпта листа — держим рядом с кодом, который от неё зависит.
# v2 (2026-08-05): фон СПЕЦИАЛЬНО ядовито-пурпурный, а не нейтрально-серый. На сером объекты
# канала (белые капсулы, кремовая бумага, стекло) отличаются от фона слабо — порог приходилось
# держать низким, и края выходили грязными. Пурпурный не встречается ни в одном нашем объекте,
# поэтому цветовая дистанция большая везде, и обрезка чище. Спилл с такого фона снимает _despill.
SHEET_BG_HINT = ("one completely plain flat vivid magenta surface (a saturated chroma-key pink, "
                 "hex #FF00B4), smooth and uniform across the whole frame, free of any writing, "
                 "pattern, texture, shading or branding")

_BG_RING_PX = 6          # ширина рамки, по которой берём цвет фона
_MASK_THRESHOLD = 60     # сумма |ΔRGB| порога объекта; поднят с 34 — фон теперь контрастный
_DOWNSCALE = 4           # во сколько раз ужимаем маску под BFS
_MIN_AREA_FRAC = 0.003   # компоненты мельче этой доли листа — шум


def detect_bg(img: Image.Image) -> np.ndarray:
    a = np.asarray(img.convert("RGB")).astype(int)
    r = _BG_RING_PX
    ring = np.concatenate([a[:r].reshape(-1, 3), a[-r:].reshape(-1, 3),
                           a[:, :r].reshape(-1, 3), a[:, -r:].reshape(-1, 3)])
    return np.median(ring, axis=0)


def _components(mask_small: np.ndarray, min_area: int) -> list[tuple[int, int, int, int]]:
    """BFS по уменьшенной маске. Возвращает bbox'ы в координатах УМЕНЬШЕННОЙ маски."""
    h, w = mask_small.shape
    seen = np.zeros_like(mask_small, bool)
    boxes = []
    for y in range(h):
        for x in range(w):
            if not mask_small[y, x] or seen[y, x]:
                continue
            q = deque([(y, x)])
            seen[y, x] = True
            x0 = x1 = x
            y0 = y1 = y
            n = 0
            while q:
                cy, cx = q.popleft()
                n += 1
                x0, x1 = min(x0, cx), max(x1, cx)
                y0, y1 = min(y0, cy), max(y1, cy)
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and mask_small[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((ny, nx))
            if n >= min_area:
                boxes.append((x0, y0, x1 + 1, y1 + 1))
    return boxes


def _row_major(boxes: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
    """Сортировка «слева направо, сверху вниз» с кластеризацией по строкам: объекты одной
    строки почти никогда не выровнены пиксель в пиксель, поэтому строкой считаем всё, чей
    центр по Y попадает в пределы половины медианной высоты объекта."""
    if not boxes:
        return []
    heights = sorted(b[3] - b[1] for b in boxes)
    tol = max(heights[len(heights) // 2] * 0.5, 1)
    rest = sorted(boxes, key=lambda b: (b[1] + b[3]) / 2)
    out, row = [], [rest[0]]
    for b in rest[1:]:
        cy = (b[1] + b[3]) / 2
        row_cy = sum((r[1] + r[3]) / 2 for r in row) / len(row)
        if abs(cy - row_cy) <= tol:
            row.append(b)
        else:
            out.extend(sorted(row, key=lambda r: (r[0] + r[2]) / 2))
            row = [b]
    out.extend(sorted(row, key=lambda r: (r[0] + r[2]) / 2))
    return out


def _bg_hue_alpha(rgb: np.ndarray, bg: np.ndarray) -> np.ndarray:
    """Множитель альфы, гасящий пиксели, ОКРАШЕННЫЕ в тон фона.

    Порог по цветовой дистанции ловит только чистый фон. Контактная тень объекта — это тот же
    пурпур, но темнее: дистанция до фона большая, маска её пропускает, и вокруг вырезки остаётся
    непрозрачный розовый ободок (проверка 2026-08-05). Здесь сравниваются не яркости, а
    НАПРАВЛЕНИЯ цветности: у тени от пурпурного фона тот же хроматический вектор, что у фона,
    и она гасится независимо от того, насколько она тёмная.

    Возвращает массив 0..1: 1 — цветность не похожа на фон, 0 — совпадает."""
    def chroma(a: np.ndarray) -> np.ndarray:
        return a - a.mean(axis=-1, keepdims=True)

    cb = chroma(bg.astype(float))
    nb = np.linalg.norm(cb)
    if nb < 1e-6:                       # серый фон — гасить по тону нечего
        return np.ones(rgb.shape[:2], dtype=float)
    cp = chroma(rgb.astype(float))
    np_ = np.linalg.norm(cp, axis=-1)
    cos = np.divide((cp * cb).sum(axis=-1), np.maximum(np_ * nb, 1e-6))
    # насыщенные пиксели того же тона, что фон → фон/его тень; слабонасыщенные не трогаем,
    # иначе пострадают тёплые объекты (амбер, орехи), у которых тон частично совпадает.
    sat = np.clip(np_ / (nb * 0.45), 0.0, 1.0)
    return np.clip(1.0 - sat * np.clip((cos - 0.55) / 0.35, 0.0, 1.0), 0.0, 1.0)


def _despill(rgb: np.ndarray, bg: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Снимает подмес цвета фона с полупрозрачной кромки.

    Ядовитый фон даёт чистую маску, но красит края объекта в свой цвет — на пурпурном фоне
    у белой капсулы появляется розовый контур. Для пикселей с частичной альфой возвращаем
    цвет к «неподмешанному»: C_obj = (C - (1-a)*C_bg) / a, с защитой от деления на ноль."""
    a = np.clip(alpha / 255.0, 0.0, 1.0)[..., None]
    edge = (a > 0.02) & (a < 0.98)
    if not edge.any():
        return rgb
    safe = np.maximum(a, 0.15)
    unmixed = (rgb - (1.0 - a) * bg[None, None, :]) / safe
    return np.where(edge, np.clip(unmixed, 0, 255), rgb)


def _matte(crop: Image.Image, bg: np.ndarray, hard_mask: np.ndarray | None = None,
           feather: float = 0.8) -> Image.Image:
    """Альфа = плавная рампа по цветовой дистанции, ОБНУЛЁННАЯ вне жёсткой маски объекта.

    Без обнуления пиксели с дистанцией чуть ниже порога (тень объекта, растушёванный край
    стикера, лёгкий градиент фона) получают частичную альфу — и вокруг вырезки остаётся
    полупрозрачный ПРЯМОУГОЛЬНИК цвета фона. На тёмном navy это видно как голубая коробка
    вокруг предмета (прогон czy-magnez-przedawkowac, 2026-08-05)."""
    a = np.asarray(crop.convert("RGB")).astype(float)
    d = np.abs(a - bg).sum(axis=2)
    alpha = np.clip((d - _MASK_THRESHOLD * 0.5) * 6, 0, 255)
    alpha = alpha * _bg_hue_alpha(a, bg)
    if hard_mask is not None:
        alpha = alpha * hard_mask
    alpha = np.asarray(Image.fromarray(alpha.astype("uint8"))
                       .filter(ImageFilter.GaussianBlur(feather))).astype(float)
    rgb = _despill(a, bg.astype(float), alpha)
    el = Image.fromarray(rgb.astype("uint8"), "RGB").convert("RGBA")
    el.putalpha(Image.fromarray(alpha.astype("uint8")))
    return el


def _merge_to_grid(boxes: list[tuple[int, int, int, int]], n: int, cols: int
                   ) -> list[tuple[int, int, int, int]]:
    """Сводит найденные компоненты к N ячейкам сетки.

    Зачем: «горсть орехов» или «два кубика шоколада» — это ОДИН объект по замыслу, но
    несколько связных компонент по пикселям, и строгое сравнение количества гнало лист на
    перегенерацию (3 лишние генерации на первом прогоне). Раскладка листа сеточная и известна
    заранее, поэтому компоненты просто раскладываются по ячейкам и объединяются в них."""
    if len(boxes) == n:
        return boxes
    if len(boxes) < n:
        return boxes            # объектов меньше ожидаемого — это настоящий брак, вызывающий решит
    rows = -(-n // cols)
    per_row = [cols] * rows
    per_row[-1] = n - cols * (rows - 1)

    def split(items, k, key):
        """Режем упорядоченный список на k групп по k-1 самым большим разрывам."""
        items = sorted(items, key=key)
        if k <= 1 or len(items) <= k:
            return [items] if k <= 1 else [[it] for it in items]
        gaps = sorted(range(1, len(items)),
                      key=lambda idx: key(items[idx]) - key(items[idx - 1]), reverse=True)[:k - 1]
        out, prev = [], 0
        for cut in sorted(gaps):
            out.append(items[prev:cut])
            prev = cut
        out.append(items[prev:])
        return out

    merged = []
    for row_items, want in zip(split(boxes, rows, lambda b: (b[1] + b[3]) / 2), per_row):
        for cell in split(row_items, want, lambda b: (b[0] + b[2]) / 2):
            if not cell:
                continue
            merged.append((min(c[0] for c in cell), min(c[1] for c in cell),
                           max(c[2] for c in cell), max(c[3] for c in cell)))
    return merged


def _clean_rmbg(path: Path, bg: np.ndarray) -> None:
    """Дочищает результат hyperframes remove-background от цвета фона.

    Салиентная модель отдаёт аккуратную маску, но НЕ знает, что фон хромакейный: кромка
    объекта остаётся окрашенной, и на стекле/бутылке получается яркий пурпурный контур
    (прогон czy-magnez-przedawkowac, 2026-08-05). Прогоняем её результат через те же
    подавление тона и деспилл, что и цветовой ключ."""
    im = Image.open(path).convert("RGBA")
    rgb = np.asarray(im.convert("RGB")).astype(float)
    alpha = np.asarray(im.split()[3]).astype(float)
    alpha = alpha * _bg_hue_alpha(rgb, bg)
    rgb = _despill(rgb, bg.astype(float), alpha)
    out = Image.fromarray(rgb.astype("uint8"), "RGB").convert("RGBA")
    out.putalpha(Image.fromarray(alpha.astype("uint8")))
    out.save(path)


def _rmbg(crop_path: Path, out_path: Path) -> bool:
    """Фолбэк для трудных элементов (стекло/вода): локальный маттинг hyperframes.
    Здесь он уместен — на вырезанном кропе объект ОДИН, а это ровно тот случай, для которого
    салиентная модель и предназначена."""
    try:
        subprocess.run(["npx", "--yes", "hyperframes", "remove-background", str(crop_path),
                        "-o", str(out_path)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return out_path.exists()
    except Exception:
        return False


def slice_sheet(sheet_png: str | Path, names: list[str], out_dir: str | Path,
                rmbg_names: set[str] | None = None, pad: int = 6,
                cols: int = 2) -> dict[str, Path]:
    """Режет лист на len(names) вырезок. Порядок имён — row-major (слева направо, сверху вниз).

    Бросает ValueError, если найдено не столько объектов, сколько имён — вызывающий код
    перегенерирует лист. Молча подставлять «что нашлось» нельзя: элементы поедут по битам."""
    sheet_png = Path(sheet_png)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    img = Image.open(sheet_png).convert("RGB")
    W, H = img.size
    bg = detect_bg(img)

    mask = (np.abs(np.asarray(img).astype(int) - bg).sum(axis=2) > _MASK_THRESHOLD)
    small = Image.fromarray((mask * 255).astype("uint8")).resize(
        (W // _DOWNSCALE, H // _DOWNSCALE), Image.BOX).filter(ImageFilter.MaxFilter(5))
    sm = np.asarray(small) > 60
    min_area = int(sm.size * _MIN_AREA_FRAC)
    boxes = _row_major(_merge_to_grid(_components(sm, min_area), len(names), cols))

    if len(boxes) != len(names):
        raise ValueError(f"на листе {sheet_png.name} найдено объектов: {len(boxes)}, "
                         f"а имён в плане: {len(names)} ({', '.join(names)})")

    rmbg_names = rmbg_names or set()
    result: dict[str, Path] = {}
    for name, b in zip(names, boxes):
        x0 = max(int(b[0] * _DOWNSCALE) - pad, 0)
        y0 = max(int(b[1] * _DOWNSCALE) - pad, 0)
        x1 = min(int(b[2] * _DOWNSCALE) + pad, W)
        y1 = min(int(b[3] * _DOWNSCALE) + pad, H)
        crop = img.crop((x0, y0, x1, y1))
        hard = mask[y0:y1, x0:x1].astype(float)
        out = out_dir / f"{name}.png"
        if name in rmbg_names:
            raw = out_dir / f"_raw_{name}.png"
            crop.save(raw)
            if _rmbg(raw, out):
                _clean_rmbg(out, bg)
            else:
                _matte(crop, bg, hard).save(out)
        else:
            _matte(crop, bg, hard).save(out)
        result[name] = out
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Режет стикер-лист на элементы с альфой")
    ap.add_argument("sheet")
    ap.add_argument("--names", required=True, help="имена через запятую, порядок row-major")
    ap.add_argument("--out", required=True)
    ap.add_argument("--rmbg", default="", help="имена (через запятую) под hyperframes remove-background")
    ap.add_argument("--cols", type=int, default=2, help="колонок в сетке листа")
    a = ap.parse_args()
    names = [n.strip() for n in a.names.split(",") if n.strip()]
    rm = {n.strip() for n in a.rmbg.split(",") if n.strip()}
    try:
        res = slice_sheet(a.sheet, names, a.out, rmbg_names=rm, cols=a.cols)
    except ValueError as e:
        print(f"[fail] {e}")
        return 1
    for n, p in res.items():
        print(f"  {n:20s} -> {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
