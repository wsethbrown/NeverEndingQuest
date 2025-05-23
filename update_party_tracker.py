import json
from file_operations import safe_write_json

def update_party_tracker(player_name, player_stats, party_tracker_data):
    if player_stats and party_tracker_data:
        for member in party_tracker_data["party"]:
            if member["name"].lower() == player_name:
                member.update({
                    "characterName": player_stats["characterName"],
                    "playerName": player_stats["playerName"],
                    "race": player_stats["race"],
                    "class": player_stats["class"],
                    "level": player_stats["level"],
                    "background": player_stats["background"],
                    "alignment": player_stats["alignment"],
                    "experiencePoints": player_stats["experiencePoints"],
                    "condition": player_stats["condition"],
                    "abilities": player_stats["abilities"],
                    "equipment": {
                        "armor": player_stats["equipment"]["armor"],
                        "weapons": player_stats["equipment"]["weapons"],
                        "other": player_stats["equipment"]["other"]
                    },
                    "goldPieces": player_stats["goldPieces"],
                    "food": player_stats["food"],
                    "water": player_stats["water"],
                    "featuresAndTraits": player_stats["featuresAndTraits"],
                    "proficiencies": player_stats["proficiencies"],
                    "languages": player_stats["languages"]
                })
                break

    # Save the updated party_tracker.json file with atomic write
    if not safe_write_json("party_tracker.json", party_tracker_data):
        print("ERROR: Failed to save party tracker")
        return None

    return party_tracker_data