import faceit

with faceit.Faceit("YOUR_API_KEY") as f:
    player = f.resources.players.get("s1mple")
    # Returns an ItemPage collection (fully-featured iterable)
    matches = f.resources.players.all_history(player.id, faceit.GameID.CS2)
    print(f"Total CS2 matches for s1mple: {len(matches)}")
    # Example: find a match by attribute
    some_match = matches.find("id", "some_match_id")
    print(f"First match with the given ID: {some_match or 'No match found'}")
