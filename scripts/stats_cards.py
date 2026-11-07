"""Generate GitHub stats + top-languages SVG cards for the profile README.

Replaces the public github-readme-stats instance (its Vercel deployment is
paused, so the cards rendered as broken images). Runs in the snake workflow
and writes into the same output directory that gets pushed to the `output`
branch.

Usage:  python3 scripts/stats_cards.py <out_dir>
Env:    GITHUB_TOKEN (required), GH_USER (default: vinitsoni03)
Only public, non-fork repositories are counted, whatever the token can see.
"""

import json
import os
import sys
import urllib.request
from html import escape

USER = os.environ.get("GH_USER", "vinitsoni03")
TOKEN = os.environ["GITHUB_TOKEN"]

# Theme, matching the rest of the README
BG, BORDER, ACCENT, TEXT, MUTED = "#0a0e14", "#1a2332", "#4fd8c4", "#8892a0", "#4d5765"
LANG_COLORS = ["#4fd8c4", "#e8a33d", "#7aa2f7", "#f7768e", "#9ece6a", "#bb9af7"]
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif"

QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      totalPullRequestContributions
      totalIssueContributions
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
    stats = [
        ("Total stars", stars),
        ("Commits (last year)", cc["totalCommitContributions"] + cc["restrictedContributionsCount"]),
        ("Pull requests", cc["totalPullRequestContributions"]),
        ("Issues", cc["totalIssueContributions"]),
        ("Contributed to", first["repositoriesContributedTo"]["totalCount"]),
        ("Public repos", first["repositories"]["totalCount"]),
    ]
    return stats, langs


def frame(width, height, title, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
<style>
  .t {{ font: 600 18px {FONT}; fill: {ACCENT}; }}
  .l {{ font: 400 14px {FONT}; fill: {TEXT}; }}
  .v {{ font: 700 14px {FONT}; fill: {ACCENT}; }}
  .s {{ font: 400 12px {FONT}; fill: {TEXT}; }}
  .row {{ opacity: 0; animation: in .5s ease-out forwards; }}
  @keyframes in {{ to {{ opacity: 1; }} }}
</style>
<rect x="0.5" y="0.5" rx="6" width="{width - 1}" height="{height - 1}" fill="{BG}" stroke="{BORDER}"/>
<text x="25" y="35" class="t">{escape(title)}</text>
{body}
</svg>
"""


def stats_card(stats):
    rows = "\n".join(
        f'<g class="row" style="animation-delay:{150 + i * 120}ms" transform="translate(25,{68 + i * 26})">'
        f'<text class="l">{escape(label)}:</text>'
        f'<text x="285" class="v" text-anchor="end">{value:,}</text></g>'
        for i, (label, value) in enumerate(stats)
    )
    return frame(335, 85 + len(stats) * 26, f"{USER}'s GitHub Stats", rows)


def langs_card(langs, top=6):
    items = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:top]
    total = sum(size for _, size in items) or 1
    width, bar_w = 335, 285
    # Stacked progress bar
    x, bar = 25.0, []
    for i, (_, size) in enumerate(items):
        w = bar_w * size / total
        bar.append(f'<rect x="{x:.2f}" y="52" width="{w:.2f}" height="8" fill="{LANG_COLORS[i % len(LANG_COLORS)]}"/>')
        x += w
    clip = f'<clipPath id="c"><rect x="25" y="52" width="{bar_w}" height="8" rx="4"/></clipPath>'
    body = [clip, f'<g clip-path="url(#c)">{"".join(bar)}</g>']
    # Two-column legend
    for i, (name, size) in enumerate(items):
        cx, cy = 25 + (i % 2) * 150, 85 + (i // 2) * 24
        color = LANG_COLORS[i % len(LANG_COLORS)]
        body.append(
            f'<g class="row" style="animation-delay:{150 + i * 100}ms" transform="translate({cx},{cy})">'
            f'<circle cx="5" cy="-4" r="5" fill="{color}"/>'
            f'<text x="16" class="s">{escape(name)} {100 * size / total:.1f}%</text></g>'
        )
    height = 85 + ((len(items) + 1) // 2) * 24
    return frame(width, height, "Most Used Languages", "\n".join(body))


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
