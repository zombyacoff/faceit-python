"""
NOTE: This example does not work with the current version `(0.1.0)` of the library.
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
        championships = f.resources.championships.all_items(
            faceit.GameID.CS2, faceit.EventCategory.ONGOING
        )
        print(f"Total ongoing CS2 championships: {len(championships)}")


if __name__ == "__main__":
    asyncio.run(main())
