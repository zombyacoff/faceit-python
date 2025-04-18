# FACEIT Python API Library

A fully type-safe, high-level Python wrapper for the [FACEIT REST API v4](https://docs.faceit.com/docs).
Provides a seamless, pythonic interface for interacting with FACEIT data — with both synchronous and asynchronous clients, strict type checking, and powerful pagination.

> **Python version:** `>=3.8`

## Features

- **High-level, idiomatic API** – Work with FACEIT as if it were a native Python service, not just raw HTTP.
- **Full type safety** – 100% compatible with [mypy](https://mypy-lang.org/) and other type checkers.
- **Sync \& async support** – Built on [httpx](https://www.python-httpx.org/); use whichever style fits your project.
- **Pydantic models** – All data models inherit from [pydantic.BaseModel](https://docs.pydantic.dev/latest/usage/models/), providing robust validation and convenient methods.
- **Advanced pagination** – Both cursor-based and unix-time-based iterators are included.
- **Flexible data access** – Choose between raw data and fully parsed models (`resources.raw_players` vs `resources.players`).
- **Page collection utilities** – Paginated responses in model mode are wrapped in an `ItemPage` collection, supporting convenient methods like `.map()`, `.filter()`, `.find()`, and more.

## Installation

```bash
pip install faceit
```

## Quickstart Example

Below is a minimal example demonstrating how to retrieve the full CS2 match history for a player using the synchronous API.
Replace the API key with your personal FACEIT API key (see [how to get one](https://docs.faceit.com/getting-started/authentication/api-keys)).

```python
import faceit

with faceit.Faceit("YOUR_API_KEY") as f:
    player = f.resources.players.get("s1mple")
    # Returns an ItemPage collection (fully-featured iterable)
    matches = f.resources.players.all_history(player.id, faceit.GameID.CS2)
    print(f"Total CS2 matches for s1mple: {len(matches)}")
    # Example: find a match by attribute
    some_match = matches.find("id", "some_match_id")
    print(some_match)
```

## Usage Notes

- All data models are implemented using [pydantic](https://docs.pydantic.dev/latest/usage/models/), providing validation, serialization, and methods like `.model_dump()` and `.model_dump_json()`.
- Both synchronous (`faceit.Faceit`) and asynchronous (`faceit.AsyncFaceit`) clients are available.
- You can either pass your API key directly or provide a pre-configured HTTP client (`faceit.SyncClient` or `faceit.AsyncClient`) to the constructor. Additional HTTP client options are supported.
- Paginated queries return an `ItemPage` collection in model mode, supporting convenient operations such as `map`, `filter`, and attribute-based search.
- Both raw and model-based data access are supported (e.g., `resources.raw_players` for raw dictionaries, `resources.players` for validated models).
- The library is strictly type-annotated and fully compatible with [mypy](https://mypy-lang.org/).

## Motivation

This project was created out of necessity during the development of a product requiring deep integration with the FACEIT platform.
Existing solutions did not offer the level of type safety, convenience, and abstraction needed for robust, maintainable code.
The goal is to provide a solution approaching enterprise-level quality, while remaining accessible and useful for a wide range of users.

## Examples

Additional usage examples are available in the [`examples/`](examples/) directory.

## Project Status & Roadmap

> [!NOTE]
> This library is in **early development**.
> Many endpoints, models, and features are not yet implemented.
> Webhooks, chat API, and some advanced features are not available yet.
> Inline code documentation is minimal, and the Sphinx documentation site is not yet ready.
> Expect breaking changes and incomplete coverage.
> **Contributions and feedback are highly welcome!**

Planned improvements:

- More endpoints and models
- Webhooks and chat API support
- Complete documentation and usage guides

## Contributing

Contributions, bug reports, and feature requests are welcome!
Please open an issue or pull request on GitHub.
If you want to help with models, documentation, or testing, see the [CONTRIBUTING.md](CONTRIBUTING.md) (coming soon).

## About

This library is not just a thin HTTP wrapper — it is designed to provide a **high-level, pythonic interface** that abstracts away the complexities of the FACEIT API.
With advanced pagination, strict typing, and pydantic models, you can focus on your logic, not on API details.

## License

Apache 2.0 License
Copyright © 2025 Alexey Svidersky (zombyacoff)

See [LICENSE](LICENSE) for details.
