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
    async with faceit.AsyncFaceit.data(client=async_client) as data:
        championships = await data.championships.all_items(
            faceit.GameID.CS2,
            faceit.EventCategory.ONGOING,
            max_items=250,  # Maximum number of items to retrieve;
            # default is `pages(30)`
            # (i.e., 30 pages * method limit per page (10 in this case) = 300 items).
        )
        print(f"Total ongoing CS2 championships: {len(championships)}")


if __name__ == "__main__":
    asyncio.run(main())
