#!/usr/bin/env python3
"""Generate github-stats.svg dari GitHub GraphQL API."""
import os
import html
from datetime import datetime, timezone
from pathlib import Path

import requests

TOKEN    = os.environ["GH_TOKEN"]
USERNAME = os.environ["GH_USERNAME"]
OUT      = Path("assets/github-stats.svg")
OUT.parent.mkdir(parents=True, exist_ok=True)

QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    login
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      contributionCalendar { totalContributions }
    }
  }
}
"""

r = requests.post(
    "https://api.github.com/graphql",
    json={"query": QUERY, "variables": {"login": USERNAME}},
    headers={"Authorization": f"Bearer {TOKEN}"},
    timeout=30,
)
r.raise_for_status()
data = r.json()
if "errors" in data:
    raise SystemExit(f"GraphQL errors: {data['errors']}")

u = data["data"]["user"]
c = u["contributionsCollection"]
repos = u["repositories"]["nodes"]

stars = sum(r_["stargazerCount"] for r_ in repos)

# Agregasi bahasa
lang_size: dict[str, int] = {}
lang_color: dict[str, str] = {}
for r_ in repos:
    for edge in r_["languages"]["edges"]:
        name = edge["node"]["name"]
        lang_size[name] = lang_size.get(name, 0) + edge["size"]
        lang_color[name] = edge["node"]["color"] or "#888"

top_langs = sorted(lang_size.items(), key=lambda x: -x[1])[:5]
total_size = sum(lang_size.values()) or 1

# ── Statistik ringkas ──
stats = [
    ("Stars",     f"{stars:,}"),
    ("Commits",   f"{c['totalCommitContributions']:,}"),
    ("PRs",       f"{c['totalPullRequestContributions']:,}"),
    ("Issues",    f"{c['totalIssueContributions']:,}"),
    ("Reviews",   f"{c['totalPullRequestReviewContributions']:,}"),
    ("Repos",     f"{u['repositories']['totalCount']:,}"),
    ("Followers", f"{u['followers']['totalCount']:,}"),
]

# ── Layout ──
W, H = 480, 260
PAD = 24
COL_W = (W - PAD * 2) / 3
ROW_H = 42

def esc(s: str) -> str:
    return html.escape(str(s))

svg = []
svg.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
    f'viewBox="0 0 {W} {H}" font-family="Segoe UI,Helvetica,Arial,sans-serif">'
)
svg.append("""
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%"  stop-color="#0d1117"/>
    <stop offset="100%" stop-color="#161b22"/>
  </linearGradient>
</defs>
""")
svg.append(f'<rect width="{W}" height="{H}" rx="14" fill="url(#bg)" stroke="#30363d"/>')

# Header
svg.append(
    f'<text x="{PAD}" y="40" fill="#e6edf3" font-size="16" font-weight="600">'
    f'GitHub Stats · @{esc(u["login"])}</text>'
)
svg.append(
    f'<text x="{W-PAD}" y="40" fill="#7d8590" font-size="11" text-anchor="end">'
    f'{datetime.now(timezone.utc).strftime("%Y-%m-%d")}</text>'
)

# Grid stats (3 kolom x 3 baris)
y0 = 70
for i, (label, value) in enumerate(stats):
    col = i % 3
    row = i // 3
    x = PAD + col * COL_W
    y = y0 + row * ROW_H
    svg.append(f'<text x="{x}" y="{y}" fill="#7d8590" font-size="10" letter-spacing="1">{esc(label.upper())}</text>')
    svg.append(f'<text x="{x}" y="{y+18}" fill="#e6edf3" font-size="16" font-weight="600">{esc(value)}</text>')

# Languages bar
bar_y = y0 + 3 * ROW_H + 12
svg.append(f'<text x="{PAD}" y="{bar_y}" fill="#7d8590" font-size="10" letter-spacing="1">TOP LANGUAGES</text>')

bar_x = PAD
bar_w = W - PAD * 2
bar_h = 8
bar_top = bar_y + 10
for name, size in top_langs:
    seg = (size / total_size) * bar_w
    svg.append(
        f'<rect x="{bar_x:.1f}" y="{bar_top}" width="{seg:.1f}" height="{bar_h}" '
        f'fill="{lang_color.get(name, "#888")}"/>'
    )
    bar_x += seg
svg.append(f'<rect x="{PAD}" y="{bar_top}" width="{bar_w}" height="{bar_h}" rx="4" '
           f'fill="none" stroke="#30363d"/>')

# Legend
lx, ly = PAD, bar_top + 26
for name, size in top_langs:
    pct = size / total_size * 100
    svg.append(f'<circle cx="{lx+4}" cy="{ly-4}" r="4" fill="{lang_color.get(name, "#888")}"/>')
    svg.append(
        f'<text x="{lx+14}" y="{ly}" fill="#e6edf3" font-size="11">'
        f'{esc(name)} <tspan fill="#7d8590">{pct:.1f}%</tspan></text>'
    )
    lx += 140
    if lx > W - PAD - 140:
        lx = PAD
        ly += 18

svg.append("</svg>")
OUT.write_text("\n".join(svg), encoding="utf-8")
print(f"✓ wrote {OUT}")