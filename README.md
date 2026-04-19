<div align="center">

# FACEIT Python API Library

[![Python](https://img.shields.io/badge/Python-3.8%2B-FAD6C5?style=flat-square)](https://www.python.org/)
[![PyPI](https://img.shields.io/pypi/v/faceit?label=PyPI&style=flat-square&color=FAD6C5)](https://pypi.org/project/faceit/)
[![License](https://img.shields.io/badge/License-Apache_2.0-FAD6C5?style=flat-square)](https://opensource.org/licenses/Apache-2.0)
[![Downloads](https://img.shields.io/pypi/dm/faceit?label=Downloads&style=flat-square&color=FAD6C5)](https://pypi.org/project/faceit/)

[![FACEIT API](https://img.shields.io/badge/FACEIT_API-Reference-FF5500?style=flat-square&logo=faceit)](https://docs.faceit.com/docs)

**The easiest and most type-safe way to interact with the FACEIT API.**

<!-- Access FACEIT data — player stats, matches, and tournaments — directly from Python. -->

</div>

---

## Features

- **High-level, idiomatic API** — Interact with FACEIT as if it were a native Python service.
- **Full type safety** — Compatible with [mypy](https://mypy-lang.org/) and other type checkers.
- **Sync & async support** — Powered by [httpx](https://www.python-httpx.org/).
- **Pydantic models** — All data models inherit from [`pydantic.BaseModel`](https://docs.pydantic.dev/latest/concepts/models/).
- **Advanced pagination** — Supports both cursor-based and Unix timestamp pagination.
- **Flexible data access** — Choose between raw data and parsed models (e.g., `.raw_players` vs `.players`).
- **Page collection utilities** — Paginated responses in model mode are wrapped in an `ItemPage` collection with convenient methods, such as `.map()`, `.filter()`, `.find()`, and more.

## Installation

> Requires Python 3.8+

```bash
pip install faceit
```

For automatic environment variable loading (see [API Key Handling](#api-key-handling)):

```bash
pip install faceit[env]
```

## Quickstart

Get started in seconds. The following example demonstrates how to fetch a player's CS2 matches and perform a basic performance analysis using the synchronous API.

> [!IMPORTANT]
> Currently, only the Data Resource is available.  
> Access to this resource requires a valid API key, which you can obtain via the official [FACEIT Developer Portal](https://docs.faceit.com/getting-started/authentication/api-keys/).

```py
import faceit

# 1. Initialize the Data Resource.
# If `FACEIT_API_KEY` is set in your environment, no arguments are needed.
data = faceit.SyncDataResource()  # or faceit.SyncDataResource("YOUR_API_KEY")

# 2. Fetch player data by nickname.
nickname = input("Enter the player's nickname: ")
player = data.players.get(nickname)

# 3. Get all CS2 matches for the player.
# Returns an `ItemPage` — a type-safe collection with built-in utility methods.
matches = data.players.all_matches_stats(player.id, faceit.GameID.CS2)

print(f"Total CS2 matches for {player.nickname}: {len(matches)}")

# 4. Perform data analysis.
# Filter for matches with a positive K/D ratio (1 or higher).
positive_kd_matches = matches.filter(lambda m: m.kd_ratio >= 1)

total_count = len(matches)
positive_count = len(positive_kd_matches)

kd_rate = (positive_count / total_count * 100) if total_count > 0 else 0

print(f"Matches with positive K/D: {positive_count}")
print(f"{player.nickname}'s positive K/D rate: {kd_rate:.2f}%")
```

See additional usage examples in the [examples/](examples/) directory.

### API Key Handling

You can provide your API key directly in the constructor or let the library automatically load it from your environment.

- **Automatic:** Set the `FACEIT_API_KEY` environment variable. _(Requires `faceit[env]` or manual [`python-decouple`](https://github.com/HBNetwork/python-decouple) installation)_.
- **Manual:** Pass the key string directly: `SyncDataResource("YOUR_API_KEY")`.
- **Custom Variable:** To use a different environment variable name, pass an instance of `EnvKey`: `SyncDataResource(EnvKey("SECRET"))`

## Motivation

This project was born out of necessity while building a product that works closely with the FACEIT platform.  
Existing solutions did not offer the level of type safety, convenience, or abstraction needed for strong, maintainable code.  
The goal is to provide a solution approaching enterprise-level quality, while remaining accessible and useful for a wide range of users.

## Project Status & Roadmap

> [!WARNING]
> This library is currently in **early development**.
>
> - Many endpoints, models, and features are not yet implemented.
> - Webhooks, chat API, and some advanced features are not available yet.
> - In-code documentation is minimal, and the Sphinx-based documentation site is not yet ready.
> - Expect breaking changes and incomplete coverage.
>
> **Contributions and feedback are highly welcome!**

### Planned Improvements

- Support for more endpoints and models
- Webhooks and chat API integration
- Full documentation and usage guides

---

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
