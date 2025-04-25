import faceit

with faceit.Faceit.data("YOUR_API_KEY") as data:
    player = data.players.get("s1mple")
    # Returns an `ItemPage` collection (fully-featured iterable)
    matches = data.players.all_history(player.id, faceit.GameID.CS2)
    print(f"Total CS2 matches for s1mple: {len(matches)}")
    # Example: find a match by attribute
    some_match = matches.find("id", "some_match_id")
    print(f"First match with the given ID: {some_match or 'No match found'}")
