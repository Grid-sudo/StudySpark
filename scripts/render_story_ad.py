"""Render the Study Spark vertical motion-design ad."""
from array import array
from pathlib import Path
import math
import random
import subprocess
import tempfile
import wave

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "study-spark-story.mp4"
W, H, FPS = 720, 1280, 30
SEGMENTS = [3.0, 3.15, 3.0, 3.55]
TRANSITION = 0.17
TOTAL = sum(SEGMENTS)
LIME = "#D7F275"
INK = "#101511"
PAPER = "#F6F7F0"
MID = "#8D9B77"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_HEAVY = "/System/Library/Fonts/Supplemental/Arial Black.ttf"
FONT_NARROW = "/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf"
FONTS = {}


def font(size, weight="bold"):
    family = {"regular": FONT_REG, "bold": FONT_BOLD, "heavy": FONT_HEAVY, "narrow": FONT_NARROW}[weight]
    key = (size, family)
    if key not in FONTS:
        FONTS[key] = ImageFont.truetype(family, size)
    return FONTS[key]


def fit_font(text, max_width, size, weight="heavy", min_size=24):
    while size > min_size and font(size, weight).getlength(text) > max_width:
        size -= 1
    return font(size, weight)


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def ease(v):
    v = clamp(v)
    return v * v * (3 - 2 * v)


def out_cubic(v):
    v = clamp(v)
    return 1 - (1 - v) ** 3


def text(im, x, y, value, f, color, alpha=255, stroke_width=0, stroke_fill=None):
    box = f.getbbox(value, stroke_width=stroke_width)
    pad = stroke_width + 3
    layer = Image.new("RGBA", (max(1, box[2] - box[0] + pad * 2), max(1, box[3] - box[1] + pad * 2)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((pad - box[0], pad - box[1]), value, font=f, fill=color, stroke_width=stroke_width, stroke_fill=stroke_fill)
    if alpha < 255:
        layer.putalpha(layer.getchannel("A").point(lambda a: a * alpha // 255))
    im.alpha_composite(layer, (round(x + box[0] - pad), round(y + box[1] - pad)))


def centered(im, y, value, f, color, alpha=255):
    text(im, (W - f.getlength(value)) / 2, y, value, f, color, alpha)


def slide_text(im, x, y, value, f, color, p, start=0.0, duration=0.24, direction=38, max_width=None):
    q = out_cubic((p - start) / duration)
    if max_width is not None:
        f = fit_font(value, max_width, f.size, "heavy")
    text(im, x, y + (1 - q) * direction, value, f, color, round(255 * q))


def star4(draw, cx, cy, r, color, ratio=0.23):
    points = []
    for i in range(8):
        angle = -math.pi / 2 + i * math.pi / 4
        radius = r if i % 2 == 0 else r * ratio
        points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    draw.polygon(points, fill=color)


def rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def mark(draw, x, y, size):
    r = size * 0.25
    rounded(draw, (x, y, x + size, y + size), r, LIME)
    cx, cy = x + size * 0.49, y + size * 0.52
    star4(draw, cx, cy, size * 0.30, "#29331A")
    star4(draw, cx, cy, size * 0.23, LIME)
    star4(draw, x + size * 0.75, y + size * 0.26, size * 0.10, "#29331A")
    star4(draw, x + size * 0.26, y + size * 0.76, size * 0.075, "#29331A")


def brand(im, x=62, y=53, scale=1.0, dark=False):
    d = ImageDraw.Draw(im)
    side = round(42 * scale)
    mark(d, x, y, side)
    f = font(round(29 * scale), "bold")
    color = "#F4F5EF" if dark else "#20271D"
    muted = LIME if dark else "#747C6D"
    text(im, x + side + 12 * scale, y + 2 * scale, "study", f, color)
    tx = x + side + 12 * scale + f.getlength("study") - 1 * scale
    text(im, tx, y + 2 * scale, "spark", f, muted)


def make_background():
    img = Image.new("RGBA", (W, H), INK)
    px = img.load()
    for y in range(H):
        yf = y / H
        for x in range(W):
            dx = (x - W * 0.70) / (W * 0.85)
            dy = (y - H * 0.43) / (H * 0.73)
            glow = max(0.0, 1.0 - math.sqrt(dx * dx + dy * dy)) ** 2
            edge = max(abs(x - W / 2) / (W / 2), abs(y - H / 2) / (H / 2))
            shade = int(8 * yf + 7 * max(0, edge - 0.42))
            px[x, y] = (12 + int(12 * glow) - shade // 3,
                        17 + int(22 * glow) - shade // 2,
                        15 + int(8 * glow) - shade // 2, 255)
    aura = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(aura).ellipse((260, 240, 980, 960), fill=(146, 215, 72, 39))
    aura = aura.filter(ImageFilter.GaussianBlur(125))
    img.alpha_composite(aura)
    return img


BG = make_background()


def background_lines(im, t, center=(530, 620), base=320, count=3):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = center
    for i in range(count):
        r = base + i * 30 + 8 * math.sin(t * 1.2 + i)
        d.arc((cx-r, cy-r, cx+r, cy+r), start=(t * 24 + i * 39) % 360, end=(t * 24 + i * 39 + 150) % 360,
              fill=(195, 233, 132, 22 + i * 3), width=2)
    im.alpha_composite(layer)


def scene_hook(p, t):
    im = BG.copy()
    background_lines(im, t, (500, 600), 330, 4)
    d = ImageDraw.Draw(im)
    brand(im, dark=True)
    # A moving clock face lives behind the typography as a visual motif.
    cx, cy, r = 560, 630, 285
    d.ellipse((cx-r, cy-r, cx+r, cy+r), outline="#28352B", width=2)
    d.arc((cx-r, cy-r, cx+r, cy+r), start=-102 + t * 24, end=34 + t * 24, fill="#66853D", width=6)
    for i in range(24):
        a = math.tau * i / 24 - math.pi / 2 + t * .08
        inner, outer = r - 8, r - (28 if i % 3 == 0 else 17)
        d.line((cx + math.cos(a)*inner, cy + math.sin(a)*inner,
                cx + math.cos(a)*outer, cy + math.sin(a)*outer), fill="#4B5C3D", width=2)
    # Headline arrives on three short, deliberate beats.
    slide_text(im, 66, 333, "ХОЧЕШЬ", font(27, "bold"), "#C8D6B1", p, 0.01, .16, 22)
    slide_text(im, 62, 385, "УЧИТЬСЯ", font(82, "heavy"), PAPER, p, .08, .22, 62)
    slide_text(im, 62, 482, "ЭФФЕКТИВНО?", font(68, "heavy"), LIME, p, .23, .22, 56, 610)
    slide_text(im, 65, 573, "И НЕ ВЫГОРАТЬ?", font(50, "bold"), PAPER, p, .38, .22, 52, 610)
    q = ease((p - .55) / .2)
    bar_width = int(570 * q)
    d.rounded_rectangle((66, 704, 66 + bar_width, 712), radius=4, fill=LIME)
    if p > .58:
        text(im, 66, 758, "ПЛАН  ·  ФОКУС  ·  ОТДЫХ", font(22, "bold"), "#C5CEBC", round(255 * q))
    # A quick shimmer crosses the ring as the scene resolves.
    sx = int(-70 + (W + 140) * ((p * 1.15) % 1))
    star4(d, sx, 905 + 8 * math.sin(t * 4), 15, LIME)
    centered(im, 1044, "Верни себе спокойный ритм учёбы.", font(21, "regular"), "#B4BDAE", round(255 * ease((p - .62) / .2)))
    return im


def draw_chip(im, x, y, label, p, index):
    q = 1 - ease((p - .12 - index * .06) / .32)
    if q <= .01:
        return
    x = x + (1 - q) * (42 if index % 2 == 0 else -42)
    alpha = round(235 * q)
    lay = Image.new("RGBA", (220, 54), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    rounded(d, (0, 0, 216, 48), 23, (34, 44, 35, alpha), (116, 144, 82, alpha), 1)
    d.ellipse((16, 18, 27, 29), fill=(215, 242, 117, alpha))
    d.text((39, 11), label, font=font(17, "bold"), fill=(236, 239, 228, alpha))
    im.alpha_composite(lay, (round(x), round(y)))


def scene_focus(p, t):
    im = BG.copy()
    background_lines(im, t, (360, 645), 300, 3)
    d = ImageDraw.Draw(im)
    brand(im, dark=True)
    centered(im, 224, "ОДИН ЦИКЛ ФОКУСА", font(24, "bold"), "#BDD0A6", round(255 * ease(p / .12)))
    cx, cy, r = 360, 642, 257
    d.ellipse((cx-r, cy-r, cx+r, cy+r), outline="#303C30", width=16)
    # Minute markers and one energized sweep animate around the dial.
    for i in range(60):
        a = i * math.tau / 60 - math.pi / 2
        tick = 17 if i % 5 == 0 else 8
        r1, r2 = r + 19 - tick, r + 19
        color = "#798C5A" if i % 5 == 0 else "#465441"
        d.line((cx + math.cos(a)*r1, cy + math.sin(a)*r1,
                cx + math.cos(a)*r2, cy + math.sin(a)*r2), fill=color, width=2)
    sweep = 95 + 215 * ease(p)
    box = (cx-r, cy-r, cx+r, cy+r)
    d.arc(box, start=-90, end=-90+sweep, fill="#A6D654", width=16)
    angle = math.radians(-90 + sweep)
    dot_x, dot_y = cx + r*math.cos(angle), cy + r*math.sin(angle)
    d.ellipse((dot_x-12, dot_y-12, dot_x+12, dot_y+12), fill=PAPER)
    d.ellipse((dot_x-6, dot_y-6, dot_x+6, dot_y+6), fill=LIME)
    # The timer is a brand moment, not a mock app screen.
    f = font(108, "heavy")
    centered(im, 529, "25:00", f, PAPER)
    centered(im, 656, "МИНУТ ФОКУСА", font(21, "bold"), LIME)
    draw_chip(im, -8, 463, "уведомления", p, 0)
    draw_chip(im, 500, 770, "лишний шум", p, 1)
    draw_chip(im, 489, 419, "сообщения", p, 2)
    # Subtle pulse at the base emphasizes the single-task rhythm.
    q = .5 + .5 * math.sin(t * math.tau * 1.35)
    d.rounded_rectangle((200, 994, 520, 1000), radius=3, fill="#33402F")
    d.rounded_rectangle((200, 994, 200 + int(320 * (.35 + .65*q)), 1000), radius=3, fill="#9FCB58")
    centered(im, 1047, "Одна задача. Только ты.", font(24, "bold"), PAPER)
    centered(im, 1090, "Начни с 25 минут — этого достаточно.", font(17, "regular"), "#AEB8A4")
    return im


def scene_break(p, t):
    im = BG.copy()
    d = ImageDraw.Draw(im)
    brand(im, dark=True)
    # Breathing halo expands and contracts behind the short break timer.
    pulse = .5 + .5 * math.sin(t * math.tau * .8)
    cx, cy = 360, 641
    for i in range(5):
        radius = 170 + i*33 + 12*pulse
        color = (110, 147, 68, 47 - i*6)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse((cx-radius, cy-radius, cx+radius, cy+radius), outline=color, width=2)
        im.alpha_composite(layer)
    d = ImageDraw.Draw(im)
    centered(im, 238, "ФОКУС ЗАВЕРШЁН", font(23, "bold"), "#C2CDB4", round(255 * ease(p / .12)))
    f = font(138, "heavy")
    y = 378 + int((1 - out_cubic(p/.22))*30)
    centered(im, y, "ПАУЗА", f, LIME, round(255 * ease(p/.16)))
    centered(im, 539, "5 МИНУТ", font(36, "bold"), PAPER, round(255 * ease((p-.08)/.17)))
    centered(im, 593, "ПЕРЕЗАГРУЗКИ", font(22, "bold"), "#AAB89A", round(255 * ease((p-.14)/.17)))
    # Stars spiral out of the halo, then gather beside the reward text.
    for i in range(14):
        q = (p * .62 + i / 14) % 1
        radius = 115 + q * 190
        a = i * 2.399 + t * .95
        x = cx + math.cos(a) * radius
        yy = cy + math.sin(a) * radius
        size = 5 + 6 * (1-q)
        star4(d, x, yy, size, LIME if i % 3 else PAPER)
    q = ease((p - .40) / .24)
    rounded(d, (179, 788, 541, 856), 34, "#243020", outline="#5A7139", width=2)
    star4(d, 226, 822, 19, LIME)
    text(im, 255, 805, "ЗВЁЗДЫ ЗА ФОКУС", font(18, "bold"), PAPER, round(255*q))
    centered(im, 1016, "Отдых — часть прогресса.", font(26, "bold"), PAPER, round(255 * ease((p-.5)/.2)))
    centered(im, 1064, "Перезагрузись и возвращайся к цели.", font(18, "regular"), "#AEB8A4", round(255 * ease((p-.58)/.2)))
    return im


def end_background():
    im = Image.new("RGBA", (W, H), "#F4F6ED")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(8):
        r = 190 + i*72
        d.arc((360-r, 625-r, 360+r, 625+r), start=195, end=340,
              fill=(91, 122, 48, 15 + i*2), width=2)
    im.alpha_composite(layer)
    return im


END_BG = end_background()


def scene_end(p, t):
    im = END_BG.copy()
    d = ImageDraw.Draw(im)
    # Lively but spacious finish: the orbit settles and leaves room for the CTA.
    cx, cy = 360, 208
    for i in range(12):
        a = t * .42 + i * math.tau / 12
        r = 240 + 15 * math.sin(t*1.2 + i)
        x, y = cx + math.cos(a)*r, cy + math.sin(a)*r
        if y < 275 or x < 72 or x > 648:
            star4(d, x, y, 5 + (i % 3)*2, "#829D3B")
    # Large brand lockup.
    f1, f2 = font(64, "heavy"), font(64, "regular")
    word_w = f1.getlength("study") + f2.getlength("spark") - 4
    x = (W - (74 + 22 + word_w)) / 2
    # Recompute centered lockup after icon width.
    x = (W - (74 + 20 + word_w)) / 2
    mark(d, round(x), 364, 74)
    tx = x + 92
    text(im, tx, 366, "study", f1, "#20271D", round(255*ease(p/.16)))
    text(im, tx + f1.getlength("study") - 3, 366, "spark", f2, "#596348", round(255*ease(p/.16)))
    centered(im, 571, "УЧИСЬ В СВОЁМ", font(31, "bold"), "#475534", round(255*ease((p-.10)/.15)))
    centered(im, 619, "РИТМЕ.", font(77, "heavy"), "#20271D", round(255*ease((p-.18)/.18)))
    centered(im, 726, "Без гонки. С фокусом и отдыхом.", font(22, "regular"), "#455332", round(255*ease((p-.28)/.18)))
    q = ease((p-.28)/.14)
    content_q = ease((p-.45)/.16)
    button_w = int(520*q)
    bx = (W-button_w)//2
    d.rounded_rectangle((bx, 932, bx+button_w, 1018), radius=28, fill="#20271D")
    if content_q > .01:
        # Telegram paper-plane mark as a simple vector glyph.
        px, py = bx + 54, 975
        d.ellipse((px-19, py-19, px+19, py+19), fill=LIME)
        d.polygon([(px-10,py-2),(px+11,py-10),(px+5,py+11),(px,py+3),(px-5,py+5)], fill="#20271D")
        text(im, bx+87, 958, "t.me/StudySparkEdu", font(24, "bold"), PAPER, round(255*content_q))
    centered(im, 1094, "ПЛАНЫ  ·  POMODORO  ·  НАГРАДЫ", font(16, "bold"), "#475534", round(255*ease((p-.52)/.2)))
    # Soft final pulse on the CTA; no extra panel or app screenshot.
    pulse = max(0, math.sin(t*math.tau*1.1)) * 18
    d.rounded_rectangle((bx-2-pulse/8, 930-pulse/8, bx+button_w+2+pulse/8, 1020+pulse/8), radius=31,
                        outline="#829D3B", width=2)
    return im


SCENES = [scene_hook, scene_focus, scene_break, scene_end]
STARTS = [0]
for duration in SEGMENTS[:-1]:
    STARTS.append(STARTS[-1] + duration)


def render_at(t):
    idx = min(len(SEGMENTS)-1, next((i for i in range(len(STARTS)-1, -1, -1) if t >= STARTS[i]), 0))
    p = clamp((t - STARTS[idx]) / SEGMENTS[idx])
    current = SCENES[idx](p, t - STARTS[idx])
    if idx < len(SCENES)-1 and t >= STARTS[idx+1] - TRANSITION:
        next_p = clamp((t - STARTS[idx+1]) / SEGMENTS[idx+1])
        nxt = SCENES[idx+1](next_p, t - STARTS[idx+1])
        q = ease((t - (STARTS[idx+1] - TRANSITION)) / TRANSITION)
        current = Image.blend(current, nxt, q)
    return current.convert("RGB")


def make_music(path):
    sr = 44100
    total = int(sr * TOTAL)
    buf = array("h", [0]) * total
    rng = random.Random(2026)
    beat = 60 / 124
    beats = int(TOTAL / beat) + 1
    # Tight, bright electronic bed: soft kick, clap, hats, warm bass and a four-note pluck.
    melody = [523.25, 659.25, 783.99, 659.25, 587.33, 698.46, 880.00, 698.46]
    chord = [261.63, 329.63, 392.00, 329.63, 293.66, 349.23, 440.00, 349.23]
    for n in range(beats):
        start = int(n * beat * sr)
        # Kick with a short downward pitch sweep and a little body.
        for j in range(int(.24*sr)):
            i = start + j
            if i >= total: break
            tt = j / sr
            freq = 48 + 112 * math.exp(-tt*26)
            val = (math.sin(2*math.pi*freq*tt) + .15*math.sin(2*math.pi*freq*2*tt)) * math.exp(-tt*17) * 8400
            buf[i] = max(-32768, min(32767, buf[i] + int(val)))
        # Clap on beats two and four.
        if n % 4 in (1, 3):
            for j in range(int(.14*sr)):
                i = start+j
                if i >= total: break
                tt = j/sr
                noise = (rng.random()*2-1) * math.exp(-tt*30)
                tone = math.sin(2*math.pi*185*tt) * math.exp(-tt*20)
                buf[i] = max(-32768, min(32767, buf[i] + int((noise*.55+tone*.35)*4100)))
        # Bass pulse and bright chord pluck.
        note = chord[n % len(chord)] / 2
        for j in range(int(.43*sr)):
            i = start+j
            if i >= total: break
            tt = j/sr
            env = math.exp(-tt*5.5)
            bass = math.sin(2*math.pi*note*tt) * math.exp(-tt*2.7) * 1450
            pluck = (math.sin(2*math.pi*melody[n % len(melody)]*tt) + .26*math.sin(2*math.pi*melody[n % len(melody)]*2*tt)) * env * 1250
            buf[i] = max(-32768, min(32767, buf[i] + int(bass + pluck)))
        # Eighth-note hats.
        hat_start = start + int(beat * sr / 2)
        for j in range(int(.045*sr)):
            i = hat_start+j
            if i >= total: break
            val = (rng.random()*2-1) * math.exp(-j/sr*88) * 950
            buf[i] = max(-32768, min(32767, buf[i] + int(val)))
    # Short whoosh accents mark the scene changes.
    for boundary in STARTS[1:]:
        start = int(boundary*sr)
        length = int(.24*sr)
        for j in range(length):
            i = start+j
            if i >= total: break
            q = j/length
            envelope = math.sin(math.pi*q) ** 2
            val = (rng.random()*2-1) * envelope * 1350
            buf[i] = max(-32768, min(32767, buf[i] + int(val)))
    fade = int(.28*sr)
    for i in range(fade):
        buf[i] = int(buf[i] * i / fade)
        buf[-1-i] = int(buf[-1-i] * i / fade)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        wav.writeframes(buf.tobytes())


def encode():
    frames = round(TOTAL * FPS)
    temp_video = Path(tempfile.gettempdir()) / "study-spark-motion-silent.mp4"
    temp_audio = Path(tempfile.gettempdir()) / "study-spark-motion-music.wav"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-frames:v", str(frames), "-an", "-c:v", "libx264",
           "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", str(temp_video)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for frame in range(frames):
            t = frame / FPS
            proc.stdin.write(render_at(t).tobytes())
    finally:
        proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("Video encoding failed")
    make_music(temp_audio)
    mux = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(temp_video), "-i", str(temp_audio),
           "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(OUT)]
    subprocess.run(mux, check=True)
    temp_video.unlink(missing_ok=True)
    temp_audio.unlink(missing_ok=True)
    print(OUT)


if __name__ == "__main__":
    encode()
