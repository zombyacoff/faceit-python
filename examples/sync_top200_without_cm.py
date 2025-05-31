import faceit

data = faceit.Faceit.data("YOUR_API_KEY")

cs2_rankings = data.raw_rankings.all_unbounded(
    faceit.GameID.CS2,
    faceit.Region.EUROPE,
    # pages (`int`): explicit page count, not item count.
    # Used to separate pages from items in logic.
    # Total items = limit * pages (pages = `math.ceil(max_items / limit)`).
    max_items=faceit.pages(2),  # equivalent to `max_items=200`
)

for player in cs2_rankings:
    print(
        f"{player['position']} place:\n"
        f"Nickname: {player['nickname']}\n"
        f"Country: {player['country']}\n"
        f"Skill Level: {player['game_skill_level']}\n"
        f"Elo: {player['faceit_elo']}\n"
    )
