
import json
from types import SimpleNamespace
from unittest.mock import patch, Mock

import pytest

from github_api.github_client import get_user_repo_commits, RepoCommits, GitHubAPIError, format_repo_commits


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, headers=None, text=""):
        self.status_code = status_code
        self._json = json_data
        self.headers = headers or {}
        self.text = text

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    def json(self):
        return self._json


def _link_header(next_url: str | None):
    if not next_url:
        return {}
    return {"Link": f'<{next_url}>; rel="next", <https://api.github.com/some>; rel="last"'}


def test_happy_path_two_repos_with_pagination(monkeypatch):
    # Simulate: user has 2 repos; commits paginated over 2 pages for one repo, 1 page for the other.
    repos_page1 = [
        {"name": "Triangle567", "full_name": "john/Triangle567"},
        {"name": "Square567", "full_name": "john/Square567"},
    ]

    commits_tri_p1 = [{"sha": f"a{i}"} for i in range(100)]
    commits_tri_p2 = [{"sha": "a100"}]
    commits_sq_p1 = [{"sha": f"b{i}"} for i in range(27)]

    # Ordered responses from Session.get
    responses = [
        # GET /users/john/repos (single page)
        FakeResponse(200, repos_page1, headers={}),
        # GET /repos/john/Triangle567/commits page 1 -> has next
        FakeResponse(200, commits_tri_p1, headers=_link_header("https://api.github.com/next1")),
        # GET next page for Triangle567
        FakeResponse(200, commits_tri_p2, headers={}),
        # GET /repos/john/Square567/commits
        FakeResponse(200, commits_sq_p1, headers={}),
    ]
    call_idx = {"i": 0}

    def fake_get(url, params=None, timeout=10):
        i = call_idx["i"]
        call_idx["i"] += 1
        return responses[i]

    with patch("requests.Session.get", side_effect=fake_get):
        out = get_user_repo_commits("john")
        assert out == [
            RepoCommits(name="Triangle567", commit_count=101),
            RepoCommits(name="Square567", commit_count=27),
        ]


def test_username_validation():
    with pytest.raises(ValueError):
        get_user_repo_commits("")

    with pytest.raises(ValueError):
        get_user_repo_commits(None)  # type: ignore[arg-type]


def test_user_not_found_raises():
    responses = [FakeResponse(404, {"message": "Not Found"})]

    def fake_get(url, params=None, timeout=10):
        return responses[0]

    with patch("requests.Session.get", side_effect=fake_get):
        with pytest.raises(GitHubAPIError):
            get_user_repo_commits("nope")


def test_rate_limited_raises():
    responses = [FakeResponse(403, {"message": "API rate limit exceeded for 1.2.3.4."})]

    def fake_get(url, params=None, timeout=10):
        return responses[0]

    with patch("requests.Session.get", side_effect=fake_get):
        with pytest.raises(GitHubAPIError) as ei:
            get_user_repo_commits("someone")
        assert "rate limit" in str(ei.value).lower()


def test_format_output():
    entries = [RepoCommits("A", 3), RepoCommits("B", 0)]
    s = format_repo_commits(entries)
    assert "Repo: A Number of commits: 3" in s
    assert "Repo: B Number of commits: 0" in s
