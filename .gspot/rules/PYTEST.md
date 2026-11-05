# pytest

Read this rule when you write or change a pytest test.

Read TESTING.md too. Use pytest fixtures for runtime boundaries and test resources.

- Use `monkeypatch` to replace attributes, environment variables, or working folders. Its fixture restores changes
  after the test; use `monkeypatch.context()` when a patch needs a shorter lifetime.
- Use `tmp_path` for files that a test creates. Each test gets its own folder; keep its files inside that folder.
- Keep mutable fixtures at function scope. Give a fixture a broader scope only when tests can share its resource
  without changing each other's results.
- Restore fakes that `monkeypatch` does not own with a context manager or a fixture's `yield` cleanup. Cleanup runs
  even when the assertion fails.
