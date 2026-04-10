<div align="center">

# FACEIT Python API Library

[![Python](https://img.shields.io/badge/Python-3.8%2B-FAD6C5?style=flat-square)](https://www.python.org/)
[![PyPI](https://img.shields.io/pypi/v/faceit?label=PyPI&style=flat-square&color=FAD6C5)](https://pypi.org/project/faceit/)
[![License](https://img.shields.io/badge/License-Apache_2.0-FAD6C5?style=flat-square)](https://opensource.org/licenses/Apache-2.0)
[![Downloads](https://img.shields.io/pypi/dm/faceit?label=Downloads&style=flat-square&color=FAD6C5)](https://pypi.org/project/faceit/)

[![FACEIT API](https://img.shields.io/badge/FACEIT_API-Reference-FF5500?style=flat-square&logo=faceit)](https://docs.faceit.com/docs)

**The most easy-to-use, type-safe way to interact with the FACEIT API.**  
Access FACEIT data — player stats, matches, and tournaments directly from Python.

</div>

## Features

- **High-level, idiomatic API** — Interact with FACEIT as if it were a native Python service.
- **Full type safety** — Compatible with [mypy](https://mypy-lang.org/) and other type checkers.
- **Sync & async support** — Powered by [httpx](https://www.python-httpx.org/).
- **Pydantic models** — All data models inherit from [`pydantic.BaseModel`](https://docs.pydantic.dev/latest/usage/models/).
- **Advanced pagination** — Supports both cursor-based and Unix timestamp pagination.
- **Flexible data access** — Choose between raw data and parsed models (e.g., `.raw_players` / `.players`).
- **Page collection utilities** — Paginated responses in model mode are wrapped in an `ItemPage` collection with convenient methods, such as `.map()`, `.filter()`, `.find()`, and more.

## Installation

```
pip install faceit
```

Use `pip install faceit[env]` if you plan to load the API key from environment (see [API Key Handling](#api-key-handling)).

## Quickstart Example

You can get started in just a few lines of code.  
Below is a short example showing how to get the complete CS2 match history for a player using the synchronous API.

> [!IMPORTANT]
> Currently, only the data resource is available, and access requires a valid API key.  
> You can get your API key by following the steps in the [official FACEIT documentation](https://docs.faceit.com/getting-started/authentication/api-keys).

### API Key Handling

You can insert your API key directly in the constructor, or let the library automatically load it from your environment (e.g., `.env`, `settings.ini`).  
By default, the key is read from the `FACEIT_API_KEY` variable (in the environment). To use a different variable, pass an instance of `EnvKey` to the constructor:

```py
data = faceit.SyncDataResource(faceit.EnvKey("SECRET"))
```

> [!NOTE]
> Loading the API key from environment files requires either installing the `env` extra or installing [python-decouple](https://github.com/HBNetwork/python-decouple) yourself.

### Minimal Example

```py
import faceit

# Initialize the API client.
# If `FACEIT_API_KEY` is set in your environment, you can omit the argument.
data = faceit.SyncDataResource()  # or faceit.SyncDataResource("YOUR_API_KEY")

# Fetch player information by nickname.
player = data.players.get("m0NESY")

# Get all CS2 match history for the player.
# Returns an `ItemPage` collection (multifunctional tuple).
matches = data.players.all_history(player.id, faceit.GameID.CS2)

print(f"Total CS2 matches for {player.nickname}: {len(matches)}")

# Example: Find a match by its ID.
match_id = "1-964ea204-03cf-4292-99f8-44da63968463"
some_match = matches.find("id", match_id)

if some_match is None:
    print(f"No match found with ID {match_id}")
else:
    print(f"Found match with ID {match_id}: {some_match}")
```

<!-- See additional usage examples in the [examples/](examples/) directory. -->

## Motivation

This project was created because of a need while building a product that works closely with the FACEIT platform.  
Existing solutions did not offer the level of type safety, convenience, or abstraction needed for strong, maintainable code.  
The goal is to provide a solution approaching enterprise-level quality, while remaining accessible and useful for a wide range of users.

## Project Status & Roadmap

> [!WARNING]
> This library is currently in **early development**.  
> Many endpoints, models, and features are not yet implemented.  
> Webhooks, chat API, and some advanced features are not available yet.  
> In-code documentation is minimal, and the Sphinx-based documentation site is not yet ready.  
> Expect breaking changes and incomplete coverage.
>
> **Contributions and feedback are highly welcome!**

### Planned Improvements

- Support for more endpoints and models
- Webhooks and chat API integration
- Full documentation and usage guides

---

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
