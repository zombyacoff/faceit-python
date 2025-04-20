import asyncio
import faceit


async def main():
    # Create an asynchronous Faceit client with a concurrency limit for HTTP requests.
    # `max_concurrent_requests` controls how many HTTP requests can be sent at the same time.
    async with faceit.AsyncFaceit(
        "YOUR_API_KEY",
        max_concurrent_requests=faceit.AsyncFaceit.MAX_CONCURRENT_REQUESTS,
    ) as f:
        # Get an async iterator for all ongoing CS2 championships (paginated).
        championships = f.resources.championships.all_items(
            faceit.GameID.CS2, faceit.EventCategory.ONGOING
        )
        # Collect all items from the iterator into a list.
        items = await championships.collect()
        print(f"Total ongoing CS2 championships: {len(items)}")


if __name__ == "__main__":
    asyncio.run(main())
