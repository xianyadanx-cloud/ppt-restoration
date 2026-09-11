# Development and release checks

Use Python 3.9+ in a virtual environment:

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -q
python -m build
```

Tests generate small inputs in temporary directories. Core checks require no customer data or Office. Real renderer checks run only when a backend and PDF rasterizer are available.

Before publishing, install the wheel into a fresh environment and run from outside the checkout:

```bash
python -m venv /path/to/release-env
/path/to/release-env/bin/python -m pip install /path/to/dist/pptrestore-0.2.0-py3-none-any.whl
/path/to/release-env/bin/pptrestore --help
/path/to/release-env/bin/pptrestore doctor
```

Windows uses Scripts/python.exe and Scripts/pptrestore.exe. Verify prepare, the exported prompt, installed OCR resource and synthetic end-to-end tests against the wheel. Real restoration additionally requires image interpretation, user approvals and actual renderer verification.

Do not add reference screenshots, golden PPTX files, generated output, SDD records or machine-specific paths. Keep dependency and version metadata in pyproject.toml.

Choose and add a license before describing this as open source; the repository currently does not grant an explicit reuse license.
