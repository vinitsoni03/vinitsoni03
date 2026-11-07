"""Build the profile README's SVG panels in the portfolio's visual language.

Matches vinit-soni.121labs.in: pure black, off-white ink (#f2f2ef), dimmed
labels, warm amber light, an ASCII-rendered portrait, glass pills, a
three-column grid with numbered lists and a status bar.

Everything personal lives in the DATA section below. Edit it, then run:

    python scripts/build_assets.py

Needs Pillow and fontTools (+ brotli for woff2). Writes into assets/.
The stats cards are built separately, daily, by scripts/stats_cards.py.
"""

import base64
import io
import math
import os
import random
from html import escape

from fontTools import subset
from fontTools.ttLib import TTFont
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

# =========================================================================
# DATA (mirrors portfolio src/data/profile.ts)
# =========================================================================

NAME = "Vinit Soni"
IDENTITY = ["Cloud & DevOps Engineer", "AWS Certified"]
CITY = "Noida, IN"
REGION = "ap-south-1"
TZ = "UTC+05:30"
SITE = "vinit-soni.121labs.in"
EMAIL = "sonivinit54@gmail.com"
LINKEDIN = "linkedin.com/in/vinit-soni-3410a2281"

HERO_LISTS = [
    ("Cloud", ["AWS", "Azure", "Serverless", "Event-Driven", "IAM"]),
    ("DevOps", ["Terraform", "Docker", "GitHub Actions", "CI/CD", "Linux"]),
]
FEATURED = [
    "Serverless File Storage", "Real-Time Streaming", "Image Recognition",
    "Digital HypeX", "UniqInn", "121Labs", "G-Rise Property Services",
    "Kingra Roofing", "Kingdom of Holidays", "KAKTS",
    "AWS Cloud Practitioner", "OCI Architect Associate",
]
TAGLINES = [
    "Building scalable, smart systems on the cloud",
    "Serverless. Event-driven. Least privilege.",
    "Infrastructure as code, shipped on every push.",
    "Observability first.",
]

BIO = [
    "I'm a Cloud & DevOps engineer who builds serverless and event-driven systems: "
    "a file storage platform on Lambda, API Gateway and S3, a real-time Kinesis "
    "streaming pipeline, and an image recognition pipeline on Azure Computer Vision.",
    "AWS Certified Cloud Practitioner and OCI Architect Associate. I build and manage "
    "websites for businesses in India and Canada, and interned as a Software Development "
    "Engineer at Bluestock Fintech. I care about least-privilege security, observability "
    "and CI/CD that ships on every push.",
]
EXPERIENCE = [
    ("Web Developer", "UniqInn", "Oct 2026 – Present"),
    ("Web Developer", "Digital HypeX", "Nov 2025 – Present"),
    ("SDE Intern", "Bluestock Fintech", "Jun 2024"),
]
CERTS = [
    ("AWS Certified Cloud Practitioner", "Amazon Web Services · 2026"),
    ("OCI Architect Associate", "Oracle · 2025"),
    ("Cloud Security Foundations", "AWS Academy"),
]
FOCUS = ["Serverless & event-driven", "Least-privilege IAM", "Infrastructure as code",
         "CI/CD on every push", "Observability"]

# (file, number, title, category, detail, link label, url)
WORK = [
    ("cloud", "Serverless File Storage", "AWS · Serverless",
     "1,000+ daily requests · 40% faster API", "Repo", "https://github.com/vinitsoni03/Cloud-file-storage"),
    ("cloud", "Real-Time Streaming Pipeline", "AWS · Event-driven",
     "<1s p95 latency · DLQ + retries", "Repo", "https://github.com/vinitsoni03/realtime-streaming-pipeline"),
    ("cloud", "Image Recognition Pipeline", "Azure · AI",
     "500+ images · 60% faster retrieval", "Repo", "https://github.com/vinitsoni03/AI-image-recognition"),
    ("client", "Digital HypeX", "Digital marketing agency", "React · Vite", "Live", "https://digitalhypex.com"),
    ("client", "UniqInn", "Marketing & events studio", "Next.js · Lenis", "Live", "https://uniqinn.com"),
    ("client", "121Labs", "AI operations studio", "Next.js · Vercel", "Live", "https://121labs.in"),
    ("client", "G-Rise Property Services", "Exterior cleaning, Surrey BC", "React · Vite", "Live", "https://grisepropertyservice.com"),
    ("client", "Kingra Roofing", "Roofing & exterior cleaning, BC", "React · Vite", "Live", "https://kingraroofing.com"),
    ("client", "Kingdom of Holidays", "Travel agency", "PHP · Bootstrap", "Live", "https://www.kingdomofholidays.com"),
    ("client", "KAKTS", "Cactus leather bags, e-commerce", "WordPress · Cloudflare", "Live", "https://kakts.com"),
]

STACK = [
    ("AWS", ["S3", "Lambda", "API Gateway", "IAM", "Kinesis", "EC2", "CloudWatch"]),
    ("Azure", ["Blob Storage", "Functions", "Computer Vision"]),
    ("DevOps", ["Terraform", "Docker", "GitHub Actions", "Jenkins", "Ansible", "CI/CD"]),
    ("Architecture", ["System Design", "Microservices", "Event-Driven", "Serverless", "Fault Tolerance"]),
    ("Security", ["IAM Policies", "Least Privilege", "Pre-Signed URLs", "SAS Tokens"]),
    ("Code & Tools", ["Python", "C++", "SQL", "Bash", "Linux", "Git"]),
]

# =========================================================================
# Theme (portfolio src/styles/tokens.css)
# =========================================================================

INK = "#f2f2ef"
DIM = "#91918f"     # INK at 0.6 on black
FAINT = "#4a4a48"
AMBER = "#e8a33d"
W = 1000
SANS = "G, Geist, Inter, 'Segoe UI', system-ui, -apple-system, sans-serif"
MONO = "ui-monospace, 'SF Mono', Menlo, Consolas, 'Courier New', monospace"
RAMP = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "[::-1]

# =========================================================================
# Font: Geist subset, embedded so the SVGs look the same everywhere
# =========================================================================

FONT_SRC = os.path.join(ASSETS, "fonts", "geist-latin-wght-normal.woff2")
FONT_OUT = os.path.join(ASSETS, "fonts", "geist-subset.woff2")
CHARS = "".join(chr(c) for c in range(32, 127)) + "·–—“”’×•"


def build_font():
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga"]
    font = TTFont(FONT_SRC)
    sub = subset.Subsetter(opts)
    sub.populate(text=CHARS)
    sub.subset(font)
    font.flavor = "woff2"
    font.save(FONT_OUT)
    return base64.b64encode(open(FONT_OUT, "rb").read()).decode()


_metrics = TTFont(FONT_SRC)
_cmap, _hmtx = _metrics.getBestCmap(), _metrics["hmtx"].metrics


def tw(text, size, weight=400):
    """Text width in px for Geist at `size` (default instance, nudged for weight)."""
    units = sum(_hmtx[_cmap[ord(c)]][0] if ord(c) in _cmap else 600 for c in text)
    return units / 1000 * size * (1 + (weight - 400) / 400 * 0.05)


def wrap(text, size, width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if tw(trial, size) > width and line:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line]


# =========================================================================
# SVG helpers
# =========================================================================

FONT_B64 = None


def svg(width, height, body, label, css=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">
<style>
@font-face {{ font-family: G; font-weight: 100 900; src: url(data:font/woff2;base64,{FONT_B64}) format("woff2"); }}
text {{ font-family: {SANS}; fill: {INK}; }}
.m {{ font-family: {MONO}; white-space: pre; }}
.d {{ fill: {DIM}; }}
.f {{ fill: {FAINT}; }}
.a {{ fill: {AMBER}; }}
.halo {{ stroke: #000; stroke-width: 3px; stroke-linejoin: round; paint-order: stroke; }}
@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
{css}
</style>
{body}
</svg>
"""


def t(x, y, s, size=13, cls="", weight=400, anchor=None, extra=""):
    a = f' text-anchor="{anchor}"' if anchor else ""
    c = f' class="{cls}"' if cls else ""
    w = f' font-weight="{weight}"' if weight != 400 else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}"{w}{c}{a}{extra}>{escape(s)}</text>'


def window(width, height, inner=""):
    """The portfolio's glass window: near-black panel, hairline border, top sheen."""
    return (f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" fill="#070707" '
            f'stroke="#fff" stroke-opacity=".13"/>'
            f'<line x1="10" y1="1.5" x2="{width - 10}" y2="1.5" stroke="#fff" stroke-opacity=".08"/>{inner}')


def pill(x, y, w, h, label, size=12.5, arrow=False):
    out = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#fff" fill-opacity=".14" '
           f'stroke="#fff" stroke-opacity=".16"/>'
           f'<line x1="{x + 5}" y1="{y + 1}" x2="{x + w - 5}" y2="{y + 1}" stroke="#fff" stroke-opacity=".22"/>'
           + t(x + 8, y + h / 2 + size * 0.36, label, size))
    if arrow:
        out += arrow_icon(x + w - 16, y + h / 2 - 4)
    return out


def arrow_icon(x, y, size=8, color=INK):
    """↗ drawn as a path (Geist has no arrow glyphs)."""
    return (f'<path d="M{x:.1f} {y + size:.1f} L{x + size:.1f} {y:.1f} M{x + 2.5:.1f} {y:.1f} H{x + size:.1f} V{y + size - 2.5:.1f}" '
            f'fill="none" stroke="{color}" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>')


def save(name, content):
    path = os.path.join(ASSETS, name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"wrote assets/{name}  {len(content.encode()) // 1024} KB")


# =========================================================================
# Hero: ASCII portrait over amber smoke, grid columns, drum list, status bar
# =========================================================================

def ascii_field(x0, y0, fw, fh, size=5.6, seed=7):
    """Render the cut-out photo over procedural smoke as coloured ASCII rows."""
    cw, lh = size * 0.6, size
    cols, rows = int(fw / cw), int(fh / lh)
    S = 3  # supersample
    cw_px, ch_px = int(fw * S), int(fh * S)

    # 1. smoke: blurred noise, warm, falling off to black at the edges
    rnd = random.Random(seed)
    noise = Image.new("L", (60, 60))
    noise.putdata([rnd.randint(0, 255) for _ in range(3600)])
    noise = noise.resize((cw_px, ch_px), Image.BICUBIC).filter(ImageFilter.GaussianBlur(28 * S))
    smoke = Image.new("RGB", (cw_px, ch_px))
    px_n, px_s = noise.load(), smoke.load()
    cx, cy = cw_px * 0.5, ch_px * 0.32
    for yy in range(0, ch_px):
        for xx in range(0, cw_px):
            d = math.hypot((xx - cx) / (cw_px * 0.55), (yy - cy) / (ch_px * 0.75))
            fall = max(0.0, 1 - d) ** 1.6
            n = px_n[xx, yy] / 255
            v = (0.25 + 0.75 * n) * fall * 0.55  # kept low so the figure carries the frame
            px_s[xx, yy] = (int(150 * v), int(78 * v), int(28 * v))

    # 2. the cut-out, placed like the portfolio hero (crown→waist, centred)
    cut = Image.open(os.path.join(ASSETS, "src", "hero-cutout.webp")).convert("RGBA")
    top, bottom, cxr = 0.032, 0.645, 0.501
    crown, waist = 0.09, 0.98
    scale = (waist - crown) * ch_px / ((bottom - top) * cut.height)
    cut = cut.resize((int(cut.width * scale), int(cut.height * scale)), Image.LANCZOS)
    # The face is much darker than the white shirt, so one tone curve can't serve both:
    # equalise luminance inside the figure (spreads face, beard, hair, shirt across the
    # glyph ramp), keep the photo's own colour, then sharpen for crisper features.
    alpha = cut.getchannel("A")
    rgb = cut.convert("RGB")
    lum = rgb.convert("L")
    eq = ImageOps.equalize(lum, mask=alpha.point(lambda a: 255 if a > 128 else 0))
    eq = eq.point(lambda v: int(255 * (0.12 + 0.82 * (v / 255) ** 1.15)))
    lum_px, eq_px, rgb_px = lum.load(), eq.load(), rgb.load()
    for yy in range(rgb.height):
        for xx in range(rgb.width):
            l, e = lum_px[xx, yy], eq_px[xx, yy]
            r, g, b = rgb_px[xx, yy]
            k = e / max(l, 8)
            rgb_px[xx, yy] = (min(255, int(r * k)), min(255, int(g * k)), min(255, int(b * k)))
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=2 * S, percent=160, threshold=2))
    cut = Image.merge("RGBA", (*rgb.split(), alpha))
    ox = int(cw_px / 2 - cxr * cut.width)
    oy = int(crown * ch_px - top * cut.height)
    # warm rim light, like the lit photo
    glow = Image.new("RGBA", cut.size, (232, 140, 60, 0))
    glow.putalpha(cut.getchannel("A").filter(ImageFilter.GaussianBlur(10 * S)).point(lambda a: int(a * 0.5)))
    smoke.paste(glow, (ox, oy), glow)
    smoke.paste(cut, (ox, oy), cut)

    if os.environ.get("ASCII_DEBUG"):
        smoke.save(os.environ["ASCII_DEBUG"])
    # 3. one sample per cell, glyph from luminance, colour lifted 1.5x
    small = smoke.resize((cols, rows), Image.BOX)
    BLACK, WHITE, GAMMA, LIFT = 0.08, 0.92, 1.25, 1.5
    cells = []
    for r in range(rows):
        row = []
        for c in range(cols):
            R, G, B = small.getpixel((c, r))
            lum = (0.2126 * R + 0.7152 * G + 0.0722 * B) / 255
            yv = min(max((lum - BLACK) / (WHITE - BLACK), 0), 1)
            g = RAMP[round(yv ** GAMMA * (len(RAMP) - 1))] if yv > 0 else " "
            row.append((g, tuple(min(255, int(v * LIFT)) for v in (R, G, B))))
        cells.append(row)

    # 4. quantise colours to a small palette -> one CSS class each
    inked = [col for row in cells for g, col in row if g != " "]
    pal_img = Image.new("RGB", (len(inked), 1))
    pal_img.putdata(inked)
    q = pal_img.quantize(colors=10, method=Image.MEDIANCUT)
    palette = q.getpalette()[:30]
    idx = iter(getattr(q, "get_flattened_data", q.getdata)())
    classes = [f"#{palette[i * 3]:02x}{palette[i * 3 + 1]:02x}{palette[i * 3 + 2]:02x}" for i in range(10)]

    css = "".join(f".c{i}{{fill:{c}}}" for i, c in enumerate(classes))
    out = []
    flicker = set(rnd.sample(range(rows), 9))
    for r, row in enumerate(cells):
        # runs of one colour class; spaces join whichever run they sit in
        spans, cur, buf = [], None, ""
        for g, _ in row:
            if g == " ":
                buf += " "
                continue
            k = next(idx)
            if cur is not None and k != cur:
                spans.append((cur, buf))
                buf = ""
            cur = k
            buf += g
        if cur is None:
            continue  # blank row
        spans.append((cur, buf))
        inner = "".join(f'<tspan class="c{k}">{escape(s)}</tspan>' for k, s in spans)
        anim = f"animation-delay:{r * 11}ms" + (f",{1200 + rnd.randint(0, 6000)}ms" if r in flicker else "")
        cls = "r fl" if r in flicker else "r"
        out.append(f'<text x="{x0}" y="{y0 + (r + 1) * lh:.1f}" textLength="{cols * cw:.1f}" lengthAdjust="spacing" '
                   f'class="m {cls}" style="{anim}" xml:space="preserve">{inner}</text>')
    return css, f'<g font-size="{size}">{"".join(out)}</g>'


def drum(x, y, items, lh=21, visible=7, hold=2.0, move=0.45):
    """The portfolio's ticking 'Featured' list: endless scroll, centre row bright."""
    n = len(items)
    cycle = n * (hold + move)
    frames = []
    for i in range(n + 1):
        t0 = i * (hold + move) / cycle * 100
        frames.append(f"{t0:.3f}%{{transform:translateY({-i * lh}px)}}")
        if i < n:
            frames.append(f"{t0 + hold / cycle * 100:.3f}%{{transform:translateY({-i * lh}px)}}")
    css = (f"@keyframes drum{{{''.join(frames)}}}"
           f".drum{{animation:drum {cycle:.2f}s cubic-bezier(.215,.61,.355,1) infinite}}")
    h = visible * lh
    rows = "".join(t(x, y + (i + 1) * lh - 6, s, 12.5, "halo") for i, s in enumerate(items + items[:visible]))
    defs = (f'<linearGradient id="dg" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
            f'<stop offset=".28" stop-color="#fff" stop-opacity=".45"/>'
            f'<stop offset=".43" stop-color="#fff" stop-opacity="1"/>'
            f'<stop offset=".57" stop-color="#fff" stop-opacity="1"/>'
            f'<stop offset=".72" stop-color="#fff" stop-opacity=".45"/>'
            f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<mask id="dm"><rect x="{x - 10}" y="{y}" width="{W - x + 10}" height="{h}" fill="url(#dg)"/></mask>')
    return css, defs, f'<g mask="url(#dm)"><g class="drum">{rows}</g></g>'


def typing(cx, y, lines, size=12.5, slot=5.0, type_s=1.6):
    """Bottom-bar taglines, centred on cx, retyped one after another (SMIL, so it runs inside <img>)."""
    total = slot * len(lines)
    defs, body, cur_x, cur_t = [], [], [], []
    for k, s in enumerate(lines):
        start = k * slot
        x = cx - tw(s, size) / 2
        times, widths = [0.0], [0.0]
        for j in range(1, len(s) + 1):
            tt = start + type_s * j / len(s)
            times.append(tt / total)
            widths.append(tw(s[:j], size))
            cur_t.append(tt / total)
            cur_x.append(x + tw(s[:j], size) + 3)
        times.append((start + slot - 0.4) / total)
        widths.append(0.0)
        if times[1] == 0:
            times[1] = 0.0001
        kt = ";".join(f"{v:.4f}" for v in times)
        vals = ";".join(f"{v:.1f}" for v in widths)
        defs.append(f'<clipPath id="tl{k}"><rect x="{x}" y="{y - size}" height="{size * 1.6}" width="0">'
                    f'<animate attributeName="width" dur="{total}s" repeatCount="indefinite" calcMode="discrete" '
                    f'keyTimes="{kt}" values="{vals}"/></rect></clipPath>')
        body.append(f'<g clip-path="url(#tl{k})">{t(x, y, s, size, "halo")}</g>')
    kt = ";".join(f"{v:.4f}" for v in [0.0] + cur_t)
    vals = ";".join(f"{v:.1f}" for v in [cx - tw(lines[0], size) / 2] + cur_x)
    body.append(f'<rect class="blink" y="{y - size * 0.82:.1f}" width="6" height="{size * 0.95:.1f}" fill="{AMBER}">'
                f'<animate attributeName="x" dur="{total}s" repeatCount="indefinite" calcMode="discrete" '
                f'keyTimes="{kt}" values="{vals}"/></rect>')
    return "".join(defs), "".join(body)


def hero():
    H = 560
    col = [14, 130, 790]   # left zone: identity + two lists; right zone: Featured; portrait between
    ascii_css, field = ascii_field(255, 40, 490, 520)
    drum_css, drum_defs, drum_g = drum(col[2] + 10, 312, FEATURED)
    type_defs, type_g = typing(W / 2, H - 14, TAGLINES)

    css = ascii_css + drum_css + """
.r { opacity: 0; animation: rv .7s ease-out forwards; }
.r.fl { animation: rv .7s ease-out forwards, fl 9s steps(1) infinite; }
@keyframes rv { from { opacity: 0; } to { opacity: 1; } }
@keyframes fl { 0%,96%,100% { opacity: 1; } 97% { opacity: .25; } 98% { opacity: .8; } 99% { opacity: .4; } }
.smoke { animation: drift 16s ease-in-out infinite alternate; }
@keyframes drift { from { transform: translate(-14px, 6px) scale(1); } to { transform: translate(16px, -8px) scale(1.06); } }
.scan { animation: scan 7s linear infinite; }
@keyframes scan { from { transform: translateY(-60px); } to { transform: translateY(600px); } }
.blink { animation: blink 1s steps(1) infinite; }
@keyframes blink { 50% { opacity: 0; } }
.in { opacity: 0; animation: rv .6s ease-out forwards; }
"""
    defs = f"""<defs>
<radialGradient id="glow" cx="0.48" cy="0.36" r="0.5"><stop offset="0" stop-color="#9a4d14" stop-opacity=".55"/><stop offset=".55" stop-color="#3a1a06" stop-opacity=".35"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>
<radialGradient id="cool" cx="0.62" cy="0.75" r="0.45"><stop offset="0" stop-color="#2b2b30" stop-opacity=".5"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>
<linearGradient id="sl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{AMBER}" stop-opacity="0"/><stop offset=".5" stop-color="{AMBER}" stop-opacity=".09"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></linearGradient>
<linearGradient id="fb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".9"/></linearGradient>
<radialGradient id="fe" cx=".5" cy=".42" r=".62"><stop offset=".6" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>
<mask id="fm"><rect x="255" y="40" width="490" height="520" fill="url(#fe)"/></mask>
<clipPath id="frame"><rect width="{W}" height="{H}" rx="10"/></clipPath>
{drum_defs}{type_defs}
</defs>"""
    pw = (W - 20 - 16) / 3
    pills = "".join(pill(10 + i * (pw + 8), 10, pw, 26, s) for i, s in enumerate([NAME, "Portfolio", "Profile"]))
    lists = ""
    for (label, items), x in zip(HERO_LISTS, col[:2]):
        lists += t(x, 372, label, 12.5, "d halo")
        lists += "".join(t(x + 10, 372 + (i + 1) * 21, s, 12.5, "halo") for i, s in enumerate(items))
    body = f"""{defs}
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="#000"/>
<g class="smoke"><rect x="-60" y="-40" width="{W + 120}" height="{H + 80}" fill="url(#glow)"/><rect width="{W}" height="{H}" fill="url(#cool)"/></g>
<g mask="url(#fm)">{field}</g>
<rect class="scan" x="255" y="0" width="490" height="60" fill="url(#sl)"/>
<rect x="0" y="470" width="{W}" height="90" fill="url(#fb)"/>
<g class="in" style="animation-delay:1.1s">
{pills}
{t(col[0], 304, IDENTITY[0], 12.5, "halo")}{t(col[0], 320, IDENTITY[1], 12.5, "halo")}
{lists}
{t(col[2], 304, "Featured", 12.5, "d halo")}
{drum_g}
{t(col[0], H - 14, CITY, 12.5, "halo")}
{type_g}
{t(col[2], H - 14, REGION, 12.5, "halo")}
{t(W - 14, H - 14, TZ, 12.5, "halo", anchor="end")}
</g>
</g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="none" stroke="#fff" stroke-opacity=".12"/>"""
    save("hero.svg", svg(W, H, body, f"{NAME}, {IDENTITY[0]}: ASCII portrait", css))


# =========================================================================
# Panels
# =========================================================================

def header(label, meta, top=22):
    return (t(24, top + 4, label, 13, weight=500) + t(W - 24, top + 4, meta, 12.5, "d", anchor="end")
            + f'<line x1="24" y1="{top + 18}" x2="{W - 24}" y2="{top + 18}" stroke="#fff" stroke-opacity=".12"/>')


def profile():
    col = [24, 340, 673]
    y = 76
    body = header("Profile", f"{CITY.replace(', IN', ', India')} · {REGION}")
    body += t(col[0], y, "About", 12.5, "d")
    for para in BIO:
        for line in wrap(para, 14, W - 24 - col[1]):
            body += t(col[1], y, line, 14)
            y += 21
        y += 12
    y += 6
    body += f'<line x1="24" y1="{y}" x2="{W - 24}" y2="{y}" stroke="#fff" stroke-opacity=".08"/>'
    y += 32
    y0 = y
    body += t(col[0], y, "Experience", 12.5, "d")
    for i, (role, company, period) in enumerate(EXPERIENCE):
        yy = y0 + 26 + i * 46
        body += t(col[0], yy, role, 13.5, weight=500) + t(col[0], yy + 18, f"{company} · {period}", 12.5, "d")
    body += t(col[1], y0, "Certifications", 12.5, "d")
    for i, (name, issuer) in enumerate(CERTS):
        yy = y0 + 26 + i * 46
        body += t(col[1], yy, name, 13.5, weight=500) + t(col[1], yy + 18, issuer, 12.5, "d")
    body += t(col[2], y0, "Focus", 12.5, "d")
    for i, s in enumerate(FOCUS):
        yy = y0 + 26 + i * 25
        body += f'<rect x="{col[2]}" y="{yy - 8}" width="5" height="5" fill="{AMBER}"/>' + t(col[2] + 14, yy, s, 13.5)
    H = int(y0 + 26 + 3 * 46 + 8)
    save("profile.svg", svg(W, H, window(W, H, body), "Profile: about, experience, certifications"))


def stack():
    cw = (W - 48) / len(STACK)
    rows = max(len(items) for _, items in STACK)
    H = 76 + rows * 22 + 18
    body = header("Stack", "what I build with")
    for i, (label, items) in enumerate(STACK):
        x = 24 + i * cw
        body += t(x, 76, label, 12.5, "d")
        body += "".join(t(x + 10, 76 + (j + 1) * 22, s, 13.5) for j, s in enumerate(items))
    save("stack.svg", svg(W, H, window(W, H, body), "Stack: " + ", ".join(l for l, _ in STACK)))


def section(name, label, meta):
    H = 44
    body = t(24, 27, label, 13, weight=500) + t(W - 24, 27, meta, 12.5, "d", anchor="end")
    save(name, svg(W, H, window(W, H, body), label))


def work_rows():
    for n, (kind, title, category, detail, link, _url) in enumerate(WORK, 1):
        H = 52
        lw = tw(link, 12.5) + 34
        body = (t(24, 31, f"{n:02d}", 12.5, "d m")
                + t(64, 31, title, 14, weight=500)
                + t(330, 31, category, 12.5, "d")
                + t(590, 31, detail, 12.5, "a" if kind == "cloud" else "d")
                + pill(W - 24 - lw, 13, lw, 26, link, 12.5, arrow=True))
        save(f"work-{n:02d}.svg", svg(W, H, window(W, H, body), f"{n:02d} {title}: {category}"))


def link_pills():
    for name, label in [("portfolio", "Portfolio"), ("linkedin", "LinkedIn"), ("email", "Email")]:
        w = int(tw(label, 13) + 40)
        body = pill(1, 1, w - 2, 30, label, 13, arrow=True)
        save(f"pill-{name}.svg", svg(w, 32, f'<rect width="{w}" height="32" rx="6" fill="#000"/>{body}', label))


def terminal():
    lines = [
        ("$", "whoami"),
        ("", f"{NAME.lower()} · cloud & devops engineer · {CITY.lower()}"),
        ("$", "cat contact"),
        ("", f"email     {EMAIL}"),
        ("", f"site      {SITE}"),
        ("", f"linkedin  {LINKEDIN}"),
        ("$", ""),
    ]
    size, lh, cwid = 13, 23, 13 * 0.6
    H = 52 + len(lines) * lh + 18
    body = (f'<line x1="0" y1="36" x2="{W}" y2="36" stroke="#fff" stroke-opacity=".1"/>'
            + "".join(f'<circle cx="{22 + i * 16}" cy="18" r="4.5" fill="{c}"/>' for i, c in enumerate([AMBER, "#5a5a58", "#3a3a38"]))
            + t(W / 2, 22, f"vinit@{REGION}: ~", 12, "d m", anchor="middle"))
    defs, start = [], 0.6
    for i, (prompt, text) in enumerate(lines):
        y = 64 + i * lh
        x = 24
        if prompt:
            body += f'<text x="{x}" y="{y}" font-size="{size}" class="m a" style="opacity:0;animation:rv .01s {start:.2f}s forwards">$</text>'
            x += 2 * cwid
        dur = max(0.05, len(text) * (0.045 if prompt else 0.012))
        if text:
            full = len(text) * cwid
            defs.append(f'<clipPath id="ln{i}"><rect x="{x}" y="{y - 14}" height="20" width="0">'
                        f'<animate attributeName="width" begin="{start:.2f}s" dur="{dur:.2f}s" fill="freeze" '
                        f'calcMode="discrete" values="{";".join(f"{k * cwid:.1f}" for k in range(len(text) + 1))}"/></rect></clipPath>')
            body += (f'<text x="{x}" y="{y}" font-size="{size}" textLength="{full:.1f}" lengthAdjust="spacingAndGlyphs" '
                     f'class="m{"" if prompt else " d"}" clip-path="url(#ln{i})" xml:space="preserve">{escape(text)}</text>')
        else:
            body += (f'<rect x="{x}" y="{y - 11}" width="8" height="14" fill="{AMBER}" '
                     f'style="opacity:0;animation:rv .01s {start:.2f}s forwards, blink 1s {start:.2f}s steps(1) infinite"/>')
        start += dur + (0.35 if prompt else 0.08)
    css = """@keyframes rv { to { opacity: 1; } }
@keyframes blink { 0% { opacity: 1; } 50% { opacity: 0; } }"""
    save("terminal.svg", svg(W, H, f"<defs>{''.join(defs)}</defs>" + window(W, H, body), "Terminal: contact details", css))


def main():
    global FONT_B64
    FONT_B64 = build_font()
    hero()
    profile()
    stack()
    section("section-cloud.svg", "Cloud & DevOps", "01 – 03 · repositories")
    section("section-clients.svg", "Client sites", "04 – 10 · built and managed")
    work_rows()
    link_pills()
    terminal()


if __name__ == "__main__":
    main()
