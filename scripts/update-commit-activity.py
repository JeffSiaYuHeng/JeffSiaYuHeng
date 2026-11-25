from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

USERNAME = "JeffSiaYuHeng"
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "commit-activity.svg"


def github_pages(path, token, params, allow_empty=False):
    page = 1
    while True:
        query = urlencode({**params, "page": page, "per_page": 100})
        request = Request(
            f"https://api.github.com/{path}?{query}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "User-Agent": "JeffSiaYuHeng-profile-activity",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urlopen(request, timeout=25) as response:
                items = json.load(response)
                has_next = 'rel="next"' in response.headers.get("Link", "")
        except HTTPError as error:
            if allow_empty and error.code == 409:
                return
            raise RuntimeError(f"GitHub request failed (HTTP {error.code})") from None
        except (TimeoutError, URLError):
            raise RuntimeError("GitHub request failed") from None
        if not isinstance(items, list):
            raise RuntimeError("GitHub returned an unexpected page")
        yield from items
        if not has_next:
            return
        page += 1


def count_private_commits(today, token):
    start = today - timedelta(days=29)
    repositories = github_pages(
        "user/repos", token, {"visibility": "private", "affiliation": "owner"}
    )
    commits = set()
    owned_repositories = 0
    for repo in repositories:
        if not repo["private"] or repo["owner"]["login"].casefold() != USERNAME.casefold():
            continue
        owned_repositories += 1
        name = quote(repo["name"], safe="")
        for commit in github_pages(
            f"repos/{USERNAME}/{name}/commits",
            token,
            {
                "author": USERNAME,
                "since": f"{start.isoformat()}T00:00:00Z",
                "until": f"{today.isoformat()}T23:59:59Z",
            },
            allow_empty=True,
        ):
            commits.add(commit["sha"])
    if not owned_repositories:
        raise RuntimeError("No owned private repositories are visible to the token")
    return len(commits)


def render_card(total, today):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="500" height="90" viewBox="0 0 500 90" role="img" aria-labelledby="title">
  <title id="title">{total:,} private-repository commits over 30 days as of {today.isoformat()} UTC</title>
  <defs>
    <linearGradient id="plate" x2="1" y2="1">
      <stop stop-color="#23352b"/>
      <stop offset="1" stop-color="#101914"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="498" height="88" rx="8" fill="url(#plate)" stroke="#658477"/>
  <path d="M9 14v62" stroke="#8fd6ac" stroke-width="2"/>
  <path d="M383 21h95m-95 6h95" stroke="#6d9583" opacity=".45" stroke-dasharray="2 4"/>
  <g font-family="ui-monospace, SFMono-Regular, Consolas, monospace">
    <text x="25" y="31" fill="#c3d3c9" font-size="13">PRIVATE REPOSITORY COMMITS · 30 DAYS</text>
    <text x="25" y="68" fill="#a9edc7" font-size="30" font-weight="700">{total:,}</text>
    <text x="479" y="66" text-anchor="end" fill="#c3d3c9" font-size="12">{today.isoformat()} UTC</text>
  </g>
</svg>
"""


if __name__ == "__main__":
    token = os.environ.get("PROFILE_ACTIVITY_TOKEN", "").strip()
    if not token:
        print("Private activity token is unavailable; keeping the existing snapshot.")
    else:
        today = datetime.now(timezone.utc).date()
        OUTPUT.write_text(render_card(count_private_commits(today, token), today), encoding="utf-8")
