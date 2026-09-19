#!/usr/bin/env python3
"""
Generate YouTube Music Widget SVG — animasi penuh + marquee title.
Butuh: requests, Pillow
"""
import base64, io, re, sys, requests
from PIL import Image

# ─── CONFIG ────────────────────────────────────────────
VIDEO_URL = "https://www.youtube.com/watch?v=5SRMuef8THI"
OUTPUT    = "music-widget.svg"
W, H      = 600, 220

TITLE_X   = 80          # ← geser kanan di sini (default 80)
TITLE_FS  = 15          # font size title
ARTIST_X  = 80          # artist ikut digeser
MARQUEE_SPEED = 45      # px per detik (makin besar = makin cepat)

# ─── 1. Metadata ───────────────────────────────────────
meta   = requests.get(f"https://www.youtube.com/oembed?url={VIDEO_URL}&format=json", timeout=10).json()
title  = meta["title"]
author = meta["author_name"]
print(f"✓ {title} — {author}")

# ─── 2. Thumbnail ──────────────────────────────────────
vid = re.search(r"v=([^&]+)", VIDEO_URL).group(1)
for q in ("maxresdefault", "sddefault", "hqdefault"):
    r = requests.get(f"https://i.ytimg.com/vi/{vid}/{q}.jpg", timeout=15)
    if r.ok and len(r.content) > 5000:
        img_bytes = r.content
        print(f"✓ Thumbnail: {q}")
        break
else:
    sys.exit("✗ Gagal fetch thumbnail")

# ─── 3. Base64 ─────────────────────────────────────────
img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((W, H), Image.LANCZOS)
buf = io.BytesIO()
img.save(buf, "JPEG", quality=72, optimize=True)
b64 = base64.b64encode(buf.getvalue()).decode()
print(f"✓ Base64: {len(b64)//1024} KB")

def esc(s):
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

# ─── 4. Marquee geometry ───────────────────────────────
CLIP_W  = W - TITLE_X - 20                    # area visible title
CHAR_W  = 9                                   # estimasi monospace 15px
text_w  = max(len(title) * CHAR_W, CLIP_W)    # lebar teks aktual
scroll_dist = CLIP_W + text_w                 # total jarak scroll
marquee_dur = max(scroll_dist / MARQUEE_SPEED, 8)
print(f"✓ Marquee: text_w={text_w}px, dur={marquee_dur:.1f}s")

# ─── 5. Equalizer data ─────────────────────────────────
bars_data = [
    (0,  0.90, "16;4;12;6;16",  "4;16;8;14;4"),
    (7,  1.10, "20;6;16;10;20", "0;14;4;10;0"),
    (14, 0.70, "12;20;8;16;12", "8;0;12;4;8"),
    (21, 1.30, "18;8;20;6;18",  "2;12;0;14;2"),
    (28, 1.00, "14;18;6;20;14", "6;2;14;0;6"),
    (35, 0.85, "20;10;18;4;20", "0;10;2;16;0"),
    (42, 1.20, "10;16;20;8;10", "10;4;0;12;10"),
]
bars_svg = "".join(
    f'    <rect x="{x}" width="4" height="20" y="0" rx="1" fill="#FF0033">\n'
    f'      <animate attributeName="height" values="{hs}" dur="{d}s" repeatCount="indefinite"/>\n'
    f'      <animate attributeName="y" values="{ys}" dur="{d}s" repeatCount="indefinite"/>\n'
    f'    </rect>\n'
    for x, d, hs, ys in bars_data
)

# ─── 6. Bangun SVG ─────────────────────────────────────
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#000" stop-opacity="0"/>
      <stop offset="50%"  stop-color="#000" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#000" stop-opacity="0.95"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="#FF0033"/>
      <stop offset="50%"  stop-color="#9945FF"/>
      <stop offset="100%" stop-color="#1f6feb"/>
    </linearGradient>
    <linearGradient id="shimmer" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="#fff" stop-opacity="0"/>
      <stop offset="50%"  stop-color="#fff" stop-opacity="0.85"/>
      <stop offset="100%" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>

    <!-- Clip untuk marquee title -->
    <clipPath id="titleClip">
      <rect x="{TITLE_X}" y="{H - 55}" width="{CLIP_W}" height="24"/>
    </clipPath>

    <clipPath id="frame"><rect width="{W}" height="{H}"/></clipPath>
  </defs>

  <g clip-path="url(#frame)">
    <!-- Thumbnail base64 -->
    <image xlink:href="data:image/jpeg;base64,{b64}"
           x="0" y="0" width="{W}" height="{H}"
           preserveAspectRatio="xMidYMid slice"/>

    <rect width="{W}" height="{H}" fill="url(#fade)"/>

    <!-- ═══ ROTATING VINYL ═══ -->
    <g transform="translate({W - 58}, 58)">
      <circle r="30" fill="#0d1117" opacity="0.85"/>
      <g>
        <animateTransform attributeName="transform" type="rotate"
                          from="0" to="360" dur="6s" repeatCount="indefinite"/>
        <circle r="26" fill="none" stroke="#1f6feb" stroke-width="1"/>
        <circle r="22" fill="none" stroke="#30363d" stroke-width="0.6"/>
        <circle r="18" fill="none" stroke="#30363d" stroke-width="0.6"/>
        <circle r="14" fill="none" stroke="#30363d" stroke-width="0.6"/>
        <circle r="10" fill="none" stroke="#30363d" stroke-width="0.6"/>
        <circle r="6"  fill="none" stroke="#30363d" stroke-width="0.6"/>
        <circle r="3"  fill="#58A6FF"/>
      </g>
      <line x1="22" y1="-26" x2="6" y2="-8" stroke="#9945FF"
            stroke-width="1.6" stroke-linecap="round"/>
    </g>

    <!-- ═══ EQUALIZER ═══ -->
    <g transform="translate(24, {H - 62})">
{bars_svg}    </g>

    <!-- ═══ FLOATING NOTES ═══ -->
    <g font-family="'Segoe UI Symbol','Apple Color Emoji',sans-serif" fill="#58A6FF">
      <text x="{W - 90}" y="{H - 80}" font-size="18" opacity="0">
        ♪
        <animate attributeName="y" values="{H - 80};{H - 210}" dur="3s" begin="0s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="0;1;1;0" dur="3s" begin="0s" repeatCount="indefinite"/>
      </text>
      <text x="{W - 68}" y="{H - 80}" font-size="14" opacity="0">
        ♫
        <animate attributeName="y" values="{H - 80};{H - 210}" dur="3.5s" begin="1s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="0;1;1;0" dur="3.5s" begin="1s" repeatCount="indefinite"/>
      </text>
      <text x="{W - 112}" y="{H - 80}" font-size="16" opacity="0">
        ♩
        <animate attributeName="y" values="{H - 80};{H - 210}" dur="4s" begin="2s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="0;1;1;0" dur="4s" begin="2s" repeatCount="indefinite"/>
      </text>
    </g>

    <!-- ═══ MARQUEE TITLE ═══ -->
    <g clip-path="url(#titleClip)">
      <g>
        <text x="0" y="{H - 38}"
              font-family="'JetBrains Mono',Consolas,monospace"
              font-size="{TITLE_FS}" font-weight="700" fill="#ffffff">
          {esc(title)}
        </text>
        <animateTransform attributeName="transform" type="translate"
          values="{CLIP_W},0; -{text_w},0; -{text_w},0"
          keyTimes="0; 0.9; 1"
          dur="{marquee_dur:.1f}s"
          repeatCount="indefinite"/>
      </g>
    </g>

    <!-- ═══ ARTIST (statis) ═══ -->
    <g clip-path="url(#titleClip)">
      <text x="{ARTIST_X}" y="{H - 20}"
            font-family="'JetBrains Mono',Consolas,monospace"
            font-size="11" fill="#c9d1d9" opacity="0.85">
        ♪ {esc(author[:50])}
      </text>
    </g>

    <!-- ═══ NOW PLAYING BADGE ═══ -->
    <g transform="translate(20, 16)">
      <rect width="124" height="24" rx="12" fill="#000" opacity="0.6"/>
      <circle cx="14" cy="12" r="3" fill="none" stroke="#FF0033" stroke-width="1">
        <animate attributeName="r" values="3;9;3" dur="1.6s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="0.9;0;0.9" dur="1.6s" repeatCount="indefinite"/>
      </circle>
      <circle cx="14" cy="12" r="3" fill="#FF0033">
        <animate attributeName="r" values="3;3.6;3" dur="1s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="1;0.6;1" dur="1s" repeatCount="indefinite"/>
      </circle>
      <text x="26" y="16" font-family="'JetBrains Mono',monospace"
            font-size="9" fill="#fff" letter-spacing="1.5">NOW PLAYING</text>
    </g>

    <!-- ═══ PROGRESS + SHIMMER ═══ -->
    <g transform="translate(0, {H - 12})">
      <rect x="0" y="0" width="{W}" height="3" fill="#1f6feb" opacity="0.35"/>
      <rect x="0" y="0" width="0" height="3" fill="url(#accent)">
        <animate attributeName="width" values="0;{W}" dur="30s" repeatCount="indefinite"/>
      </rect>
      <rect x="-150" y="-3" width="150" height="9" fill="url(#shimmer)">
        <animate attributeName="x" values="-150;{W + 50}" dur="2.8s" repeatCount="indefinite"/>
      </rect>
    </g>

    <rect x="0" y="{H - 4}" width="{W}" height="4" fill="url(#accent)" opacity="0.85"/>
  </g>
</svg>
'''

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"\n✅ Saved: {OUTPUT}  ({len(svg)//1024} KB)")