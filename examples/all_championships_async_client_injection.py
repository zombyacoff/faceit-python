"""
NOTE: This example does not work with the current version (0.1.0) of the
library. Please wait for release 0.1.1 for this feature.

Backport 0.1.1:
Do not use the enum `faceit.MaxConcurrentRequests.ABSOLUTE` — replace it with
the constant `MAX_CONCURRENT_REQUESTS_ABSOLUTE_ABSOLUTE` from `AsyncClient`.

The `max_items` parameter is not available yet, and instead of a list,
the method returns an iterator. To get a list, you need to call
`await championships.collect()`.

Use this at your own risk, as in version 0.1.1 the iterator is not initially
limited, so it may return a very large list.
"""

import asyncio
import faceit


async def main():
    async_client = faceit.http.AsyncClient(
        "YOUR_API_KEY",
        max_concurrent_requests=faceit.MaxConcurrentRequests.ABSOLUTE,
        # Or just "max" (=100). The limit is necessary because higher values
        # may cause serious issues. The default is 30.
    )

    # You can initially pass the client to the `faceit.AsyncFaceit`
    # constructor using the named argument `client`.
    async with faceit.AsyncFaceit(client=async_client) as f:
        championships = await f.resources.championships.all_items(
            faceit.GameID.CS2,
            faceit.EventCategory.ONGOING,
            max_items=100,  # Maximum number of items to retrieve;
            # default is `MaxPages(30)`
            # (i.e., 30 pages * method limit per page = 300 items).
        )
        print(f"Total ongoing CS2 championships: {len(championships)}")


if __name__ == "__main__":
    asyncio.run(main())
