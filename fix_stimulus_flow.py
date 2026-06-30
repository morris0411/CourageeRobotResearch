"""Fix fig_study1_stimulus_flow.png: preserve screenshot aspect ratios."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
FIGURES_DIR = ROOT / "Frontiers_LaTeX_Templates" / "figures"

# Source images (do NOT resize except to fit columns)
SEQ_FRAME1 = FIGURES_DIR / "fig1_scene_large_text.png"  # scene only (sequential frame 1)
SEQ_FRAME2 = FIGURES_DIR / "fig2_conflict.png"  # thought bubble (sequential frame 2)
SIM_FRAME  = FIGURES_DIR / "fig2_conflict.png"  # thought bubble (simultaneous — same content)

OUTPUT     = FIGURES_DIR / "fig_study1_stimulus_flow.png"

CANVAS_W   = 1900   # match original composite width
COL_PAD    = 50     # outer / inner column padding
ROW_GAP    = 25     # gap between the two sequential frames (same column)
SECTION_GAP = 60    # vertical space between sequential row and simultaneous row
TOP_PAD    = 20
BOTTOM_PAD = 30
BG         = (255, 255, 255)


def fit_width(img: Image.Image, max_w: int) -> Image.Image:
    """Scale image to fit max_w, preserving aspect ratio. Never upscale."""
    w, h = img.size
    if w <= max_w:
        return img.copy()
    scale = max_w / w
    return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)


def main() -> None:
    img1   = Image.open(SEQ_FRAME1).convert("RGB")
    img2   = Image.open(SEQ_FRAME2).convert("RGB")
    img_s  = Image.open(SIM_FRAME).convert("RGB")

    # Sequential column: each frame fills half the canvas (minus padding)
    col_w  = (CANVAS_W - COL_PAD * 3) // 2   # three gaps: left | mid | right

    f1 = fit_width(img1, col_w)
    f2 = fit_width(img2, col_w)

    seq_h = f1.height + ROW_GAP + f2.height

    # Simultaneous: scale to fit the same col_w but NEVER stretch horizontally
    fs = fit_width(img_s, col_w)

    canvas_h = TOP_PAD + seq_h + SECTION_GAP + fs.height + BOTTOM_PAD
    canvas   = Image.new("RGB", (CANVAS_W, canvas_h), BG)

    # ── Row 1: two sequential frames side by side ────────────────────────────
    x_left  = COL_PAD
    x_right = COL_PAD * 2 + col_w
    y = TOP_PAD

    canvas.paste(f1, (x_left, y))
    canvas.paste(f2, (x_right, y))

    # ── Row 2: simultaneous frame, centered ──────────────────────────────────
    y += seq_h + SECTION_GAP
    x_sim = (CANVAS_W - fs.width) // 2
    canvas.paste(fs, (x_sim, y))

    canvas.save(OUTPUT, dpi=(220, 220))
    print(f"Saved: {OUTPUT}  ({canvas.width}×{canvas.height})")


if __name__ == "__main__":
    main()
