#!/usr/bin/env python3
"""
Builds the animated SVG cards for the profile README.

  assets/header.svg    ASCII banner + typed tagline (static content)
  assets/neofetch.svg  neofetch-style card with live GitHub stats

Runs in GitHub Actions every 15 minutes. Stats come from the GitHub GraphQL API
using GITHUB_TOKEN (or GH_PAT if you add one, to also count private contributions).
Run locally with `--demo` to render using sample numbers, no token needed.
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from html import escape
from pathlib import Path

USER = "Prathu3110"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# ── palette ─────────────────────────────────────────────────────────────────
BG = "#0d1117"
BG_BAR = "#161b22"
BORDER = "#30363d"
FG = "#c9d1d9"
DIM = "#6e7681"
ACCENT = "#b392f0"     # identicon purple
ACCENT2 = "#79c0ff"
GREEN = "#7ee787"
ORANGE = "#ffa657"
PINK = "#ff7b9c"
YELLOW = "#e3b341"

FONT = "ConsolasFallback, Consolas, 'SF Mono', Menlo, 'DejaVu Sans Mono', 'Courier New', monospace"

# ── the ASCII art ───────────────────────────────────────────────────────────
BANNER = [
    '██████╗ ██████╗  █████╗ ████████╗██╗  ██╗██╗   ██╗██╗   ██╗███╗   ███╗███╗   ██╗ █████╗ ',
    '██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██║  ██║╚██╗ ██╔╝██║   ██║████╗ ████║████╗  ██║██╔══██╗',
    '██████╔╝██████╔╝███████║   ██║   ███████║ ╚████╔╝ ██║   ██║██╔████╔██║██╔██╗ ██║███████║',
    '██╔═══╝ ██╔══██╗██╔══██║   ██║   ██╔══██║  ╚██╔╝  ██║   ██║██║╚██╔╝██║██║╚██╗██║██╔══██║',
    '██║     ██║  ██║██║  ██║   ██║   ██║  ██║   ██║   ╚██████╔╝██║ ╚═╝ ██║██║ ╚████║██║  ██║',
    '╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝',
]

# Your GitHub identicon (5x5), redrawn in text using the letters of your handle.
IDENTICON = [
    "11111",
    "01110",
    "01110",
    "10101",
    "10101",
]


def identicon_ascii(cell_w=4, cell_h=2):
    letters = "PRATHU3110"
    rows, k = [], 0
    for r in IDENTICON:
        for _ in range(cell_h):
            line = []
            for c in r:
                if c == "1":
                    chunk = ""
                    for _ in range(cell_w):
                        chunk += letters[k % len(letters)]
                        k += 1
                    line.append(("on", chunk))
                else:
                    line.append(("off", " ·  "[:cell_w]))
            rows.append(line)
    return rows


# ── GitHub data ─────────────────────────────────────────────────────────────
QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100__PRIVACY__) {
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
      restrictedContributionsCount
      totalPullRequestContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch():
    # With your own PAT the query can see private repos (count, languages) and
    # private contributions. With the default Actions token it sees public only.
    pat = os.environ.get("GH_PAT")
    token = pat or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("set GITHUB_TOKEN (or run with --demo)")
    query = QUERY.replace("__PRIVACY__", "" if pat else ", privacy: PUBLIC")
    print("token:", "GH_PAT (public + private)" if pat else "GITHUB_TOKEN (public only)")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": USER},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(json.dumps(data["errors"], indent=2))
    return data["data"]["user"]


def demo_data():
    today = dt.date.today()
    days = [{"date": str(today - dt.timedelta(d)), "contributionCount": (1 if d < 6 else (d * 7) % 3)}
            for d in range(364, -1, -1)]
    return {
        "createdAt": "2024-05-21T00:00:00Z",
        "followers": {"totalCount": 8},
        "repositories": {"totalCount": 14, "nodes": [{
            "stargazerCount": 0,
            "languages": {"edges": [
                {"size": 3901, "node": {"name": "Python", "color": "#3572A5"}},
                {"size": 2550, "node": {"name": "TypeScript", "color": "#3178c6"}},
                {"size": 2240, "node": {"name": "JavaScript", "color": "#f1e05a"}},
                {"size": 888, "node": {"name": "CSS", "color": "#563d7c"}},
                {"size": 333, "node": {"name": "HTML", "color": "#e34c26"}},
                {"size": 88, "node": {"name": "C", "color": "#555555"}},
            ]}}]},
        "contributionsCollection": {
            "totalCommitContributions": 113, "restrictedContributionsCount": 0,
            "totalPullRequestContributions": 0,
            "contributionCalendar": {"totalContributions": 361,
                                     "weeks": [{"contributionDays": days}]},
        },
    }


def summarise(u):
    cc = u["contributionsCollection"]
    days = [d for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    days.sort(key=lambda d: d["date"])
    today = dt.date.today().isoformat()
    days = [d for d in days if d["date"] <= today]

    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        longest = max(longest, run)
    current = 0
    tail = list(reversed(days))
    if tail and tail[0]["contributionCount"] == 0:  # today not done yet: don't break the streak
        tail = tail[1:]
    for d in tail:
        if d["contributionCount"] == 0:
            break
        current += 1

    langs = {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            n = e["node"]["name"]
            langs.setdefault(n, [0, e["node"]["color"] or DIM])[0] += e["size"]
    total = sum(v[0] for v in langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1][0])[:5]
    top = [(n, v[1], v[0] / total * 100) for n, v in top]

    created = dt.datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00")).date()
    months = (dt.date.today().year - created.year) * 12 + dt.date.today().month - created.month
    uptime = f"{months // 12} yr{'s' if months // 12 != 1 else ''}, {months % 12} mo"

    return {
        "repos": u["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "followers": u["followers"]["totalCount"],
        "commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        "prs": cc["totalPullRequestContributions"],
        "contribs": cc["contributionCalendar"]["totalContributions"],
        "streak": current,
        "longest": longest,
        "langs": top,
        "uptime": uptime,
        "updated": dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).strftime("%d %b %Y, %H:%M IST"),
    }


# ── SVG helpers ─────────────────────────────────────────────────────────────
def t(text, fill=FG, weight=None):
    w = f' font-weight="{weight}"' if weight else ""
    return f'<tspan fill="{fill}"{w}>{escape(text)}</tspan>'


def window(width, height, title, body, extra_css=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="{FONT}">
<style>
  .ln {{ animation: rise .45s ease-out both; }}
  @keyframes rise {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
  .cursor {{ animation: blink 1s steps(1) infinite; }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
  {extra_css}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
</style>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>
<path d="M.5 34V12.5a12 12 0 0 1 12-12h{width - 25}a12 12 0 0 1 12 12V34z" fill="{BG_BAR}"/>
<line x1="0" y1="34" x2="{width}" y2="34" stroke="{BORDER}"/>
<circle cx="22" cy="17" r="6" fill="#ff5f57"/><circle cx="42" cy="17" r="6" fill="#febc2e"/><circle cx="62" cy="17" r="6" fill="#28c840"/>
<text x="{width / 2}" y="22" text-anchor="middle" font-size="12" fill="{DIM}">{escape(title)}</text>
{body}
</svg>
'''


# ── header ──────────────────────────────────────────────────────────────────
def header_svg():
    W, H = 900, 270
    fs, lh = 11.5, 13.6
    bw = 88 * fs * 0.6                     # rendered banner width
    x0 = (W - bw) / 2
    lines = []
    for i, row in enumerate(BANNER):
        lines.append(
            f'<text class="ln" style="animation-delay:{0.15 + i * 0.12:.2f}s" x="{x0:.1f}" y="{78 + i * lh}" '
            f'font-size="{fs}" fill="url(#grad)" textLength="{bw:.1f}" lengthAdjust="spacingAndGlyphs" '
            f'xml:space="preserve">{escape(row)}</text>')

    tagline = "ml · data engineering · inference & gpu · fintech"
    n, cw = len(tagline), 13 * 0.6
    ty = 78 + 6 * lh + 44
    prompt = f'{t("prathyumna", GREEN)}{t("@", DIM)}{t("github", ACCENT2)}{t(" ~ $ ", DIM)}'
    plen = len("prathyumna@github ~ $ ")
    tag_x = W / 2 - (plen + n + 1) * cw / 2
    tx = tag_x + plen * cw
    body = f'''
<defs>
  <linearGradient id="grad" x1="0" x2="1" y1="0" y2="0">
    <stop offset="0" stop-color="{ACCENT}"/><stop offset=".5" stop-color="{PINK}"/><stop offset="1" stop-color="{ACCENT2}"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-.6 0;.6 0;-.6 0" dur="8s" repeatCount="indefinite"/>
  </linearGradient>
  <clipPath id="type"><rect class="typer" x="{tx:.1f}" y="{ty - 16}" width="{n * cw + 2:.1f}" height="24"/></clipPath>
</defs>
{''.join(lines)}
<text x="{tag_x:.1f}" y="{ty}" font-size="13" xml:space="preserve" class="ln" style="animation-delay:1s">{prompt}</text>
<text x="{tx:.1f}" y="{ty}" font-size="13" xml:space="preserve" fill="{FG}" clip-path="url(#type)">{escape(tagline)}</text>
<g class="mover"><text x="{tx + n * cw:.1f}" y="{ty}" font-size="13" fill="{ACCENT}" class="cursor">█</text></g>
<text x="{W / 2}" y="{ty + 30}" font-size="11.5" text-anchor="middle" fill="{DIM}" class="ln" style="animation-delay:4.1s">B.Tech CSE (Big Data Analytics) · SRM IST, Chennai · ex-SWE intern @ Firstsource</text>
'''
    # typing effect: the clip grows one character at a time and the cursor follows it
    css = f'''.typer {{ animation: typing 2.6s steps({n}) 1.4s both; }}
  @keyframes typing {{ from {{ width: 0px; }} to {{ width: {n * cw + 2:.1f}px; }} }}
  .mover {{ animation: follow 2.6s steps({n}) 1.4s both; }}
  @keyframes follow {{ from {{ transform: translateX(-{n * cw:.1f}px); }} to {{ transform: none; }} }}'''
    return window(W, H, "~/Prathu3110 — zsh", body, css)


# ── neofetch card ───────────────────────────────────────────────────────────
def neofetch_svg(s):
    W = 900
    fs, lh, cw = 13, 19, 13 * 0.6
    top = 64

    def kv(key, val, vcol=FG):
        return t(key, ACCENT, "bold") + t(" " + "." * (12 - len(key)) + " ", DIM) + t(val, vcol)

    lang_bar = ""
    bar_w = 34
    used = 0
    segs = []
    for i, (name, color, pct) in enumerate(s["langs"]):
        n = max(1, round(pct / 100 * bar_w)) if i < len(s["langs"]) - 1 else bar_w - used
        n = max(0, min(n, bar_w - used))
        used += n
        segs.append(t("█" * n, color))
    lang_bar = "".join(segs)
    lang_legend = "  ".join(f"{n} {p:.0f}%" for n, _, p in s["langs"][:4])

    info = [
        t("prathyumna", GREEN, "bold") + t("@", DIM) + t("github", ACCENT2, "bold"),
        t("─" * 52, BORDER),
        kv("OS", "B.Tech CSE · Big Data Analytics '28"),
        kv("Host", "SRM IST Ramapuram, Chennai"),
        kv("Uptime", s["uptime"] + " on GitHub"),
        kv("Kernel", "ML / data engineering × finance"),
        kv("Shell", "python · go · c++ · typescript"),
        kv("Loading", "inference eng · CUDA · Go backend · DSA"),
        kv("Prev", "SWE Intern @ Firstsource Solutions"),
        kv("Web", "prathyumna-portfolio.vercel.app", ACCENT2),
        "",
        t("── github ", DIM) + t("─" * 42, BORDER),
        kv("Repos", f'{s["repos"]}') + t("   ★ ", YELLOW) + t(f'{s["stars"]}') + t("   followers ", DIM) + t(f'{s["followers"]}'),
        kv("Commits", f'{s["commits"]} this year') + t("   PRs ", DIM) + t(f'{s["prs"]}'),
        kv("Activity", f'{s["contribs"]} contributions'),
        kv("Streak", f'{s["streak"]} days', ORANGE) + t("   best ", DIM) + t(f'{s["longest"]} days', ORANGE),
        t("Langs", ACCENT, "bold") + t(" ....... ", DIM) + lang_bar,
        t(" " * 14 + lang_legend, DIM),
        "",
        "PALETTE",
    ]

    H = top + len(info) * lh + 40
    art = identicon_ascii()
    art_x = 40
    art_y = top + (len(info) * lh - len(art) * lh) / 2 - 4
    info_x = art_x + 24 * cw + 26

    out = []
    for i, row in enumerate(art):
        spans = "".join(
            f'<tspan fill="url(#ig)">{escape(c)}</tspan>' if kind == "on" else t(c, BORDER)
            for kind, c in row)
        out.append(f'<text class="ln" style="animation-delay:{0.05 + i * 0.05:.2f}s" x="{art_x}" y="{art_y + i * lh:.1f}" '
                   f'font-size="{fs}" font-weight="bold" xml:space="preserve">{spans}</text>')

    for i, line in enumerate(info):
        y = top + i * lh
        delay = 0.5 + i * 0.09
        if line == "PALETTE":
            sw = "".join(
                f'<rect class="ln" style="animation-delay:{delay + j * 0.05:.2f}s" x="{info_x + j * 26}" y="{y - 12}" width="22" height="14" rx="3" fill="{c}"/>'
                for j, c in enumerate([ACCENT, PINK, ORANGE, YELLOW, GREEN, ACCENT2, FG, DIM]))
            out.append(sw)
            out.append(f'<text x="{info_x + 8 * 26 + 6}" y="{y}" font-size="{fs}" fill="{ACCENT}" class="cursor">█</text>')
            continue
        if not line:
            continue
        out.append(f'<text class="ln" style="animation-delay:{delay:.2f}s" x="{info_x:.1f}" y="{y}" font-size="{fs}" xml:space="preserve">{line}</text>')

    out.append(f'<text x="{W - 20}" y="{H - 14}" font-size="10" text-anchor="end" fill="{DIM}">synced {escape(s["updated"])}</text>')

    body = f'''<defs><linearGradient id="ig" x1="0" y1="0" x2="1" y2="1" gradientUnits="userSpaceOnUse" gradientTransform="translate({art_x} {art_y - 12}) scale(190)">
  <stop offset="0" stop-color="{ACCENT}"/><stop offset="1" stop-color="{PINK}"/>
  </linearGradient></defs>
''' + "\n".join(out)
    return window(W, int(H), "prathyumna@github: ~ — neofetch", body)


def main():
    ASSETS.mkdir(exist_ok=True)
    stats = summarise(demo_data() if "--demo" in sys.argv else fetch())
    (ASSETS / "header.svg").write_text(header_svg(), encoding="utf-8")
    # Only rewrite the card when a stat actually changed, so frequent runs
    # don't make a commit every time just because the "synced" time moved.
    card = ASSETS / "neofetch.svg"
    new = neofetch_svg(stats)
    strip = lambda svg: "\n".join(l for l in svg.splitlines() if "synced " not in l)
    if not card.exists() or strip(card.read_text(encoding="utf-8")) != strip(new):
        card.write_text(new, encoding="utf-8")
        print("stats changed, card updated")
    else:
        print("no change in stats")
    print(json.dumps({k: v for k, v in stats.items() if k != "langs"}, indent=2))


if __name__ == "__main__":
    main()
