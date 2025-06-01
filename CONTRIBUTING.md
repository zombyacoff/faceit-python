# Contributing to faceit-python

Thank you for your interest in improving **faceit-python**!  
We welcome contributions of all kinds – bug fixes, documentation, new features, and more.

## Code Style & Quality

- **Consistency:** Please follow the existing code style and conventions throughout the codebase.
- **Linting:** Use [ruff](https://github.com/astral-sh/ruff) for linting.
- **Type Checking:** Use [mypy](https://mypy-lang.org/) for static type checking.
- **Testing:** Tests are written with [pytest](https://docs.pytest.org/). High test coverage is encouraged; please add or update tests where appropriate.
- **Dependencies:** Managed with [uv](https://github.com/astral-sh/uv). Always work inside the uv environment and use uv for installing/updating dependencies.
- **Pre-commit Hooks:** All commits are checked using [pre-commit](https://pre-commit.com/) hooks.

> [!IMPORTANT]
> Before starting work, always run:
>
> ```
> make setup
> ```
>
> This will create the virtual environment, install all dependencies, and set up pre-commit hooks.
>
> **No Make? (e.g., Windows):**
> Run these commands manually:
>
> ```
> uv venv --python 3.8.0
> uv sync --all-extras
> pre-commit install
> ```

## Commit Messages

- **Clarity:** Write clear and descriptive commit messages that explain the purpose and context of your changes.
- **Conventional Commits:** Follow the [Conventional Commits](https://www.conventionalcommits.org/) standard. Examples:
  - `feat: add leagues endpoint`
  - `fix: correct typo in player model`
  - `refactor: enhance auth token retrieval from environment`
- **Atomicity:** Each commit should represent a logical, self-contained change.

## Areas Where Help Is Needed

- **Pydantic Models:** Help is especially appreciated in creating and refining Pydantic models for API responses. Reference the [official FACEIT Data API docs](https://docs.faceit.com/docs/data-api/data).
- **Endpoint Coverage:** Contributions to support currently unsupported FACEIT API endpoints are welcome.

## Contribution Workflow

1. **Fork** the repository and create your branch from `main`.
2. **Write** clear, focused code and commit messages.
3. **Test** your changes locally.
4. **Lint and check types** before submitting.
5. **Open a Pull Request** with a clear description of your changes and the motivation behind them.

## Community Standards

- Please be respectful and considerate in all interactions.
- By participating, you agree to abide by our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

Thank you for helping make **faceit-python** better!  
We appreciate your contributions and look forward to collaborating with you.
