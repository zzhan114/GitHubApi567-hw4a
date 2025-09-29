
from __future__ import annotations

import requests
from dataclasses import dataclass
from typing import List, Optional, Iterable, Tuple, Dict


@dataclass(frozen=True)
class RepoCommits:
    name: str
    commit_count: int


class GitHubAPIError(RuntimeError):
    """Raised when GitHub API returns an error or unexpected response."""
    pass


def _iter_paginated(
    session: requests.Session,
    url: str,
    params: Optional[Dict[str, str]] = None,
    timeout: int = 10,
) -> Iterable[list]:
    """
    Yield JSON arrays for each page until no 'next' link exists.
    Each page from these endpoints returns a list of items.
    """
    next_url = url
    while next_url:
        resp = session.get(next_url, params=params, timeout=timeout)
        # Reset params for subsequent 'next' URLs which already encode query params.
        params = None
        if resp.status_code == 404:
            raise GitHubAPIError("Resource not found (404). Check username/repository.")
        if resp.status_code == 403:
            # Likely rate-limited or forbidden
            msg = resp.json().get("message", "Forbidden or rate limited")
            raise GitHubAPIError(f"GitHub API error 403: {msg}")
        if not resp.ok:
            raise GitHubAPIError(f"GitHub API error {resp.status_code}: {resp.text}")

        page = resp.json()
        if not isinstance(page, list):
            raise GitHubAPIError("Unexpected response shape: expected a list.")

        yield page

        # Handle pagination via Link header
        link = resp.headers.get("Link", "")
        next_url = None
        if link:
            parts = [p.strip() for p in link.split(",")]
            for part in parts:
                if 'rel="next"' in part:
                    # format: <url>; rel="next"
                    start = part.find("<") + 1
                    end = part.find(">", start)
                    if start > 0 and end > start:
                        next_url = part[start:end]
                    break


def get_user_repo_commits(
    username: str,
    *,
    auth_token: Optional[str] = None,
    timeout: int = 10,
    per_page: int = 100,
) -> List[RepoCommits]:
    """
    Given a GitHub username, return a list of RepoCommits with commit counts for each repo.

    Design for testability:
    - Pure function relative to inputs (no globals).
    - Small helper _iter_paginated is isolated and unit-tested via mocking.
    - Clear, typed return value.
    - Raises GitHubAPIError for caller to assert in tests.

    Note: Commit counts are retrieved by paging through /commits to avoid truncation.
    """
    if not isinstance(username, str) or not username.strip():
        raise ValueError("username must be a non-empty string")

    session = requests.Session()
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GitHubApi567-hw4a/1.0",
    }
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    session.headers.update(headers)

    # 1) Get repos (owner-only to avoid forks/noise; adjust if needed)
    repos_url = f"https://api.github.com/users/{username}/repos"
    repo_params = {"type": "owner", "per_page": str(per_page), "sort": "full_name"}

    repos: List[Tuple[str, str]] = []  # (name, full_name)
    for page in _iter_paginated(session, repos_url, params=repo_params, timeout=timeout):
        for repo in page:
            name = repo.get("name")
            full_name = repo.get("full_name")
            if isinstance(name, str) and isinstance(full_name, str):
                repos.append((name, full_name))

    results: List[RepoCommits] = []

    # 2) For each repo, count commits (public only; private require auth)
    for name, full_name in repos:
        commits_url = f"https://api.github.com/repos/{full_name}/commits"
        commit_params = {"per_page": str(per_page)}
        count = 0
        for page in _iter_paginated(session, commits_url, params=commit_params, timeout=timeout):
            count += len(page)
        results.append(RepoCommits(name=name, commit_count=count))

    return results


def format_repo_commits(entries: Iterable[RepoCommits]) -> str:
    """Produce the exact output format specified by the assignment."""
    lines = []
    for rc in entries:
        lines.append(f"Repo: {rc.name} Number of commits: {rc.commit_count}")
    return "\n".join(lines)


def main(argv: Optional[Iterable[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="List repos and commit counts for a GitHub user.")
    parser.add_argument("username", help="GitHub username (e.g., richkempinski)")
    parser.add_argument("--token", help="Optional GitHub token to raise rate limits.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        entries = get_user_repo_commits(args.username, auth_token=args.token)
    except (GitHubAPIError, ValueError) as e:
        print(f"Error: {e}")
        return 1

    print(format_repo_commits(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
