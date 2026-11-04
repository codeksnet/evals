# Contributing

Issues and PRs welcome.

```sh
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest && ruff check .
```

- One PR per feature, kept small, with tests.
- Eval sets must be synthetic or anonymized. No client data, no real user data.
- Never commit secrets; use `.env.example`. Install the hook: `pre-commit install` (gitleaks).

By contributing you agree your work is released under the MIT license.
