"""SRT 파싱 → 모션 자막 프레임 생성 — 강조 자동 감지 + 세그먼트별 스타일링"""
import math
import os
import random
import srt
from concurrent.futures import ThreadPoolExecutor
from os import cpu_count
from PIL import Image, ImageDraw, ImageFont
from app.core.config import WIDTH, HEIGHT, FPS, FONTS_DIR

# --- 폰트 ---
FONT_FILES = [
    "Pretendard-Black.otf",
    "Pretendard-Bold.otf",
    "GmarketSansBold.otf",
    "NanumSquareRoundEB.ttf",
    "NanumSquareB.ttf",
    "BlackHanSans-Regular.ttf",
    "DoHyeon-Regular.ttf",
    "Jua-Regular.ttf",
    "Gasoek-One.ttf",
    "SingleDay-Regular.ttf",
    "Dongle-Bold.ttf",
]
AVAILABLE_FONTS = [str(FONTS_DIR / f) for f in FONT_FILES if (FONTS_DIR / f).exists()]
if not AVAILABLE_FONTS:
    AVAILABLE_FONTS = [str(FONTS_DIR / "NanumSquareB.ttf")]

# --- 효과 ---
EFFECTS = [
    "pop_in", "slide_up", "bounce", "slide_down", "scale_pulse",
    "zoom_in", "zoom_out", "rotate_in", "slide_right", "typewriter",
]
Y_POSITIONS = [0.35, 0.42, 0.50, 0.38, 0.45, 0.40, 0.48, 0.36, 0.44, 0.46]
TEXT_MARGIN = 40  # 화면 양쪽 여백 (px)

# --- 강조 키워드 (자동 감지) ---
EMPHASIS_KEYWORDS = {
    "대박": {"scale": 1.5, "color": (0, 255, 255)},
    "최고": {"scale": 1.5, "color": (0, 255, 255)},
    "맛집": {"scale": 1.4, "color": (255, 215, 0)},
    "추천": {"scale": 1.4, "color": (255, 215, 0)},
    "인정": {"scale": 1.3, "color": (255, 150, 150)},
    "완벽": {"scale": 1.4, "color": (0, 255, 128)},
    "꿀팁": {"scale": 1.4, "color": (255, 200, 100)},
    "핫플": {"scale": 1.4, "color": (255, 100, 200)},
    "감성": {"scale": 1.3, "color": (180, 160, 255)},
    "할인": {"scale": 1.5, "color": (255, 80, 80)},
    "무료": {"scale": 1.5, "color": (255, 80, 80)},
    "한정": {"scale": 1.3, "color": (255, 150, 50)},
    "특별": {"scale": 1.3, "color": (255, 200, 100)},
    "프리미엄": {"scale": 1.3, "color": (255, 215, 0)},
    "오픈": {"scale": 1.4, "color": (0, 255, 200)},
    "1등": {"scale": 1.5, "color": (255, 215, 0)},
    "N0.1": {"scale": 1.4, "color": (255, 215, 0)},
}
CTA_KEYWORDS = ["방문", "예약", "클릭", "지금", "바로", "확인", "문의"]

# --- 자동 색상 팔레트 (기본값) ---
AUTO_COLORS = [
    (255, 255, 255),
    (0, 255, 255),
    (255, 215, 0),
    (255, 140, 200),
    (100, 255, 200),
    (255, 160, 80),
    (150, 200, 255),
    (255, 255, 100),
]

# --- 색상 스키마 ---
COLOR_SCHEMES: dict[str, list[tuple[int, int, int]]] = {
    "neon": [
        (0, 255, 255), (255, 0, 255), (0, 255, 128),
        (255, 255, 0), (128, 0, 255), (0, 200, 255),
    ],
    "warm": [
        (255, 140, 80), (255, 200, 60), (255, 100, 100),
        (255, 180, 100), (255, 120, 60), (255, 160, 80),
    ],
    "cool": [
        (80, 200, 255), (100, 255, 220), (130, 180, 255),
        (0, 220, 200), (100, 160, 255), (80, 255, 200),
    ],
    "pastel": [
        (255, 180, 200), (180, 200, 255), (200, 255, 200),
        (255, 220, 180), (220, 180, 255), (180, 255, 230),
    ],
    "rainbow": [
        (255, 80, 80), (255, 180, 50), (255, 255, 80),
        (80, 255, 80), (80, 180, 255), (200, 100, 255),
    ],
    "gold": [
        (255, 215, 0), (255, 200, 80), (255, 230, 120),
        (255, 190, 50), (255, 220, 100), (255, 210, 60),
    ],
    "pink": [
        (255, 100, 200), (255, 150, 180), (255, 80, 160),
        (255, 120, 220), (230, 100, 255), (255, 140, 200),
    ],
    "mint": [
        (100, 255, 200), (150, 255, 220), (80, 230, 180),
        (120, 255, 210), (100, 240, 190), (140, 255, 200),
    ],
}


# ========== 유틸 ==========

def _get_font(size: int, font_path: str = "") -> ImageFont.FreeTypeFont:
    path = font_path or AVAILABLE_FONTS[0]
    return ImageFont.truetype(path, size)


def _find_emphasis(text: str) -> dict | None:
    """텍스트에서 강조 키워드 찾기 (가장 긴 매치 우선)"""
    best = None
    for kw, info in EMPHASIS_KEYWORDS.items():
        if kw in text:
            if best is None or len(kw) > len(best["keyword"]):
                best = {"keyword": kw, "scale": info["scale"], "color": info["color"]}
    if best:
        return best
    for kw in CTA_KEYWORDS:
        if kw in text:
            return {"keyword": kw, "scale": 1.3, "color": (255, 100, 100)}
    return None


def _dim_color(color: tuple, factor: float = 0.8) -> tuple:
    """색상을 약간 어둡게"""
    return tuple(max(int(c * factor), 0) for c in color)


# ========== 텍스트 스타일링 ==========

def _style_text(text: str, _index: int, base_color: tuple) -> list[dict]:
    """텍스트 → 세그먼트 기반 라인 구조. 강조 부분은 크기/색상 분리."""
    emphasis = _find_emphasis(text)

    # 짧은 텍스트 (6자 이하): 한 덩어리
    if len(text) <= 6:
        if emphasis:
            return [{"segments": [
                {"text": text, "size": 140, "color": emphasis["color"], "emphasis": True}
            ]}]
        return [{"segments": [
            {"text": text, "size": 130, "color": base_color}
        ]}]

    # 강조 키워드가 있으면 세그먼트 분리
    if emphasis:
        kw = emphasis["keyword"]
        idx = text.find(kw)
        before = text[:idx]
        after = text[idx + len(kw):]
        base_size = 90

        segments = []
        if before.strip():
            segments.append({"text": before, "size": base_size, "color": _dim_color(base_color)})
        segments.append({
            "text": kw,
            "size": int(base_size * emphasis["scale"]),
            "color": emphasis["color"],
            "emphasis": True,
        })
        if after.strip():
            segments.append({"text": after, "size": base_size, "color": _dim_color(base_color)})
        return [{"segments": segments}]

    # 긴 텍스트: 두 줄 분리
    if len(text) > 12:
        mid = len(text) // 2
        split_pos = mid
        for offset in range(min(5, mid)):
            for pos in [mid + offset, mid - offset]:
                if 0 < pos < len(text) and text[pos] in " ,!?":
                    split_pos = pos + 1
                    break
            else:
                continue
            break
        line1 = text[:split_pos].strip()
        line2 = text[split_pos:].strip()
        return [
            {"segments": [{"text": line1, "size": 78, "color": _dim_color(base_color)}]},
            {"segments": [{"text": line2, "size": 100, "color": base_color}]},
        ]

    return [{"segments": [{"text": text, "size": 100, "color": base_color}]}]


# ========== SRT 파싱 ==========

def parse_srt_to_motion(srt_content: str, effect: str = "",
                        color_scheme: str = "") -> list[dict]:
    entries = list(srt.parse(srt_content))
    subtitles = []
    scheme_colors = COLOR_SCHEMES.get(color_scheme)

    for i, entry in enumerate(entries):
        text = entry.content.strip().replace("\n", " ")
        font_path = AVAILABLE_FONTS[i % len(AVAILABLE_FONTS)]

        # 색상 결정: 스키마 > 자동
        if scheme_colors:
            base_color = scheme_colors[i % len(scheme_colors)]
        else:
            base_color = AUTO_COLORS[i % len(AUTO_COLORS)]

        lines = _style_text(text, i, base_color)
        chosen_effect = effect if effect in EFFECTS else EFFECTS[i % len(EFFECTS)]

        has_emphasis = any(
            any(seg.get("emphasis") for seg in line.get("segments", []))
            for line in lines
        )

        subtitles.append({
            "start": entry.start.total_seconds(),
            "end": entry.end.total_seconds(),
            "lines": lines,
            "y_center": Y_POSITIONS[i % len(Y_POSITIONS)],
            "effect": chosen_effect,
            "font_path": font_path,
            "has_emphasis": has_emphasis,
        })

    return subtitles


# ========== 모션 효과 ==========

def apply_effect(effect: str, t: float, has_emphasis: bool = False) -> dict:
    """모션 효과 → scale, alpha, offsets, angle, emphasis_scale, emphasis_flash"""
    anim_t = 0.25
    p = min(t / anim_t, 1.0)

    fx = {
        "scale": 1.0, "alpha": 1.0,
        "y_offset": 0, "x_offset": 0, "angle": 0.0,
        "emphasis_scale": 1.0, "emphasis_flash": 0.0,
    }

    if effect == "pop_in":
        if p < 0.5:
            fx["scale"] = p / 0.5 * 1.3
        elif p < 1.0:
            fx["scale"] = 1.3 - (p - 0.5) / 0.5 * 0.3
        if t > anim_t:
            fx["scale"] = 1.0 + math.sin((t - anim_t) * 4) * 0.03
        fx["alpha"] = min(p * 3, 1.0)

    elif effect == "slide_up":
        ease = 1 - (1 - p) ** 3
        fx["alpha"] = min(p * 2.5, 1.0)
        fx["y_offset"] = int((1 - ease) * 200)

    elif effect == "slide_down":
        ease = 1 - (1 - p) ** 3
        fx["alpha"] = min(p * 2.5, 1.0)
        fx["y_offset"] = int((1 - ease) * -200)

    elif effect == "slide_right":
        ease = 1 - (1 - p) ** 3
        fx["alpha"] = min(p * 2.5, 1.0)
        fx["x_offset"] = int((1 - ease) * -WIDTH * 0.4)

    elif effect == "bounce":
        if p < 0.4:
            fx["y_offset"] = int((1 - p / 0.4) * -280)
        elif p < 0.65:
            fx["y_offset"] = int(math.sin((p - 0.4) / 0.25 * math.pi) * -50)
        elif p < 0.85:
            fx["y_offset"] = int(math.sin((p - 0.65) / 0.2 * math.pi) * -20)
        fx["alpha"] = min(p * 3, 1.0)

    elif effect == "scale_pulse":
        if p < 0.5:
            fx["scale"] = p / 0.5 * 1.2
        elif p < 1.0:
            fx["scale"] = 1.2 - (p - 0.5) / 0.5 * 0.2
        if t > anim_t:
            fx["scale"] = 1.0 + math.sin((t - anim_t) * 3 * math.pi) * 0.05
        fx["alpha"] = min(p * 3, 1.0)

    elif effect == "zoom_in":
        if p < 1.0:
            fx["scale"] = 0.3 + 0.7 * (1 - (1 - p) ** 2)
        if t > anim_t:
            fx["scale"] = 1.0 + math.sin((t - anim_t) * 2) * 0.02
        fx["alpha"] = min(p * 4, 1.0)

    elif effect == "zoom_out":
        if p < 1.0:
            fx["scale"] = 1.8 - 0.8 * (1 - (1 - p) ** 2)
        if t > anim_t:
            fx["scale"] = 1.0 + math.sin((t - anim_t) * 2) * 0.02
        fx["alpha"] = min(p * 3, 1.0)

    elif effect == "rotate_in":
        ease = 1 - (1 - p) ** 3
        if p < 1.0:
            fx["angle"] = (1 - ease) * 15.0
            fx["scale"] = 0.5 + 0.5 * ease
        fx["alpha"] = min(p * 3, 1.0)

    elif effect == "typewriter":
        fx["alpha"] = min(p * 5, 1.0)
        if p < 0.3:
            fx["x_offset"] = int(random.uniform(-3, 3))
            fx["y_offset"] = int(random.uniform(-2, 2))

    # 강조 폭발 효과 (키워드가 있을 때)
    if has_emphasis:
        ep = min(t / 0.2, 1.0)  # 0.2초 동안 폭발
        if ep < 0.3:
            fx["emphasis_scale"] = 2.0 - (ep / 0.3) * 0.7   # 2.0 → 1.3
        elif ep < 0.7:
            fx["emphasis_scale"] = 1.3 - ((ep - 0.3) / 0.4) * 0.15  # 1.3 → 1.15
        else:
            fx["emphasis_scale"] = 1.15  # 약간 크게 유지
        # 순간 플래시
        if ep < 0.12:
            fx["emphasis_flash"] = 1.0 - ep / 0.12

    return fx


# ========== 렌더링 ==========

def _draw_outlined_text(draw: ImageDraw.ImageDraw,
                        x: int, y: int, text: str,
                        font: ImageFont.FreeTypeFont,
                        color: tuple, alpha: int, scale: float):
    """외곽선 + 그림자 + 본문 렌더링"""
    ow = max(int(5 * scale), 1)
    shadow = max(int(3 * scale), 1)
    # 그림자
    draw.text((x + shadow, y + shadow), text, font=font,
              fill=(0, 0, 0, int(alpha * 0.6)))
    # 외곽선
    for dx in range(-ow, ow + 1):
        for dy in range(-ow, ow + 1):
            if dx * dx + dy * dy <= ow * ow:
                draw.text((x + dx, y + dy), text, font=font,
                          fill=(0, 0, 0, alpha))
    # 본문
    r, g, b = color
    draw.text((x, y), text, font=font, fill=(r, g, b, alpha))


def _measure_segments(draw, segments, fx, font_path):
    """세그먼트 치수 측정"""
    seg_data = []
    max_h = 0
    for seg in segments:
        sz = seg["size"]
        if seg.get("emphasis"):
            sz = int(sz * fx.get("emphasis_scale", 1.0))
        sz = max(int(sz * fx["scale"]), 1)
        fp = seg.get("font_path", font_path)
        font = _get_font(sz, fp)
        bbox = draw.textbbox((0, 0), seg["text"], font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        seg_data.append({"seg": seg, "font": font, "w": tw, "h": th})
        max_h = max(max_h, th)
    return seg_data, max_h


def _seg_color(seg: dict, fx: dict) -> tuple:
    """세그먼트 색상 (플래시 효과 적용)"""
    color = seg["color"]
    if seg.get("emphasis") and fx.get("emphasis_flash", 0) > 0:
        f = fx["emphasis_flash"]
        return tuple(min(int(c + (255 - c) * f), 255) for c in color)
    return color


def _render_line_segments(img: Image.Image, draw: ImageDraw.ImageDraw,
                          seg_data: list, base_y: int, line_h: int,
                          alpha: int, fx: dict) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """한 줄의 세그먼트들을 렌더링 (중앙 정렬)"""
    if not seg_data:
        return img, draw

    total_w = sum(sd["w"] for sd in seg_data) + 6 * max(len(seg_data) - 1, 0)
    needs_transform = fx["angle"] != 0.0

    if needs_transform:
        # 회전이 필요하면 임시 이미지에 렌더 후 회전
        pad = 60
        tmp = Image.new("RGBA", (total_w + pad * 2, line_h + pad * 2), (0, 0, 0, 0))
        tmp_draw = ImageDraw.Draw(tmp)
        x = pad
        for sd in seg_data:
            seg = sd["seg"]
            y = pad + (line_h - sd["h"]) // 2
            color = _seg_color(seg, fx)
            _draw_outlined_text(tmp_draw, x, y, seg["text"],
                                sd["font"], color, alpha, fx["scale"])
            x += sd["w"] + 6

        tmp = tmp.rotate(-fx["angle"], expand=True, resample=Image.BICUBIC)
        paste_x = (WIDTH - tmp.width) // 2 + fx.get("x_offset", 0)
        paste_x = max(TEXT_MARGIN, min(paste_x, WIDTH - TEXT_MARGIN - tmp.width))
        paste_y = base_y - pad + (line_h - tmp.height) // 2
        img.paste(tmp, (paste_x, paste_y), tmp)
        draw = ImageDraw.Draw(img)
    else:
        start_x = (WIDTH - total_w) // 2 + fx.get("x_offset", 0)
        if total_w <= WIDTH - 2 * TEXT_MARGIN:
            start_x = max(TEXT_MARGIN, min(start_x, WIDTH - TEXT_MARGIN - total_w))
        else:
            start_x = (WIDTH - total_w) // 2  # 너무 넓으면 중앙 정렬
        x = start_x
        for sd in seg_data:
            seg = sd["seg"]
            y = base_y + (line_h - sd["h"]) // 2
            color = _seg_color(seg, fx)
            _draw_outlined_text(draw, x, y, seg["text"],
                                sd["font"], color, alpha, fx["scale"])
            x += sd["w"] + 6

    return img, draw


def _render_frame(args) -> None:
    """단일 프레임 렌더링"""
    frame_idx, subtitles, output_dir = args
    t = frame_idx / FPS
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for sub in subtitles:
        if sub["start"] <= t < sub["end"]:
            local_t = (t - sub["start"]) / (sub["end"] - sub["start"])
            fx = apply_effect(sub["effect"], local_t,
                              sub.get("has_emphasis", False))
            if fx["alpha"] < 0.01:
                continue

            font_path = sub.get("font_path", AVAILABLE_FONTS[0])
            a = int(255 * fx["alpha"])

            # 라인별 높이 측정
            all_seg_data = []
            line_heights = []
            for line in sub["lines"]:
                segments = line.get("segments", [])
                sd, max_h = _measure_segments(draw, segments, fx, font_path)
                all_seg_data.append(sd)
                line_heights.append(max_h)

            total_h = sum(line_heights) + 20 * max(len(line_heights) - 1, 0)
            base_y = int(HEIGHT * sub["y_center"] - total_h / 2) + fx["y_offset"]

            for sd, lh in zip(all_seg_data, line_heights):
                img, draw = _render_line_segments(img, draw, sd, base_y, lh, a, fx)
                base_y += lh + 20

    img.save(f"{output_dir}/frame_{frame_idx:04d}.png")


# ========== 진입점 ==========

def generate_frames(srt_content: str, duration: float, output_dir: str,
                    workers: int = 0, effect: str = "",
                    color_scheme: str = "") -> str:
    """SRT → 모션 자막 프레임 PNG 시퀀스 생성"""
    os.makedirs(output_dir, exist_ok=True)
    subtitles = parse_srt_to_motion(srt_content, effect=effect,
                                     color_scheme=color_scheme)
    total_frames = int(duration * FPS)

    if workers == 0:
        workers = min(cpu_count(), 4)

    args = [(i, subtitles, output_dir) for i in range(total_frames)]

    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            pool.map(_render_frame, args)
    else:
        for a in args:
            _render_frame(a)

    return output_dir
