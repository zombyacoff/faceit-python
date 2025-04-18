# FACEIT Python API Library

A fully type-safe, high-level Python wrapper for the [FACEIT REST API v4](https://docs.faceit.com/docs).  
Provides a seamless, pythonic interface for interacting with FACEIT data — with both synchronous and asynchronous clients, strict type checking, and powerful pagination.

---

**Supported Python version:** **3.8+**

---

## Features

- **High-level, idiomatic API** – Work with FACEIT as if it were a native Python service, not just raw HTTP.
- **Full type safety** – 100% compatible with [mypy](https://mypy-lang.org/) and other type checkers.
- **Sync & async support** – Built on [httpx](https://www.python-httpx.org/), choose the style you prefer.
- **Pydantic models** – All data models inherit from [pydantic.BaseModel](https://docs.pydantic.dev/latest/usage/models/), giving you validation, parsing, and rich model methods out of the box.
- **Advanced pagination** – Both cursor-based and unix-time-based iterators included.

---

## Installation

```bash
pip install faceit
```

---

## Quickstart Example

Below is a minimal example demonstrating how to retrieve the full CS2 match history for a player using the synchronous API.
Replace `"API_KEY"` with your personal FACEIT API key (see [how to get one](https://docs.faceit.com/getting-started/authentication/api-keys)).

```python
import os
import faceit

API_KEY = os.getenv("API_KEY", "N/A")

def main():
    with faceit.Faceit(API_KEY) as f:
        player = f.resources.players.get("s1mple")
        matches = f.resources.players.all_history(player.id, faceit.GameID.CS2)

    print(f"Total CS2 matches for s1mple: {len(matches)}")

if __name__ == "__main__":
    main()
```

---

## Usage Notes

- All data models are implemented using [pydantic](https://docs.pydantic.dev/latest/usage/models/), providing robust validation, serialization, and convenient methods such as `.dict()` and `.json()`.
- Both synchronous (`faceit.Faceit`) and asynchronous (`faceit.AsyncFaceit`) clients are available.
- An API key can be provided directly, or a pre-configured HTTP client (`faceit.SyncClient` or `faceit.AsyncClient`) can be passed to the constructor. Additional HTTP client options are supported.
- Advanced pagination is supported, including both cursor-based and unix-time-based iterators.
- The library is strictly type-annotated and fully compatible with [mypy](https://mypy-lang.org/).

---

## Project Status & Roadmap

> **Warning:**  
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

---

## Contributing

Contributions, bug reports, and feature requests are welcome!  
Please open an issue or pull request on GitHub.  
If you want to help with models, docs, or testing, see the [CONTRIBUTING.md](CONTRIBUTING.md) (coming soon).

---

## License

Apache 2.0 License  
Copyright © 2025 Alexey Svidersky (zombyacoff)

See [LICENSE](LICENSE) for details.

---

## About

This library is not just a thin HTTP wrapper — it aims to provide a **high-level, pythonic interface** that abstracts away the complexities of the FACEIT API.  
With advanced pagination, strict typing, and pydantic models, you can focus on your logic, not on API details.

---

_См. также: [README_ru.md](README_ru.md) для русской версии._
