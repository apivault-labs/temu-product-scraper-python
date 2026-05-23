# Contributing

Thanks for your interest in improving this SDK.

## Reporting bugs

Open a [GitHub issue](https://github.com/apivault-labs/temu-product-scraper-python/issues)
with:
- Python version (`python --version`)
- SDK version (`pip show temu-product-scraper`)
- A minimal reproducer
- The full traceback or unexpected output

## Suggesting features

- **Client-side improvements** (better filters, async client, retries) — open an issue
- **New extracted fields** (more risk patterns, new derived metrics) — those live in
  the underlying Apify actor; open an issue and we'll discuss

## Development setup

```bash
git clone https://github.com/apivault-labs/temu-product-scraper-python.git
cd temu-product-scraper-python
python -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .
```

## Pull requests

- One PR per feature/bugfix
- Add a line to `CHANGELOG.md` under `[Unreleased]`
- Match existing code style (PEP 8, type hints)

## License

By contributing you agree your code will be released under the MIT license.
