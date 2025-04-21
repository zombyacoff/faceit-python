# FACEIT Python API Library

[![python](https://img.shields.io/badge/python-3.8%2B-3776ab?style=flat-square&labelColor=ffffff&color=2e86c1)](https://www.python.org/)
[![pypi](https://img.shields.io/pypi/v/faceit?style=flat-square&labelColor=ffffff&color=43a047)](https://pypi.org/project/faceit/)

A fully type-safe, high-level Python wrapper for the [FACEIT REST API](https://docs.faceit.com/docs).
Provides a seamless, pythonic interface for interacting with FACEIT data — with both synchronous and asynchronous clients, strict type checking, and powerful pagination.

### Requirements

- Python 3.8 or higher

## Features

- **High-level, idiomatic API** – Work with FACEIT as if it were a native Python service.
- **Full type safety** – Compatible with [mypy](https://mypy-lang.org/) and other type checkers.
- **Sync & async support** – Built on [httpx](https://www.python-httpx.org/).
- **Pydantic models** – All data models inherit from [pydantic.BaseModel](https://docs.pydantic.dev/latest/usage/models/).
- **Advanced pagination** – Both cursor-based and unix-time-based iterators.
- **Flexible data access** – Choose between raw data and parsed models (`resources.raw_players` / `resources.players`).
- **Page collection utilities** – Paginated responses in model mode are wrapped in an `ItemPage` collection with convenient methods: `.map()`, `.filter()`, `.find()`, etc.

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
    print(f"First match with the given ID: {some_match or 'No match found'}")
```

### More Examples

See additional usage examples in the [`examples/`](examples/) directory.

## Usage Notes

- Both synchronous (`faceit.Faceit`) and asynchronous (`faceit.AsyncFaceit`) clients are available.
- You can pass your API key directly or provide a pre-configured HTTP client (`faceit.SyncClient` or `faceit.AsyncClient`).
- Paginated queries in model mode return an `ItemPage` collection with utility methods.
- Both raw and model-based data access are supported.

## Motivation

This project was created out of necessity during the development of a product requiring deep integration with the FACEIT platform.
Existing solutions did not offer the level of type safety, convenience, and abstraction needed for robust, maintainable code.
The goal is to provide a solution approaching enterprise-level quality, while remaining accessible and useful for a wide range of users.

## Project Status & Roadmap

> [!WARNING]
>
> This library is currently in **early development**.
> Many endpoints, models, and features are not yet implemented.
> Webhooks, chat API, and some advanced features are not available yet.
> Inline code documentation is minimal, and the Sphinx documentation site is not yet ready.
> Expect breaking changes and incomplete coverage.
>
> **Contributions and feedback are highly welcome!**

### Planned Improvements

- Support for more endpoints and models
- Webhooks and chat API integration
- Complete documentation and usage guides

## About

This library is designed to provide a **high-level, pythonic interface** that abstracts away the complexities of the FACEIT API.
With advanced pagination, strict typing, and pydantic models, you can focus on your logic, not on API details.

## Contributing

Contributions, bug reports, and feature requests are welcome!
Please open an issue or pull request on GitHub.
If you want to help with models, documentation, or testing, see the [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache 2.0 License  
Copyright © 2025 Alexey Svidersky (zombyacoff)

See [LICENSE](LICENSE) for details.
