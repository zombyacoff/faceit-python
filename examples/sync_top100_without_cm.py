import faceit

data = faceit.Faceit.data("YOUR_API_KEY")

cs2_rankings = data.raw_rankings.all_unbounded(
    faceit.GameID.CS2,
    faceit.Region.EUROPE,
    # MaxPages (`int`): explicit page count, not item count.
    # Used to separate pages from items in logic.
    # Total items = limit * MaxPages (pages = `math.ceil(max_items / limit)`).
    max_items=faceit.MaxPages(1),  # equivalent to `max_items=100`
)

for place, player in enumerate(cs2_rankings, 1):
    print(
        f"{place} place:\n"
        f"Nickname: {player['nickname']}\n"
        f"Country: {player['country']}\n"
        f"Skill Level: {player['game_skill_level']}\n"
        f"Elo: {player['faceit_elo']}\n"
    )

# If not using a context manager, it's best to explicitly
# close the client after use to avoid resource leaks.
data.client.close()
