# FACEIT Python API Library

![python](https://img.shields.io/badge/python-3.8%2B-3776ab?style=flat-square)
![pypi](https://img.shields.io/pypi/v/faceit?style=flat-square&color=43a047)

This library makes it easy to access and use data from the FACEIT gaming platform – such as player stats, matches, and tournaments – directly from your Python programs, without needing to understand the technical details of the FACEIT API. Automate and integrate FACEIT data into your projects, whether building apps, analyzing stats, or creating tools for esports and gaming.

**See the [official FACEIT API documentation](https://docs.faceit.com/docs) for details about the available data and endpoints.**

## Requirements

- Python 3.8 or higher

## Features

- **High-level, idiomatic API** – Interact with FACEIT as if it were a native Python service.
- **Full type safety** – Compatible with [mypy](https://mypy-lang.org/) and other type checkers.
- **Sync & async support** – Powered by [httpx](https://www.python-httpx.org/).
- **Pydantic models** – All data models inherit from [`pydantic.BaseModel`](https://docs.pydantic.dev/latest/usage/models/).
- **Advanced pagination** – Supports both cursor-based and unix-time-based iterators.
- **Flexible data access** – Choose between raw data and parsed models (e.g., `.raw_players` / `.players`).
- **Page collection utilities** – Paginated responses in model mode are wrapped in an `ItemPage` collection with convenient methods, such as `.map()`, `.filter()`, `.find()`, and more.

## Installation

```
pip install faceit
```

You can also install with the `env` extra to enable loading the API key from environment files (details below):

```
pip install faceit[env]
```

## Quickstart Example

You can get started in just a few lines of code.  
Below is a minimal example demonstrating how to retrieve the complete CS2 match history for a player using the synchronous API.

> [!IMPORTANT]
> Currently, only the Faceit Data resource is available, and access requires a valid API key.  
> You can obtain your API key by following the instructions in the [official FACEIT documentation](https://docs.faceit.com/getting-started/authentication/api-keys).

### API Key Handling

You can specify your API key directly in the constructor, or let the library automatically load it from your environment (e.g., `.env`, `settings.ini`).  
By default, the key is read from the `FACEIT_API_KEY` variable.  
To use a different variable, pass an instance of `EnvKey` to the constructor:

```py
from faceit import Faceit, EnvKey

data = Faceit.data(EnvKey("API_KEY_FIELD"))
```

> [!NOTE]
> Loading the API key from environment files requires either installing the `[env]` extra or installing [python-decouple](https://github.com/HBNetwork/python-decouple) yourself.

### Minimal Example

```py
from faceit import Faceit, GameID

# Initialize the API client.
# If FACEIT_API_KEY is set in your environment, you can omit the argument.
data = Faceit.data()  # or Faceit.data("YOUR_API_KEY")

# Fetch player information by nickname.
player = data.players.get("s1mple")

# Retrieve all CS2 match history for the player.
# Returns an ItemPage collection (fully-featured iterable).
matches = data.players.all_history(player.id, GameID.CS2)

print(f"Total CS2 matches for {player.nickname}: {len(matches)}")

# Example: Find a match by its ID.
match_id = "1-441ff69f-09e3-4c58-b5c4-a0a7424fe8e0"
some_match = matches.find("id", match_id)

if some_match:
    print(f"Found match with ID {match_id}: {some_match}")
else:
    print(f"No match found with ID {match_id}")
```

### More Examples

See additional usage examples in the [examples/](examples/) directory.

## Motivation

This project was created out of necessity during the development of a product requiring deep integration with the FACEIT platform.
Existing solutions did not offer the level of type safety, convenience, or abstraction needed for robust, maintainable code.
The goal is to provide a solution approaching enterprise-level quality, while remaining accessible and useful for a wide range of users.

## Project Status & Roadmap

> [!WARNING]
> This library is currently in **early development**.  
> Many endpoints, models, and features are not yet implemented.
> Webhooks, chat API, and some advanced features are not available yet.
> Inline code documentation is minimal, and the Sphinx-based documentation site is not yet ready.
> Expect breaking changes and incomplete coverage.  
> **Contributions and feedback are highly welcome!**

### Planned Improvements

- Support for more endpoints and models
- Webhooks and chat API integration
- Complete documentation and usage guides

## Contributing

Contributions, bug reports, and feature requests are welcome!  
Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines before opening an issue or pull request.

---

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
