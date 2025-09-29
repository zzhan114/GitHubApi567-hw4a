# tests/test_github_client_mocked.py
from unittest.mock import patch
import pytest

from github_api.github_client import (
    get_user_repo_commits,
    RepoCommits,
    GitHubAPIError,
    format_repo_commits,
)

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

def test_happy_path_with_pagination():
    # /users/<user>/repos  (single page)
    repos_page1 = [
        {"name": "Triangle567", "full_name": "john/Triangle567"},
        {"name": "Square567", "full_name": "john/Square567"},
    ]

    # /repos/<full_name>/commits pages
    tri_p1 = [{"sha": f"a{i}"} for i in range(100)]
    tri_p2 = [{"sha": "a100"}]
    sq_p1  = [{"sha": f"b{i}"} for i in range(27)]

    responses = [
        FakeResponse(200, repos_page1, headers={}),
        FakeResponse(200, tri_p1, headers=_link_header("https://api.github.com/next1")),
        FakeResponse(200, tri_p2, headers={}),
        FakeResponse(200, sq_p1,  headers={}),
    ]
    idx = {"i": 0}

    def fake_get(url, params=None, timeout=10):
        i = idx["i"]; idx["i"] += 1
        return responses[i]

    with patch("requests.Session.get", side_effect=fake_get):
        out = get_user_repo_commits("john")
        assert out == [
            RepoCommits(name="Triangle567", commit_count=101),
            RepoCommits(name="Square567",  commit_count=27),
        ]

def test_username_validation():
    with pytest.raises(ValueError):
        get_user_repo_commits("")
    with pytest.raises(ValueError):
        get_user_repo_commits(None)  # type: ignore[arg-type]

def test_user_not_found():
    def fake_get(url, params=None, timeout=10):
        return FakeResponse(404, {"message": "Not Found"})
    with patch("requests.Session.get", side_effect=fake_get):
        with pytest.raises(GitHubAPIError):
            get_user_repo_commits("nope")

def test_rate_limit():
    def fake_get(url, params=None, timeout=10):
        return FakeResponse(403, {"message": "API rate limit exceeded"})
    with patch("requests.Session.get", side_effect=fake_get):
        with pytest.raises(GitHubAPIError) as ei:
            get_user_repo_commits("someone")
        assert "rate" in str(ei.value).lower()

def test_output_format():
    s = format_repo_commits([RepoCommits("A", 3), RepoCommits("B", 0)])
    assert "Repo: A Number of commits: 3" in s
    assert "Repo: B Number of commits: 0" in s
