[![Build Status](https://app.travis-ci.com/zzhan114/GitHubApi567-hw4a.svg?branch=main)](https://app.travis-ci.com/zzhan114/GitHubApi567-hw4a)

# GitHubApi567-hw4a

Simple Python module that, given a GitHub username, lists each repository and the number of commits in that repo.

This implementation is written **with the tester's perspective** in mind:
- Small, pure functions with clear inputs/outputs
- Deterministic error handling via custom `GitHubAPIError`
- Pagination handled explicitly (commits can exceed one page)
- Unit tests that **mock HTTP** to avoid rate limits and flakiness

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m github_api.github_client richkempinski
```

Example output:

```
Repo: hellogitworld Number of commits: 30
...
```

> Tip: Add `--token <GITHUB_TOKEN>` to raise rate limits if needed.

## Run tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

## CI

### GitHub Actions (recommended for this course)
This repo includes a sample workflow at `.github/workflows/ci.yml`.

### Travis CI
Add a repository in Travis and ensure you include `.travis.yml` from below.

### CircleCI
Add a project in Circle and use `.circleci/config.yml`.

## Design Notes (Tester Perspective)

See **`reflection.md`** for a concise write-up about design decisions and testing challenges.

