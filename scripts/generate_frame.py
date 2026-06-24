#!/usr/bin/env python3
"""영상용 프레임 템플릿 이미지를 Nano Banana로 1회 생성 (종목 비종속).

용도:
  각 씬에 공통으로 깔리는 하이테크 외곽 프레임/보더 디자인.
  중앙 영역은 투명하게 마스킹되어, 기존 씬 콘텐츠(헤더·사진·카드)가
  그대로 보이고 가장자리만 통일된 브랜드 룩으로 장식된다.

실행:
  python scripts/generate_frame.py                  # 새로 생성 (덮어쓰기)
  python scripts/generate_frame.py --keep-existing  # 이미 있으면 유지

환경변수: GEMINI_API_KEY (없거나 호출 실패 시 PIL 절차적 생성으로 자동 대체 — API 의존 0).
출력: data/frame-template.png (RGBA, 1080×1920)

※ 1회 생성 후 git 커밋해서 재사용. 새 디자인이 필요할 때만 다시 실행.
"""

import os
import sys
from pathlib import Path

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

OUT_PATH    = Path("data/frame-template.png")
W, H        = 1080, 1920
BORDER_PX   = 34    # 상/좌/우 보더 두께 (px) — 기존 씬 카드/배지가 PAD=40부터 시작하므로 그보다 얇게
BOTTOM_PX   = 14    # 하단 보더 두께 (px) — AI 생성 고지 밴드(scene 2) 텍스트가 하단 ~24px까지 내려와 더 얇게
CORNER_R    = 22    # 중앙 투명 영역의 모서리 라운드 반경

# ⚠ 보더 두께는 기존 씬 레이아웃(weekly_video_prep.py의 PAD=40 카드 여백, 하단 AI 고지
#   밴드 텍스트)을 가리지 않도록 실측 후 정한 값이다. 키우기 전에 build_scene_image()의
#   가장자리 콘텐츠(헤더 배지·하단 고지문) 위치를 다시 확인할 것.
FRAME_PROMPT = f"""
A futuristic high-tech decorative frame border design, vertical 9:16, ultra-high resolution.
The image must show ONLY a THIN outer border/frame decoration around the edges.
The CENTER area (everything except a thin {BORDER_PX}px strip on top/left/right and a
{BOTTOM_PX}px strip on the bottom) should be a flat solid dark navy color (#0a0e1a) —
completely empty, no content.

Border decoration features (only along the edges, thin {BORDER_PX}px strips, {BOTTOM_PX}px on bottom):
- Top edge: thin glowing cyan neon line, abstract tech motif
- Bottom edge: thin futuristic accent line with magenta-cyan gradient glow
- Left and right edges: thin vertical neon glow lines
- Four corners: small glowing tech bracket accents (HUD-style corner marks)
- Overall style: cyberpunk, high-tech aesthetic, neon cyan + magenta + electric purple highlights
- Background of border area: deep navy/black with subtle starfield texture

Strict requirements:
- The border decoration must stay THIN and close to the edges — it must NOT bleed inward
- No text, no letters, no numbers, no watermark, no logo
- High contrast between glowing border and dark empty center
"""

_NANO_BANANA_MODELS = [
    "gemini-2.5-flash-image",
    "gemini-3.1-flash-image-preview",
]


def generate_with_nano_banana() -> bytes | None:
    if not GEMINI_API_KEY:
        print("⚠ GEMINI_API_KEY 환경변수 필요", file=sys.stderr)
        return None
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=GEMINI_API_KEY)
    for model_id in _NANO_BANANA_MODELS:
        try:
            print(f"🎨 {model_id}로 프레임 생성 중...")
            response = client.models.generate_content(
                model=model_id,
                contents=FRAME_PROMPT,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio="9:16"),
                ),
            )
            for part in response.parts:
                if part.inline_data:
                    return part.inline_data.data
        except Exception as e:
            print(f"   ⚠ {model_id} 실패: {e}", file=sys.stderr)
    return None


NAVY_BG  = (10, 14, 26)
CYAN     = (0, 229, 255)
MAGENTA  = (255, 0, 170)
PURPLE   = (150, 80, 255)
_FRAME_RNG_SEED = 7


def generate_with_pil_fallback() -> bytes:
    """Nano Banana 미가용(키 없음/호출 실패) 시 절차적 생성으로 대체 — API 의존 0.

    FRAME_PROMPT가 묘사하는 모티프(상단 네온 라인+노드, 하단 마젠타→시안 그라디언트,
    좌우 네온 라인, 모서리 HUD 브래킷, 미세 별빛)를 PIL/numpy로 직접 합성한다.
    결과는 punch_center_transparent()로 동일하게 중앙이 투명 처리되므로
    Nano Banana 경로와 합류점이 같다.
    """
    import random
    from io import BytesIO

    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter

    print("🎨 PIL 절차적 생성으로 프레임 합성 중...")
    rng = random.Random(_FRAME_RNG_SEED)

    def additive_blend(base, glow, strength=1.0):
        b = np.asarray(base.convert("RGB"), dtype=np.float32)
        g = np.asarray(glow.convert("RGB"), dtype=np.float32)
        out = np.clip(b + g * strength, 0, 255).astype(np.uint8)
        return Image.fromarray(out)

    def draw_starfield(draw, count=110):
        for _ in range(count):
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            r = rng.uniform(0.5, 1.6)
            v = rng.randint(70, 180)
            draw.ellipse([x - r, y - r, x + r, y + r], fill=(v, v, min(255, v + 30)))

    def draw_top_ticks(draw):
        """상단 라인 위 작은 노드 점 — 회로 느낌을 얇은 보더 안에서도 살짝 표현."""
        y = BORDER_PX * 0.5
        for x in range(80, W - 80, 130):
            draw.ellipse([x - 2.5, y - 2.5, x + 2.5, y + 2.5], fill=CYAN)

    def draw_corner_accents(draw):
        """HUD 스타일 모서리 브래킷 — 보더 두께(BORDER_PX) 안에서만 그려 콘텐츠 침범 방지."""
        s = BORDER_PX * 0.8
        for (cx, cy, dx, dy) in ((0, 0, 1, 1), (W, 0, -1, 1), (0, H, 1, -1), (W, H, -1, -1)):
            draw.line([(cx + dx * s, cy + dy * 5), (cx + dx * 5, cy + dy * 5),
                       (cx + dx * 5, cy + dy * s)], fill=PURPLE, width=3, joint="curve")

    def draw_bottom_gradient_bar(layer):
        """하단 마젠타→시안 그라디언트 — BOTTOM_PX 두께 전체를 채우는 얇은 라인."""
        grad = np.linspace(0, 1, W, dtype=np.float32).reshape(1, W, 1)
        col_a, col_b = np.array(MAGENTA, dtype=np.float32), np.array(CYAN, dtype=np.float32)
        row = (col_a * (1 - grad) + col_b * grad).astype(np.uint8)
        band = np.repeat(row, BOTTOM_PX, axis=0)
        layer.paste(Image.fromarray(band), (0, H - BOTTOM_PX))

    base = Image.new("RGB", (W, H), NAVY_BG)
    draw_starfield(ImageDraw.Draw(base))

    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.line([(0, 4), (W, 4)], fill=CYAN, width=3)
    gd.line([(4, 0), (4, H - BOTTOM_PX)], fill=CYAN, width=2)
    gd.line([(W - 4, 0), (W - 4, H - BOTTOM_PX)], fill=CYAN, width=2)
    draw_top_ticks(gd)
    draw_corner_accents(gd)
    draw_bottom_gradient_bar(glow)

    base = additive_blend(base, glow.filter(ImageFilter.GaussianBlur(6)), strength=1.1)
    base = additive_blend(base, glow.filter(ImageFilter.GaussianBlur(1.0)), strength=0.6)

    buf = BytesIO()
    base.convert("RGBA").save(buf, "PNG")
    return buf.getvalue()


def punch_center_transparent(img_bytes: bytes) -> "Image.Image":
    """생성된 이미지의 중앙 영역을 강제로 투명화 (라운드 사각형 마스크)."""
    from io import BytesIO
    from PIL import Image, ImageDraw

    base = Image.open(BytesIO(img_bytes)).convert("RGBA")
    if base.size != (W, H):
        base = base.resize((W, H), Image.LANCZOS)

    # 알파 마스크 생성: 가장자리만 불투명, 중앙은 투명 (하단은 BOTTOM_PX로 더 얇게 —
    # AI 생성 고지 밴드 텍스트가 하단 ~24px까지 내려오므로 그보다 얇아야 가리지 않음)
    mask = Image.new("L", (W, H), 0)        # 0 = 투명
    md = ImageDraw.Draw(mask)
    md.rectangle([0, 0, W, H], fill=255)   # 전체 불투명
    md.rounded_rectangle(
        [BORDER_PX, BORDER_PX, W - BORDER_PX, H - BOTTOM_PX],
        radius=CORNER_R, fill=0,
    )                                       # 중앙 라운드 사각형 = 투명

    base.putalpha(mask)
    return base


def main():
    keep_existing = "--keep-existing" in sys.argv
    if keep_existing and OUT_PATH.exists():
        print(f"✅ 기존 프레임 유지: {OUT_PATH}")
        return

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    raw = generate_with_nano_banana()
    if not raw:
        print("ℹ️ Nano Banana 미사용 — PIL 절차적 생성으로 대체")
        raw = generate_with_pil_fallback()

    framed = punch_center_transparent(raw)
    framed.save(OUT_PATH, "PNG")
    print(f"✅ 프레임 저장 완료: {OUT_PATH} (1080×1920, RGBA)")
    print(f"   보더 상/좌/우 {BORDER_PX}px · 하단 {BOTTOM_PX}px, 중앙 라운드 모서리 {CORNER_R}px 투명")
    print(f"   ※ git 커밋 후 모든 영상에 자동 적용됩니다.")


if __name__ == "__main__":
    main()
