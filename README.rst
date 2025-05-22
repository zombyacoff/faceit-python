FACEIT Python API Library
=========================

.. image:: https://img.shields.io/badge/python-3.8%2B-3776ab?style=flat-square&labelColor=ffffff&color=2e86c1
    :target: https://www.python.org/
.. image:: https://img.shields.io/pypi/v/faceit?style=flat-square&labelColor=ffffff&color=43a047
    :target: https://pypi.org/project/faceit/

A fully type-safe, high-level Python wrapper for the `FACEIT REST API <https://docs.faceit.com/docs>`_.
Provides a seamless, pythonic interface for working with FACEIT data, featuring both synchronous and asynchronous clients, strict type checking, and robust pagination.

Requirements
------------

- Python 3.8 or higher

Features
--------

- **High-level, idiomatic API** – Interact with FACEIT as if it were a native Python service.
- **Full type safety** – Compatible with `mypy <https://mypy-lang.org/>`_ and other type checkers.
- **Synchronous & asynchronous support** – Powered by `httpx <https://www.python-httpx.org/>`_.
- **Pydantic models** – All data models inherit from `pydantic.Base_Model <https://docs.pydantic.dev/latest/usage/models/>`_.
- **Advanced pagination** – Supports both cursor-based and unix-time-based iterators.
- **Flexible data access** – Choose between raw data and parsed models (e.g., ``.raw_players`` / ``.players``).
- **Page collection utilities** – Paginated responses in model mode are wrapped in an ``ItemPage`` collection with convenient methods: ``.map()``, ``.filter()``, ``.find()``, and more.

Installation
------------

.. code-block:: console

    pip install faceit

Quickstart Example
------------------

Below is a minimal example demonstrating how to retrieve the complete CS2 match history for a player using the synchronous API.

.. important::
   Currently, only the Faceit Data resource is available, and access requires a valid API key.
   You can obtain your API key by following the instructions in the `official FACEIT documentation <https://docs.faceit.com/getting-started/authentication/api-keys>`_.

.. code-block:: python

    import faceit

    with faceit.Faceit.data("YOUR_API_KEY") as data:
        player = data.players.get("s1mple")
        # Returns an `ItemPage` collection (fully-featured iterable)
        matches = data.players.all_history(player.id, faceit.GameID.CS2)
        print(f"Total CS2 matches for s1mple: {len(matches)}")
        # Example: find a match by attribute
        some_match = matches.find("id", "some_match_id")
        print(f"First match with the given ID: {some_match or 'No match found'}")

More Examples
~~~~~~~~~~~~~

See additional usage examples in the ``examples/`` directory.

Motivation
----------

This project was created out of necessity during the development of a product requiring deep integration with the FACEIT platform.
Existing solutions did not offer the level of type safety, convenience, or abstraction needed for robust, maintainable code.
The goal is to provide a solution approaching enterprise-level quality, while remaining accessible and useful for a wide range of users.

Project Status & Roadmap
------------------------

.. warning::
   This library is currently in **early development**.
   Many endpoints, models, and features are not yet implemented.
   Webhooks, chat API, and some advanced features are not available yet.
   Inline code documentation is minimal, and the Sphinx documentation site is not yet ready.
   Expect breaking changes and incomplete coverage.
   **Contributions and feedback are highly welcome!**

Planned Improvements
~~~~~~~~~~~~~~~~~~~~

- Support for more endpoints and models
- Webhooks and chat API integration
- Complete documentation and usage guides

Contributing
------------

Contributions, bug reports, and feature requests are welcome!
Please open an issue or pull request on GitHub.

License
-------

Apache License, Version 2.0 (SPDX: Apache-2.0)  
Copyright © 2025 Alexey Svidersky (zombyacoff)

See the ``LICENSE`` file or https://www.apache.org/licenses/LICENSE-2.0 for details.
