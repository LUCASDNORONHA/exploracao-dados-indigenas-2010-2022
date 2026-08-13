# AGENTS.md

## Project overview

This repository contains the project **Panorama da População Indígena Brasileira 2010–2022**, based primarily on data from the 2010 and 2022 Brazilian Demographic Censuses published by IBGE.

The project combines exploratory data analysis, statistical analysis, geospatial analysis, data storytelling, Streamlit, and Power BI. It is currently considered a completed portfolio project, but it may receive new studies and methodological improvements in the future.

When modifying the repository, preserve the analytical narrative, reproducibility, existing visual identity, and separation of responsibilities already established in the codebase.

## Environment and dependency management

- Use Python 3.12 or a compatible version satisfying `requires-python = ">=3.12"`.
- Use `uv` as the dependency and environment manager.
- Do not introduce direct `pip install` instructions when an equivalent `uv` workflow is available.
- Treat `pyproject.toml` as the primary dependency declaration.
- Keep `uv.lock` synchronized whenever dependencies change.
- Development dependencies belong in the `dev` dependency group unless they are required at runtime.

Recommended environment setup:

```bash
uv sync
```

## Repository structure

The current source-code organization is:

```text
src/
├── analysis/
├── charts/
├── dashboard/
└── preprocessing/
```

Use these directories according to their responsibilities:

- `src/analysis/`: analytical and statistical computation independent of presentation.
- `src/charts/`: reusable charting and visualization code used by the analytical studies.
- `src/dashboard/`: Streamlit-specific application logic, metrics, formatting, pages, interactive charts, themes, and runtime utilities.
- `src/preprocessing/`: data preparation, transformation, dashboard dataset generation, and geospatial preprocessing.

Do not create a new top-level source directory when an existing responsibility already accommodates the implementation.

## Data conventions

The repository contains processed tabular, dashboard, and geospatial datasets under `data/processed/`.

General rules:

- Preserve source data provenance and IBGE semantics.
- Do not silently overwrite or reinterpret variables from the source data.
- Prefer explicit transformation steps over undocumented manual edits.
- Keep tabular and geospatial transformations reproducible whenever practical.
- Avoid duplicating large generated datasets without a clear analytical or application need.
- Before changing the format or location of existing processed data, verify all notebooks, dashboard modules, and tests that depend on it.

When adding new data sources, document their origin and role in the corresponding study and update the project documentation when necessary.

## Notebooks and future studies

Notebooks represent the analytical investigation and storytelling layer of the project.

When adding a new study:

- Preserve the chronological and thematic progression of the existing studies.
- Use a clear numeric prefix so the intended reading order remains evident.
- Keep notebooks focused on analysis, interpretation, and narrative.
- Move reusable transformations, calculations, plotting functions, or application logic into `src/` rather than duplicating substantial code across notebooks.
- Do not refactor completed studies merely for stylistic uniformity unless the change solves a concrete maintenance, correctness, or reproducibility problem.

A new study should normally extend the project rather than rewrite previous conclusions without analytical justification.

## Visualizations and storytelling

The project has an established visual identity and storytelling approach.

When modifying or adding visualizations:

- Preserve the existing design language unless a deliberate redesign is part of the task.
- Prefer titles that communicate the analytical finding rather than merely naming the chart type.
- Keep subtitles, annotations, labels, and explanatory text aligned with the narrative purpose of the study.
- Avoid introducing generic plotting defaults when an established project-specific treatment already exists.
- Maintain consistency between static analytical visualizations and the dashboard where appropriate.

## Dashboard

The Streamlit application is entered through:

```text
streamlit_app.py
```

Dashboard-specific code belongs primarily in `src/dashboard/`.

When changing the dashboard:

- Preserve separation between data loading, metrics, formatting, visualization, and page composition.
- Avoid concentrating substantial business or analytical logic in `streamlit_app.py`.
- Ensure dashboard changes remain compatible with the processed datasets under `data/processed/dashboard/`.
- Add or update tests whenever dashboard behavior, data contracts, metrics, or geospatial logic changes.

## Testing

The repository contains a pytest suite covering dashboard behavior, dashboard data, geospatial processing, regional and state views, methodology, statistical analysis, and statistical charts.

Run the full test suite after relevant code changes:

```bash
uv run pytest tests
```

Tests should be added or updated when modifying:

- analytical calculations;
- statistical functions;
- dashboard metrics or behavior;
- geospatial transformations;
- processed-data contracts;
- reusable chart logic whose behavior is testable.

Do not remove or weaken a test merely to make a failing implementation pass. Determine whether the implementation or the expected behavior should change.

## Continuous integration

The repository uses GitHub Actions through:

```text
.github/workflows/tests.yml
```

The workflow installs Python 3.12 and `uv`, synchronizes dependencies from the lockfile, and executes the pytest suite on pushes and pull requests targeting `main`.

Any change to dependency management, Python compatibility, or test commands should be reflected in the CI workflow when necessary.

## Code quality

The project currently declares Black, isort, Ruff, Flake8, and pytest as development tools.

Existing formatting configuration uses a line length of 88 characters for Black and isort.

When editing Python code:

- follow the existing module conventions;
- prefer clear, descriptive names;
- keep functions focused on a coherent responsibility;
- avoid unnecessary duplication;
- preserve type and data semantics;
- favor readable analytical code over premature abstraction.

Large modules may be split when there is a concrete maintainability benefit, but avoid architectural churn solely to make the directory tree appear more elaborate.

## Documentation

`README.md` is the public-facing description of the project. `AGENTS.md` is the operational guide for agents modifying the repository.

When repository structure, technologies, study sequence, dashboards, or execution instructions change materially:

- update the relevant public documentation;
- ensure examples and directory trees in `README.md` reflect the actual repository state;
- update this file when development conventions or architectural rules change.

When documentation and the actual repository disagree, inspect the current code and tree before making assumptions.

## Change discipline

Before considering a change complete:

1. Confirm that the change belongs in the chosen directory and module.
2. Preserve compatibility with existing studies unless the task explicitly requires a breaking change.
3. Update or add tests when behavior changes.
4. Run the relevant tests, preferably the full suite for cross-cutting changes.
5. Update documentation when structure, usage, or public behavior changes.
6. Avoid unrelated refactoring in the same change.

The project is intended to evolve incrementally. Prefer small, justified improvements over broad rewrites unless a future architectural review explicitly establishes a new structure.