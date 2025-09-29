
# Reflection: Developing with the Tester’s Perspective

**Goals I optimized for**
- **Determinism & Isolation:** The core function `get_user_repo_commits` is side-effect free (beyond HTTP), returns typed data, and throws a single custom exception class for all API failures. Tests can assert specific failure modes.
- **Pagination Correctness:** Commit counts often exceed one page. I implemented a robust `_iter_paginated` helper that follows the HTTP `Link` header `rel="next"` chain to avoid undercounting.
- **Mock-friendly Design:** All HTTP calls go through `requests.Session.get`, making it trivial to patch in unit tests with `unittest.mock`. Tests don’t touch the network, avoiding flakiness and rate limits.

**Key test cases**
1. **Happy path with pagination:** Two repos; one needs 2 commit pages; the other needs 1 page.
2. **Input validation:** Reject empty/non-string usernames with `ValueError`.
3. **404 handling:** Unknown user raises `GitHubAPIError`.
4. **403 handling (rate limit):** Surface the server’s message to help users understand transient failures.
5. **Output formatter:** Ensures exact string format matches the assignment requirement.

**Challenges & tradeoffs**
- **Rate limits:** Live tests can fail spuriously. I avoided this by mocking HTTP in unit tests. A CLI `--token` is supported for manual runs.
- **Large repositories:** Counting commits by paging is correct but can be slow for massive histories. For the assignment’s scope, it is acceptable and keeps logic simple and transparent.
- **Public vs private repos:** Without a token, only public repos are visible. Tests document this; token support is included but optional.

**Why this is easy to test**
- Single entry point with typed return.
- Explicit exceptions for error conditions.
- Pagination isolated and unit-tested.
- No hidden state or global config.

