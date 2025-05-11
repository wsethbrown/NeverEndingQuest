import json
import random

def print_encounter_details(encounter_data):
    print("Encounter Details:")
    encounter_details = []
    for creature in encounter_data["creatures"]:
        name = creature["name"]
        with open(f"{name.lower().replace(' ', '_')}.json") as char_file:
            char_data = json.load(char_file)
            hp = creature["currentHitPoints"]
            max_hp = creature["maxHitPoints"]
            ac = char_data["armorClass"]
        initiative = creature.get("initiative", "Not yet rolled")
        hp_display = hp if hp > 0 else "Unconscious" if hp == 0 else "Dying"
        creature_details = f"{name}: HP {hp_display}/{max_hp}, AC: {ac}, Initiative: {initiative}"
        print(creature_details)
        encounter_details.append(creature_details)
    return encounter_details

def roll_initiative(filename):
    with open(filename, 'r+') as encounter_file:
        encounter_data = json.load(encounter_file)

        initiative_rolls = []
        for creature in encounter_data["creatures"]:
            with open(f"{creature['name'].lower().replace(' ', '_')}.json") as char_file:
                char_data = json.load(char_file)
                dex_modifier = (char_data["abilities"]["dexterity"] - 10) // 2

            die_roll = random.randint(1, 20)
            initiative_roll = die_roll + dex_modifier
            creature["initiative"] = initiative_roll
            initiative_rolls.append(f"{creature['name']} rolls {die_roll} + {dex_modifier} (DEX) = {initiative_roll} for initiative.")

        # Sort creatures by initiative (highest to lowest)
        encounter_data["creatures"].sort(key=lambda x: x["initiative"], reverse=True)

        # Reset file pointer and write the updated data
        encounter_file.seek(0)
        json.dump(encounter_data, encounter_file, indent=2)
        encounter_file.truncate()

        encounter_data["history"] = []

    return encounter_data

def determine_targets(encounter_data):
    for creature in encounter_data["creatures"]:
        if creature["type"] == "enemy":
            possible_targets = [c for c in encounter_data["creatures"] if c["type"] == "player"]
            creature["target"] = random.choice(possible_targets)["name"] if possible_targets else None

def calculate_hit(attacker_data, defender_data, attack_info):
    """Calculates whether an attack hits and prints details, using new attack_info format."""
    attack_bonus = attack_info["attackBonus"]
    damage_dice = attack_info["damageDice"]
    damage_bonus = attack_info.get("damageBonus", 0)  # Default to 0 if damageBonus not present
    damage_type = attack_info["damageType"]

    attack_roll = random.randint(1, 20)
    attack_total = attack_roll + attack_bonus
    defender_name = defender_data.get("characterName", defender_data.get("name", ""))
    print(f"{attacker_data['name']} attacks {defender_name} with {attack_info['name']}! (Attack roll: {attack_roll} + {attack_bonus} = {attack_total} vs. AC {defender_data['armorClass']})")

    if attack_total >= defender_data["armorClass"]:
        print("Hit!")
        return True, damage_dice, damage_bonus, damage_type, attack_roll, attack_bonus, attack_total
    else:
        print("Miss!")
        return False, None, None, None, attack_roll, attack_bonus, attack_total

def roll_damage(damage_dice, damage_bonus):
    """Rolls damage dice and adds bonus."""
    damage_roll = sum(random.randint(1, int(die)) for die in damage_dice.split("d")) + damage_bonus
    return damage_roll

def handle_encounter(encounter_data, file_path):
    encounter_details = print_encounter_details(encounter_data)
    encounter_data["history"].append({"encounter_details": encounter_details})

    determine_targets(encounter_data)

    for creature in encounter_data["creatures"]:
        with open(creature["characterSheet"], 'r') as char_file:
            char_data = json.load(char_file)
            if creature["type"] == "player":
                hp = char_data["hitPoints"]["current"]
                max_hp = char_data["hitPoints"]["max"]
                ac = char_data["armorClass"]
                attacks = char_data["attacksAndSpellcasting"]
                condition = char_data.get("condition", "")
            else:
                hp = char_data["hitPoints"]
                max_hp = char_data.get("maxHitPoints", hp)
                ac = char_data["armorClass"]
                attacks = char_data.get("specialAbilities", []) + char_data.get("actions", [])
                condition = char_data.get("condition", "")

        creature_actions = [f"{creature['name']}'s turn:"]

        if hp > 0 and creature.get("target") is not None:
            target_creature_data = next((c for c in encounter_data["creatures"] if c["name"] == creature["target"]), None)

            if target_creature_data:
                with open(target_creature_data["characterSheet"], 'r') as target_char_file:
                    target_char_data = json.load(target_char_file)
                    target_ac = target_char_data["armorClass"]

                creature_actions.append(f"{creature['name']}'s target is: {creature['target']}")
                creature_actions.append(f"{creature['name']}'s AC is: {ac}")
                creature_actions.append(f"{creature['name']}'s condition is: {condition}")

                for attack in attacks:
                    is_hit, damage_dice, damage_bonus, damage_type, attack_roll, attack_modifier, attack_total = calculate_hit(creature, target_char_data, attack)

                    creature_actions.append(f"{creature['name']} attacks {target_creature_data['name']} with {attack['name']}. Attack roll: {attack_roll} + {attack_modifier} = {attack_total} vs. AC {target_ac}")

                    if is_hit:
                        damage = roll_damage(damage_dice, damage_bonus)
                        if target_creature_data["type"] == "player":
                            target_char_data["hitPoints"]["current"] -= damage
                            if target_char_data["hitPoints"]["current"] <= 0:
                                target_char_data["condition"] = "Unconscious"
                        else:
                            target_char_data["hitPoints"] -= damage
                            if target_char_data["hitPoints"] <= 0:
                                target_char_data["condition"] = "Dead"

                        creature_actions.append(f"Hit! {target_creature_data['name']} takes {damage} {damage_type} damage. ({target_char_data['hitPoints']['current'] if target_creature_data['type'] == 'player' else target_char_data['hitPoints']}/{max_hp} HP remaining)")

                        # Update the target creature's JSON file
                        with open(target_creature_data["characterSheet"], 'w') as target_char_file:
                            json.dump(target_char_data, target_char_file, indent=2)

                        break  # Stop attacking after a successful hit
                    else:
                        creature_actions.append("Miss!")
            else:
                creature_actions.append(f"No valid target found for {creature['name']}.")
        else:
            creature_actions.append(f"{creature['name']} is unconscious or has no valid target.")

        encounter_data["history"].append(creature_actions)

    # Check if all players are unconscious or dying
    all_players_unconscious = all(
        creature["type"] == "player" and creature.get("hitPoints", {}).get("current", 1) <= 0
        for creature in encounter_data["creatures"]
    )

    if all_players_unconscious:
        encounter_data["history"].append(["All players are unconscious or dying. The encounter ends."])

    # Update the encounter JSON file with the encounter history
    with open(file_path, 'w') as encounter_file:
        json.dump(encounter_data, encounter_file, indent=2)

def run_encounter(file_path):
    encounter_data = roll_initiative(file_path)
    handle_encounter(encounter_data, file_path)