# zarr-utils Documentation

This directory contains the documentation for zarr-utils, built with MkDocs.

## Building Documentation Locally

1. Install documentation dependencies:
```bash
pip install -e ".[docs]"
```

2. Serve documentation locally:
```bash
mkdocs serve
```

Then visit http://127.0.0.1:8000

3. Build static documentation:
```bash
mkdocs build
```

The built documentation will be in the `site/` directory.

## Documentation Structure

```
docs/
├── index.md                 # Home page
├── getting-started/         # Getting started guides
│   ├── installation.md
│   ├── quickstart.md
│   └── examples.md
├── user-guide/             # User guides for each feature
│   ├── inspect.md
│   ├── xarray.md
│   ├── visualization.md
│   ├── metadata.md
│   ├── debug.md
│   └── compatibility.md
├── api/                    # API reference (auto-generated)
│   ├── index.md
│   ├── inspect.md
│   ├── xarray.md
│   ├── visualization.md
│   ├── metadata.md
│   ├── debug.md
│   └── compat.md
└── development/            # Development guides
    ├── contributing.md
    ├── testing.md
    └── changelog.md
```

## Writing Documentation

- Use Markdown for all documentation
- Follow the existing structure and style
- Include code examples where appropriate
- Test all code examples
- Use relative links between pages

## API Documentation

API documentation is automatically generated from docstrings using mkdocstrings. To ensure proper documentation:

1. Use Google-style docstrings
2. Include type hints
3. Provide examples in docstrings
4. Document all public functions and classes

## Deployment

Documentation is automatically deployed to Read the Docs when changes are pushed to the main branch. The configuration is in `.readthedocs.yaml`.