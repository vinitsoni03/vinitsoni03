"""Generate GitHub stats + top-languages SVG cards for the profile README.

Replaces the public github-readme-stats instance (its Vercel deployment is
paused, so the cards rendered as broken images). Runs in the snake workflow
and writes into the same output directory that gets pushed to the `output`
branch.

Usage:  python3 scripts/stats_cards.py <out_dir>
Env:    GITHUB_TOKEN (required), GH_USER (default: vinitsoni03)
Only public, non-fork repositories are counted, whatever the token can see.
"""

import base64
import json
import os
import sys
import urllib.request
from html import escape

USER = os.environ.get("GH_USER", "vinitsoni03")
TOKEN = os.environ["GITHUB_TOKEN"]

# Theme: the portfolio's (black, off-white ink, amber), same as scripts/build_assets.py
BG, BORDER, ACCENT, TEXT, MUTED = "#070707", "#2a2a2a", "#f2f2ef", "#91918f", "#4a4a48"
LANG_COLORS = ["#e8a33d", "#f2e4c8", "#c46a1c", "#91918f", "#8a4a16", "#4a4a48"]
FONT = "G, Geist, Inter, 'Segoe UI', system-ui, sans-serif"
# Geist subset written by build_assets.py; embedded so the cards match the other panels
_FONT_FILE = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "geist-subset.woff2")
FONT_FACE = (
    "@font-face { font-family: G; font-weight: 100 900; src: url(data:font/woff2;base64,"
    + base64.b64encode(open(_FONT_FILE, "rb").read()).decode() + ') format("woff2"); }'
    if os.path.exists(_FONT_FILE) else ""
)

QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount } }
      }
    }
    repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, ISSUE]) { totalCount }
    repositories(first: 100, after: $after, ownerAffiliations: OWNER,
                 privacy: PUBLIC, isFork: false) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""


def graphql(variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "User-Agent": "stats-cards"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    if "errors" in body:
        raise SystemExit(f"GraphQL error: {body['errors']}")
    return body["data"]["user"]


def fetch():
    """Walk all public repos (paginated) and aggregate stars + language bytes."""
    stars, langs, after, first = 0, {}, None, None
    while True:
        user = graphql({"login": USER, "after": after})
        first = first or user
        repos = user["repositories"]
        for repo in repos["nodes"]:
            stars += repo["stargazerCount"]
            for edge in repo["languages"]["edges"]:
                name = edge["node"]["name"]
                langs[name] = langs.get(name, 0) + edge["size"]
        if not repos["pageInfo"]["hasNextPage"]:
            break
        after = repos["pageInfo"]["endCursor"]
    cc = first["contributionsCollection"]
    cal = cc["contributionCalendar"]
    active = sum(1 for w in cal["weeks"] for d in w["contributionDays"] if d["contributionCount"])
    stats = [
        ("Contributions (last year)", cal["totalContributions"]),
        ("Commits (last year)", cc["totalCommitContributions"] + cc["restrictedContributionsCount"]),
        ("Active days (last year)", active),
        ("Public repos", first["repositories"]["totalCount"]),
        ("Repos contributed to", first["repositoriesContributedTo"]["totalCount"]),
        ("Languages used", len(langs)),
    ]
    if stars:  # only worth showing once there are some
        stats[-1] = ("Total stars", stars)
    return stats, langs


def frame(width, height, title, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
<style>
  {FONT_FACE}
  .t {{ font: 500 15px {FONT}; fill: {ACCENT}; }}
  .l {{ font: 400 14px {FONT}; fill: {TEXT}; }}
  .v {{ font: 500 14px {FONT}; fill: {ACCENT}; font-variant-numeric: tabular-nums; }}
  .s {{ font: 400 12px {FONT}; fill: {TEXT}; }}
  .row {{ opacity: 0; animation: in .5s ease-out forwards; }}
  @keyframes in {{ to {{ opacity: 1; }} }}
</style>
<rect x="0.5" y="0.5" rx="10" width="{width - 1}" height="{height - 1}" fill="{BG}" stroke="{BORDER}"/>
<text x="25" y="35" class="t">{escape(title)}</text>
<line x1="25" y1="48" x2="{width - 25}" y2="48" stroke="#fff" stroke-opacity=".12"/>
{body}
</svg>
"""


def stats_card(stats):
    rows = "\n".join(
        f'<g class="row" style="animation-delay:{150 + i * 120}ms" transform="translate(25,{80 + i * 26})">'
        f'<text class="l">{escape(label)}:</text>'
        f'<text x="285" class="v" text-anchor="end">{value:,}</text></g>'
        for i, (label, value) in enumerate(stats)
    )
    return frame(335, 97 + len(stats) * 26, "GitHub", rows)


def langs_card(langs, top=6):
    """One row per language (name, share, thin bar) on the same 26px rhythm as the
    stats card, so the two sit side by side at equal height."""
    items = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:top]
    total = sum(size for _, size in items) or 1
    body = []
    for i, (name, size) in enumerate(items):
        share = size / total
        color = LANG_COLORS[i % len(LANG_COLORS)]
        body.append(
            f'<g class="row" style="animation-delay:{150 + i * 120}ms" transform="translate(25,{80 + i * 26})">'
            f'<text class="l">{escape(name)}</text>'
            f'<rect x="110" y="-6" width="130" height="3" rx="1.5" fill="#fff" fill-opacity=".1"/>'
            f'<rect x="110" y="-6" width="{max(2, 130 * share):.1f}" height="3" rx="1.5" fill="{color}"/>'
            f'<text x="285" class="v" text-anchor="end">{100 * share:.1f}%</text></g>'
        )
    return frame(335, 97 + top * 26, "Languages", "\n".join(body))


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "dist"
    os.makedirs(out_dir, exist_ok=True)
    stats, langs = fetch()
    for name, svg in (("stats.svg", stats_card(stats)), ("top-langs.svg", langs_card(langs))):
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {out_dir}/{name}")


if __name__ == "__main__":
    main()
