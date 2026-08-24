#!/usr/bin/env python3
"""
assembly_v7g.py — экспериментальная ТЕМА «clinical glass» поверх сборки v7.

Что это. Мудборд владельца (медицинские лендинги/дашборды 2025: светлый воздух, стеклянные
светящиеся органы, белые матовые карточки со скруглением, тёмно-синий текст, зелёные пилюли-
акценты) требует поменять ровно одно — **язык оформления**. Драматургия, гейты качества,
тайминги, звук и контракт `Overlay` остаются v7 без единой правки.

Поэтому здесь НЕ копия `assembly_v7.py`, а тонкий слой: модуль подменяет три вещи в v7 на
время рендера и возвращает всё обратно.

  1. `_CSS`         — целиком новая таблица стилей (тёмная тема → светлая).
  2. `YELLOW`       — цвет караоке-подсветки. Жёлтый #FFDD00 на белом фоне нечитаем.
  3. `_caption_clips` — обёртка: в v7 цвет ВОЗВРАТА слова зашит литералом `#ffffff`
                      прямо в строку GSAP-твина, а белый субтитр на светлом кадре пропадает.

Ключевое отличие темы от v7, из-за которого пришлось трогать не только CSS: **фон стал
светлым**. В v7 читаемость держали белый текст + чёрные тени; здесь ровно наоборот —
тёмно-синий текст, а под ним светлая подложка. Подложку даёт уже существующий полноэкранный
элемент `.vig` (в v7 это была тёмная виньетка): он живёт весь ролик на дорожке 2, между
кадром и графикой, — поэтому светлая размывка низа кадра не потребовала нового элемента
в разметке.

Запуск — через `engine_v7g.py`. Пересборка готового прогона: `--rebuild` там же.
"""
from __future__ import annotations

import assembly_v7 as A7
# Звук темы не касается — профили, микс и семантические события берём у v7 как есть.
from assembly_v7 import (SFX_PROFILES, DEFAULT_SFX_PROFILE, mix, sfx_events,  # noqa: F401
                         _sfx_plan, SAFE_TOP, SAFE_BOTTOM, SAFE_RIGHT)

# --- палитра темы ---------------------------------------------------------------
# Бренд-цвета канала сохранены как якоря (#2A5C82 синий, #4CAF50 зелёный), но переведены
# в светлую схему: синий стал цветом ТЕКСТА, зелёный — цветом акцента и «выигравшей» стороны.
DEEP = "#0D2C46"     # основной текст (тёмно-синий вместо белого)
INK = "#123A5A"      # вторичный текст
NAVY = "#2A5C82"     # бренд-синий: числа, значения
ACC = "#1EA95C"      # акцент/караоке — зелёный, читаемый на белом (жёлтый бренда не читается)
WIN = "#128A4B"      # «побеждающая» сторона versus
BAD = "#E0483C"      # штамп/крестик
GLASS = "rgba(255,255,255,.82)"
WASH = "246,251,255"  # цвет светлой размывки (rgb)

# --- CSS темы -------------------------------------------------------------------
# Селекторы обязаны совпадать с разметкой v7 один в один: модуль стилей заменяется целиком,
# незакрытый селектор = элемент без оформления. Перечень взят из `_overlay_clips`,
# `_caption_clips`, `_headline_clip`, `_payoff_clip`, `_frame_clips`.
_CSS_GLASS = f"""
:root{{--deep:{DEEP};--ink:{INK};--navy:{NAVY};--acc:{ACC};--glass:{GLASS}}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#EDF4FB}}
body{{font-family:Montserrat,Inter,"Helvetica Neue",Arial,sans-serif;
-webkit-font-smoothing:antialiased}}
.fwrap{{position:absolute;inset:0;overflow:hidden}}
.frame{{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover}}

/* Зерно почти выключено: тема стерильная, шум читается как брак печати.
   Полностью убирать нельзя — на широких светлых градиентах вылезает бандинг. */
.grain{{position:absolute;inset:0;mix-blend-mode:soft-light;opacity:.045;
background-image:url("{A7._GRAIN_SVG}");background-size:260px 260px}}

/* Бывшая тёмная виньетка — теперь СВЕТЛАЯ ПОДЛОЖКА. Нижние ~30% кадра забеляются,
   и тёмно-синий субтитр читается независимо от того, что нарисовала модель. */
.vig{{position:absolute;inset:0;background:
linear-gradient(0deg,rgba({WASH},.95) 0%,rgba({WASH},.80) 11%,rgba({WASH},.30) 22%,
rgba({WASH},0) 33%),
radial-gradient(120% 72% at 50% 34%,rgba(255,255,255,.20) 0%,rgba(214,233,247,0) 62%)}}

/* субтитры: тёмно-синий текст + белое свечение вместо белого текста + чёрной тени */
.cap{{position:absolute;left:70px;right:{SAFE_RIGHT + 20}px;bottom:{SAFE_BOTTOM}px;text-align:center;
color:var(--deep);font-size:66px;font-weight:800;line-height:1.14;letter-spacing:-1px;
text-shadow:0 2px 0 rgba(255,255,255,.95),0 0 26px rgba(255,255,255,.95),
0 0 64px rgba(255,255,255,.85)}}
.word{{display:inline-block;margin-right:.34em}}
.word:last-child{{margin-right:0}}
.word.emph{{font-weight:900;padding:0 .10em;margin-right:.42em}}

/* постер кадра-0 */
.headline{{position:absolute;left:56px;right:56px;top:{SAFE_TOP + 60}px;text-align:center;
color:var(--deep);font-weight:900;line-height:1.03;letter-spacing:-3px;
text-shadow:0 2px 0 rgba(255,255,255,.9),0 0 44px rgba(255,255,255,.95)}}
.scrim{{position:absolute;left:0;right:0;top:0;height:900px;
background:linear-gradient(180deg,rgba({WASH},.93) 0%,rgba({WASH},.62) 52%,rgba({WASH},0) 100%)}}
.hl{{color:var(--acc)}}

/* ---- слой информационной графики: матовые стеклянные карточки ---- */
.ov{{position:absolute;left:80px;right:{SAFE_RIGHT + 30}px;top:820px;
color:var(--deep);text-align:center}}
/* общий вид карточки — то, что в мудборде несёт всю информацию */
.ov-stat,.ov-bar,.ov-list,.ov-versus,.ov-timeline{{background:var(--glass);
-webkit-backdrop-filter:blur(26px) saturate(1.15);backdrop-filter:blur(26px) saturate(1.15);
border:2px solid rgba(255,255,255,.95);border-radius:46px;padding:38px 40px;
box-shadow:0 30px 74px rgba(18,58,90,.20),inset 0 2px 0 rgba(255,255,255,.9)}}

.ov-stat .statnum{{font-size:216px;font-weight:900;line-height:.94;letter-spacing:-8px;
color:var(--navy);
background:linear-gradient(158deg,#3EC9A7 0%,#2A8FD0 46%,#1D4E82 100%);
-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}}
.ov-stat .unit{{font-size:92px;margin-left:12px;letter-spacing:-2px}}
.ov-stat .statlab{{margin-top:12px;font-size:50px;font-weight:800;color:var(--ink);opacity:.92}}

.barlab{{display:flex;justify-content:space-between;align-items:baseline;font-size:44px;
font-weight:800;margin-bottom:18px;color:var(--ink)}}
.barval{{color:var(--navy);font-size:58px;font-weight:900}}
.bartrack{{height:42px;background:rgba(42,92,130,.13);border-radius:21px;overflow:hidden}}
.barfill{{height:100%;border-radius:21px;
background:linear-gradient(90deg,#37C98F 0%,#2A8FD0 100%);
box-shadow:0 6px 20px rgba(42,143,208,.42)}}

.vs{{display:flex;align-items:stretch;gap:20px}}
.vscol{{flex:1;background:rgba(255,255,255,.70);border:2px solid rgba(42,92,130,.14);
border-radius:34px;padding:26px 16px 22px}}
.vscol.win{{border-color:rgba(30,169,92,.85);
background:linear-gradient(180deg,rgba(233,251,240,.96),rgba(255,255,255,.86));
box-shadow:0 16px 36px rgba(30,169,92,.20)}}
.vsval{{font-size:70px;font-weight:900;color:var(--navy);line-height:1}}
.vscol.win .vsval{{color:{WIN}}}
.vslab{{font-size:37px;font-weight:700;margin-top:10px;line-height:1.15;color:var(--ink);
opacity:.88}}
.vsmid{{align-self:center;font-size:38px;font-weight:900;color:var(--navy);opacity:.5}}

.lhead{{font-size:47px;font-weight:900;margin-bottom:20px;color:var(--deep)}}
.lrow{{display:flex;align-items:center;gap:18px;text-align:left;
background:rgba(255,255,255,.66);border:2px solid rgba(42,92,130,.10);border-radius:28px;
padding:15px 24px;margin-bottom:13px;font-size:43px;font-weight:800;line-height:1.1;
color:var(--ink)}}
.lrow .lmark{{font-size:38px;font-weight:900;min-width:58px;height:58px;line-height:58px;
text-align:center;border-radius:50%;background:rgba(42,92,130,.14);color:var(--navy)}}
.lrow.ok .lmark{{color:#fff;background:var(--acc)}}
.lrow.no .lmark{{color:#fff;background:{BAD}}}

/* callout — плотная синяя пилюля: единственный элемент темы с инверсией контраста,
   поэтому он и читается как выделенная мысль */
.ov-callout .cotext{{display:inline-block;
background:linear-gradient(140deg,#2E7FB8 0%,#1D4E82 100%);color:#fff;
font-size:56px;font-weight:900;line-height:1.14;padding:22px 40px;border-radius:36px;
box-shadow:0 24px 54px rgba(24,74,120,.36);letter-spacing:-1px}}
.ov-callout .hl{{color:#8CF0B8}}

.ov-stamp{{top:700px}}
.ov-stamp .stamptext{{display:inline-block;background:rgba(255,255,255,.92);
border:9px solid {BAD};color:{BAD};font-weight:900;letter-spacing:4px;padding:14px 40px;
border-radius:30px;max-width:100%;text-transform:uppercase;
box-shadow:0 22px 50px rgba(224,72,60,.24)}}

.tlwrap{{position:relative;height:150px;margin-top:24px}}
.tlline{{position:absolute;left:4%;right:4%;top:26px;height:8px;border-radius:4px;
background:linear-gradient(90deg,rgba(62,201,167,.6),rgba(42,143,208,.6))}}
.tlmark{{position:absolute;top:0;transform:translateX(-50%);width:210px;text-align:center}}
.tldot{{display:block;width:30px;height:30px;border-radius:50%;background:#2A8FD0;
margin:15px auto 0;box-shadow:0 0 0 10px rgba(42,143,208,.16),0 6px 16px rgba(24,74,120,.28)}}
.tllab{{display:block;margin-top:14px;font-size:35px;font-weight:800;line-height:1.1;
color:var(--ink)}}

/* атрибуция: намеренно тихая — сигнал доверия, а не элемент дизайна */
.ov-source{{top:1225px}}
.ov-source .srctext{{display:inline-block;background:rgba(255,255,255,.74);color:#456B88;
font-size:29px;font-weight:700;letter-spacing:.4px;padding:9px 24px;border-radius:999px;
border:2px solid rgba(42,92,130,.14)}}

/* payoff-карточка: тот же кадр 0, но осветлённый — петля «конец = начало» сохраняется */
.poframe{{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover}}
/* Осветление слабее, чем кажется правильным «на глаз в коде»: кадр здесь и без того
   светлый, и подложка .84–.94 из первой версии стёрла его в белый лист — петля
   «конец = начало» работает, только если кадр 0 УЗНАЁТСЯ. Читаемость держит белое
   свечение вокруг букв (.poinner), а не плотность заливки. */
.pocard{{position:absolute;inset:0;
background:linear-gradient(165deg,rgba(240,248,255,.42) 0%,rgba(222,239,253,.56) 54%,
rgba(206,230,248,.66) 100%)}}
.potext{{position:absolute;left:80px;right:80px;top:{SAFE_TOP}px;bottom:{SAFE_BOTTOM - 40}px;
display:flex;align-items:center;justify-content:center}}
.poinner{{width:100%;text-align:center;color:var(--deep);font-weight:900;line-height:1.12;
letter-spacing:-2px;overflow-wrap:break-word;
text-shadow:0 2px 0 rgba(255,255,255,.85),0 0 44px rgba(255,255,255,.92)}}
.potext .hl{{color:{WIN}}}
"""


def _caption_clips_light(*args, **kwargs):
    """Караоке под светлую тему.

    В v7 цвет «слово отзвучало» зашит литералом `color:"#ffffff"` внутрь строки GSAP-твина —
    константы для него нет, а на светлом кадре белое слово исчезает. Перекрашиваем твины
    после генерации: это единственная правка, разметка и тайминги остаются нетронутыми."""
    clips, tweens = _ORIG_CAPTION_CLIPS(*args, **kwargs)
    tweens = [t.replace('color:"#ffffff"', f'color:"{DEEP}"') for t in tweens]
    return clips, tweens


_ORIG_CAPTION_CLIPS = A7._caption_clips


def build_and_render(*args, **kwargs):
    """Рендер v7 в теме v7g. Подмены живут только на время вызова: если в одном процессе
    соберут и v7, и v7g (например, сравнительную катушку), тема не протечёт."""
    saved = (A7._CSS, A7.YELLOW, A7._caption_clips)
    A7._CSS = _CSS_GLASS
    A7.YELLOW = ACC                      # цвет подсветки активного слова
    A7._caption_clips = _caption_clips_light
    try:
        return A7.build_and_render(*args, **kwargs)
    finally:
        A7._CSS, A7.YELLOW, A7._caption_clips = saved
