"""Generate all raster assets for the Amazfit Balance "Sequoia" watchface.

Produces, under assets/balance/:
  - bg.png                    480x480 two-tone background (black top / gray bottom)
  - hour_0.png .. hour_9.png  white bold digit glyphs (hour row)
  - minute_0.png .. minute_9.png  black bold digit glyphs (minute row)
  - icon.png                  248x248 circular-masked app-list icon

And under preview/: static renders for visual sanity-checking without a watch.
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(ROOT, "assets", "balance")
PREVIEW_DIR = os.path.join(ROOT, "preview")

SCREEN = 480
CENTER = SCREEN / 2  # 240
SAFE_MARGIN = 10
R_SAFE = CENTER - SAFE_MARGIN  # 230

H_SPACE = 6  # px gutter between the two digits in a pair

BG_BLACK = (0, 0, 0)
BG_GRAY = (65, 65, 65)      # sampled from reference image (bottom band)
HOUR_COLOR = (255, 255, 255)
MINUTE_COLOR = (0, 0, 0)

# Analog second hand: thin, muted, sits behind the digits.
HAND_LENGTH = 195
HAND_WIDTH = 6
HAND_HUB_RADIUS = 7
HAND_COLOR = (120, 120, 128, 170)

FONT_CANDIDATES = [
    "/System/Library/Fonts/SFCompactRounded.ttf",
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
]
VARIATION_NAME = "Black"
REF_SIZE = 1000
DIGITS = "0123456789"


def find_font_path():
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    raise RuntimeError("No suitable bold font found; install Arial Black or edit FONT_CANDIDATES.")


def load_font(font_path, size):
    font = ImageFont.truetype(font_path, size)
    try:
        if VARIATION_NAME.encode() in font.get_variation_names():
            font.set_variation_by_name(VARIATION_NAME)
    except OSError:
        pass  # not a variable font
    return font


def measure(font_path, size):
    font = load_font(font_path, size)
    boxes = {d: font.getbbox(d) for d in DIGITS}
    return font, boxes


def solve_h_row(k, r_safe, h_space):
    """Largest H_row such that a 2-digit pair block of height H_row and the
    worst-case pair width (2*k*H_row + h_space) fits, corner-to-corner,
    inside a circle of radius r_safe (with the block centered on it)."""
    b = h_space / 2
    a = k ** 2 + 1
    bb = 2 * k * b
    cc = b ** 2 - r_safe ** 2
    return (-bb + math.sqrt(bb ** 2 - 4 * a * cc)) / (2 * a)


def compute_layout():
    font_path = find_font_path()
    ref_font, ref_boxes = measure(font_path, REF_SIZE)
    ref_h = max(b[3] - b[1] for b in ref_boxes.values())
    ref_w_max = max(b[2] - b[0] for b in ref_boxes.values())
    k = ref_w_max / ref_h

    h_row = solve_h_row(k, R_SAFE, H_SPACE)

    # sanity check
    worst_pair_w = 2 * k * h_row + H_SPACE
    corner_dist = math.hypot(worst_pair_w / 2, h_row)
    assert corner_dist <= R_SAFE + 0.5, f"layout math failed: {corner_dist} > {R_SAFE}"

    return font_path, k, h_row


def render_digit_set(font_path, target_h, color, out_prefix):
    ref_font, ref_boxes = measure(font_path, REF_SIZE)
    ref_h = max(b[3] - b[1] for b in ref_boxes.values())
    scale = target_h / ref_h
    real_size = max(1, int(REF_SIZE * scale))
    font = load_font(font_path, real_size)
    boxes = {d: font.getbbox(d) for d in DIGITS}

    # shared baseline: same top_pad/bottom_pad for every glyph so digits
    # don't jitter vertically minute to minute.
    top_pad = min(b[1] for b in boxes.values())
    bottom_pad = max(b[3] for b in boxes.values())
    canvas_h = bottom_pad - top_pad

    widths = {}
    for d in DIGITS:
        l, t, r, btm = boxes[d]
        w = r - l
        widths[d] = w
        img = Image.new("RGBA", (w, canvas_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((-l, -top_pad), d, font=font, fill=color)
        img.save(os.path.join(ASSETS_DIR, f"{out_prefix}_{d}.png"))

    return canvas_h, widths


def render_second_hand(out_path):
    """Hand image points straight up (12 o'clock, angle=0), pivot at the
    hub center. Returns (pos_x, pos_y) to place the image so the hub lands
    exactly on the screen center (240, 240)."""
    canvas_w = HAND_HUB_RADIUS * 2 + 4
    canvas_h = HAND_LENGTH + HAND_HUB_RADIUS + 4
    img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pivot_x = canvas_w / 2
    pivot_y = canvas_h - HAND_HUB_RADIUS - 2

    draw.rounded_rectangle(
        [pivot_x - HAND_WIDTH / 2, 2, pivot_x + HAND_WIDTH / 2, pivot_y],
        radius=HAND_WIDTH / 2,
        fill=HAND_COLOR,
    )
    draw.ellipse(
        [pivot_x - HAND_HUB_RADIUS, pivot_y - HAND_HUB_RADIUS, pivot_x + HAND_HUB_RADIUS, pivot_y + HAND_HUB_RADIUS],
        fill=HAND_COLOR,
    )
    img.save(out_path)
    return CENTER - pivot_x, CENTER - pivot_y


def render_bg(split_y, out_path):
    bg = Image.new("RGB", (SCREEN, SCREEN), BG_BLACK)
    draw = ImageDraw.Draw(bg)
    draw.rectangle([0, split_y, SCREEN, SCREEN], fill=BG_GRAY)
    bg.save(out_path)


def render_icon(h_row, out_path, size=248):
    scene = compose_scene(h_row, "10", "09")
    scaled = scene.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(scaled, (0, 0), mask)
    out.save(out_path)


def compose_scene(h_row, hour_str, minute_str, debug=False, hand_angle=None, hand_pos=None):
    bg = Image.open(os.path.join(ASSETS_DIR, "bg.png")).convert("RGBA")

    if hand_angle is not None:
        hand = Image.open(os.path.join(ASSETS_DIR, "second_hand.png"))
        pos_x, pos_y = hand_pos
        layer = Image.new("RGBA", (SCREEN, SCREEN), (0, 0, 0, 0))
        layer.alpha_composite(hand, (int(pos_x), int(pos_y)))
        # rotate the whole layer around the screen center (== hand's pivot);
        # clock angles are clockwise from 12 o'clock, PIL rotates CCW, so negate.
        rotated = layer.rotate(-hand_angle, resample=Image.BICUBIC, center=(CENTER, CENTER))
        bg.alpha_composite(rotated, (0, 0))

    def paste_pair(prefix, s, top_y):
        imgs = [Image.open(os.path.join(ASSETS_DIR, f"{prefix}_{c}.png")) for c in s]
        total_w = sum(i.width for i in imgs) + H_SPACE * (len(imgs) - 1)
        x = int((SCREEN - total_w) / 2)
        for i in imgs:
            bg.alpha_composite(i, (x, int(top_y)))
            x += i.width + H_SPACE

    paste_pair("hour", hour_str, CENTER - h_row)
    paste_pair("minute", minute_str, CENTER)

    if debug:
        d = ImageDraw.Draw(bg)
        d.ellipse(
            [CENTER - R_SAFE, CENTER - R_SAFE, CENTER + R_SAFE, CENTER + R_SAFE],
            outline=(255, 0, 0, 220),
            width=2,
        )
    return bg


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    os.makedirs(PREVIEW_DIR, exist_ok=True)

    font_path, k, h_row = compute_layout()
    print(f"font: {font_path}")
    print(f"measured widest-digit aspect ratio k={k:.4f}")
    print(f"computed H_row={h_row:.1f}px  (R_safe={R_SAFE}px, margin={SAFE_MARGIN}px)")

    render_bg(CENTER, os.path.join(ASSETS_DIR, "bg.png"))

    hour_h, hour_widths = render_digit_set(font_path, h_row, HOUR_COLOR, "hour")
    minute_h, minute_widths = render_digit_set(font_path, h_row, MINUTE_COLOR, "minute")
    print(f"hour glyph canvas height={hour_h}px, minute glyph canvas height={minute_h}px")

    render_icon(h_row, os.path.join(ASSETS_DIR, "icon.png"))

    hand_pos_x, hand_pos_y = render_second_hand(os.path.join(ASSETS_DIR, "second_hand.png"))
    print(f"second hand pos_x={hand_pos_x:.0f} pos_y={hand_pos_y:.0f} (center_x=center_y={CENTER:.0f})")

    widest_pair = max(hour_widths.values()) + H_SPACE
    widest_digit = max(hour_widths, key=hour_widths.get)
    worst_case_pair = widest_digit * 2

    compose_scene(h_row, "10", "09").save(os.path.join(PREVIEW_DIR, "preview_10_09.png"))
    compose_scene(h_row, worst_case_pair, worst_case_pair, debug=True).save(
        os.path.join(PREVIEW_DIR, "preview_worstcase.png")
    )
    compose_scene(
        h_row, "10", "09", hand_angle=42, hand_pos=(hand_pos_x, hand_pos_y)
    ).save(os.path.join(PREVIEW_DIR, "preview_with_hand.png"))
    print(f"widest single digit: '{widest_digit}' ({hour_widths[widest_digit]}px)")
    print(f"worst-case pair used for stress preview: '{worst_case_pair}'")
    print("wrote preview/preview_10_09.png, preview_worstcase.png, preview_with_hand.png")


if __name__ == "__main__":
    main()
