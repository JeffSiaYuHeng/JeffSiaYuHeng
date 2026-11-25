from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

USERNAME = "JeffSiaYuHeng"
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "commit-activity.svg"


def fetch_commit_count(today):
    start = today - timedelta(days=29)
    query = urlencode({
        "q": f"author:{USERNAME} author-date:{start.isoformat()}..{today.isoformat()}",
        "per_page": 1,
    })
    request = Request(
        f"https://api.github.com/search/commits?{query}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "JeffSiaYuHeng-profile-activity",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    # Anonymous requests only search public repositories.
    with urlopen(request, timeout=20) as response:
        result = json.load(response)
    total = result.get("total_count")
    if result.get("incomplete_results") is not False or type(total) is not int or total < 0:
        raise RuntimeError("GitHub did not return a complete commit count")
    return total


def render_card(total, today):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="500" height="90" viewBox="0 0 500 90" role="img" aria-labelledby="title">
  <title id="title">{total:,} public GitHub commits over 30 days as of {today.isoformat()} UTC</title>
  <rect x="1" y="1" width="498" height="88" rx="8" fill="#101c19" stroke="#365951"/>
  <g font-family="ui-monospace, SFMono-Regular, Consolas, monospace">
    <text x="20" y="31" fill="#b6d2c7" font-size="13">PUBLIC GITHUB COMMITS · 30 DAYS</text>
    <text x="20" y="68" fill="#9df2cd" font-size="30" font-weight="700">{total:,}</text>
    <text x="479" y="66" text-anchor="end" fill="#b6d2c7" font-size="12">{today.isoformat()} UTC</text>
  </g>
</svg>
"""


if __name__ == "__main__":
    today = datetime.now(timezone.utc).date()
    OUTPUT.write_text(render_card(fetch_commit_count(today), today), encoding="utf-8")
