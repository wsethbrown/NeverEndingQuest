#!/usr/bin/env python3
"""
Create a content-rich Mythic Bastionland realm with detailed:
- Holdings with NPCs, politics, and conflicts
- Myths with full backstories and supernatural elements
- Landmarks with specific features and encounters
- Sites with rich narrative content and challenges
"""

import json
import os
from utils.sites_generator import SiteGenerator
from utils.enhanced_logger import set_script_name, info, debug
from utils.file_operations import safe_write_json

# Set script name for logging
set_script_name("rich_realm_creator")

def create_rich_realm_content():
    """Create a content-rich Mythic Bastionland realm"""
    
    module_name = "The_Bloodmoor_Reaches"
    realm_name = "The Bloodmoor Reaches"
    
    info(f"Creating rich Mythic Bastionland realm: {realm_name}")
    
    # Create module directory structure
    module_dir = f"modules/{module_name}"
    os.makedirs(module_dir, exist_ok=True)
    os.makedirs(f"{module_dir}/sites", exist_ok=True)
    os.makedirs(f"{module_dir}/holdings", exist_ok=True)
    os.makedirs(f"{module_dir}/myths", exist_ok=True)
    
    # Rich Holdings with full details
    holdings_data = {
        "seat_of_power": {
            "name": "Thornspire Keep",
            "location": {"x": 6, "y": 6},
            "type": "seat_of_power",
            "ruler": {
                "name": "Lord Commander Aldric Voss",
                "title": "The Iron Shepherd",
                "description": "A weathered Knight whose left arm was replaced with brass clockwork after a battle with the Crimson Wyrm. Commands absolute loyalty but harbors deep guilt over past failures.",
                "virtues": {"vigour": 12, "clarity": 14, "spirit": 8},
                "guard": 3,
                "glory": 4,
                "passion": "Protecting the innocent at any cost",
                "seer": "The Brass Oracle",
                "abilities": ["Tactical Genius", "Inspiring Presence", "Mechanical Limb (d6 damage)"]
            },
            "population": 800,
            "description": "A massive fortress of black stone crowned with iron spires, Thornspire Keep dominates the central moors. Its walls are scored with ancient runes that pulse with faint crimson light during storms. The keep houses the realm's military command and serves as refuge for displaced villagers.",
            "notable_npcs": [
                {
                    "name": "Captain Mira Blackthorne", 
                    "role": "Guard Captain",
                    "description": "Lord Voss's most trusted lieutenant, a fierce warrior who lost her family to the Weeping Plague. Utterly devoted to the Keep's defense.",
                    "secret": "Secretly corresponds with rebels who oppose the Lord Commander's harsh rule"
                },
                {
                    "name": "Seraph the Chronicler",
                    "role": "Court Scholar", 
                    "description": "An ancient scribe who claims to have witnessed the realm's founding. His memories may hold keys to understanding the myths.",
                    "secret": "Is actually a transformed remnant of the Sunken Court, cursed to remember but never speak the full truth"
                }
            ],
            "conflicts": [
                "Lord Voss's iron-fisted rule breeds resentment among common folk",
                "Strange crimson lights have begun appearing in the Keep's foundations",
                "Food stores are running low due to blighted harvests"
            ],
            "resources": ["Military garrison", "Ancient library", "Smithy", "Granary stores"],
            "defenses": "Massive walls, crossbow batteries, elite guard unit 'The Iron Hawks'"
        },
        "castle": {
            "name": "Greywatch Tower",
            "location": {"x": 2, "y": 9},
            "type": "fortress",
            "ruler": {
                "name": "Dame Elena Greywatch",
                "title": "The Vigilant",
                "description": "A silver-haired Knight who never sleeps, cursed to eternal wakefulness after witnessing the Midnight Convergence. Her eyes glow faintly in darkness.",
                "virtues": {"vigour": 10, "clarity": 16, "spirit": 6},
                "guard": 2,
                "glory": 3,
                "passion": "Watching for threats others cannot see",
                "seer": "The Night Mother",
                "abilities": ["Never Sleeps", "Supernatural Perception", "Command Shadows"]
            },
            "population": 200,
            "description": "A tall, angular tower of grey stone that overlooks the western marshes. No light burns in its windows, yet Dame Elena can be seen pacing the battlements at all hours. Local folk whisper that she sees threats that exist only in her visions.",
            "notable_npcs": [
                {
                    "name": "Brother Marcus the Sleepless",
                    "role": "Tower Chaplain",
                    "description": "A former priest who stays awake to keep Dame Elena company. His faith has grown strange from lack of dreams.",
                    "secret": "Has begun receiving visions from an entity that may not be divine"
                }
            ],
            "conflicts": [
                "Dame Elena's paranoid warnings strain relations with other Holdings",
                "The tower's guards are exhausted from constant vigilance",
                "Strange marsh lights appear to be growing closer to the tower"
            ],
            "mystery": "Dame Elena claims she can see the 'Convergence Points' where reality grows thin"
        },
        "town": {
            "name": "Millhaven",
            "location": {"x": 9, "y": 3},
            "type": "town",
            "ruler": {
                "name": "Mayor Aldwin Toft",
                "title": "The Merchant Prince",
                "description": "A rotund, jovial man who made his fortune in rare wool and exotic spices. His friendly demeanor masks shrewd intelligence and ruthless business practices.",
                "virtues": {"vigour": 8, "clarity": 12, "spirit": 10},
                "guard": 1,
                "glory": 2,
                "passion": "Accumulating wealth and influence",
                "abilities": ["Silver Tongue", "Trade Networks", "Information Broker"]
            },
            "population": 600,
            "description": "A prosperous trading town built around ancient mill wheels that turn without wind or water. The source of their motion is unknown, but they produce the finest flour in the realm. Colorful banners and bustling markets give the town a cheerful appearance.",
            "notable_npcs": [
                {
                    "name": "Vera Millwright",
                    "role": "Mill Keeper",
                    "description": "An elderly woman who tends the mysterious mills. She knows their secret but has never revealed it to anyone.",
                    "secret": "The mills are powered by the dreams of sleeping earth spirits"
                },
                {
                    "name": "Garrett the Bold",
                    "role": "Caravan Guard",
                    "description": "A young Knight who protects merchant caravans. Seeks glory and adventure beyond mere commerce.",
                    "secret": "Is actually a bastard son of Lord Voss, unaware of his heritage"
                }
            ],
            "conflicts": [
                "Merchant rivalries threaten to turn violent",
                "Strange blight affects crops except those near the mills",
                "Caravan routes are increasingly dangerous due to supernatural encounters"
            ],
            "trade_goods": ["Mystical flour", "Rare wool", "Exotic spices", "Merchant information"]
        },
        "fortress": {
            "name": "The Sunward Bastion",
            "location": {"x": 10, "y": 10},
            "type": "fortress",
            "ruler": {
                "name": "Sir Lysander the Golden",
                "title": "Dawn's Champion",
                "description": "A radiant Knight whose armor gleams like captured sunlight. He arrived mysteriously five years ago and built the fortress to 'hold back the darkness.' His past remains unknown.",
                "virtues": {"vigour": 14, "clarity": 10, "spirit": 12},
                "guard": 4,
                "glory": 3,
                "passion": "Bringing light to dark places",
                "seer": "The Solar Oracle",
                "abilities": ["Radiant Armor", "Daylight Sword", "Immunity to Shadow"]
            },
            "population": 150,
            "description": "A gleaming white fortress that seems to glow with inner light. Built on a hill that never knows shadow, even at night. The fortress serves as a beacon visible for miles across the moors.",
            "notable_npcs": [
                {
                    "name": "Sister Aurelia",
                    "role": "Fortress Healer",
                    "description": "A young woman whose touch can heal wounds with warm light. She worships the sun with fervent devotion.",
                    "secret": "Her healing powers are actually draining life from the surrounding land"
                }
            ],
            "conflicts": [
                "Sir Lysander's mysterious past creates distrust",
                "The fortress's light is slowly burning out plant life nearby",
                "Something in the deepest chambers is trying to escape"
            ],
            "mystery": "The fortress was built on the site of an ancient temple to a forgotten sun god"
        }
    }
    
    # Rich Myths with full supernatural elements
    myths_data = {
        "the_crimson_wyrm": {
            "name": "The Crimson Wyrm",
            "location": {"x": 1, "y": 1},
            "hex_number": 1,
            "description": "A massive dragon of living blood that sleeps beneath the northern bogs. When it stirs, the ground bleeds and the waters run red. Local legends say it was bound by the first lords of the realm.",
            "manifestation": "The hex is perpetually shrouded in crimson mist. Plants grow unnaturally large and red. The ground feels warm to the touch and sometimes pulses like a heartbeat.",
            "effects_on_hex": [
                "All water sources run crimson",
                "Plants grow twisted and oversized",
                "Animals avoid the area entirely",
                "The ground occasionally trembles with the Wyrm's breathing"
            ],
            "encounter_table": [
                {"roll": "1-2", "result": "Blood rain falls for d6 hours"},
                {"roll": "3-4", "result": "Crimson flowers whisper secrets in unknown tongues"},
                {"roll": "5-6", "result": "The Wyrm's eye opens briefly, causing temporary madness"}
            ],
            "truth": "The Wyrm is not sleeping but healing from ancient wounds. It will soon awaken.",
            "treasure": "Heart's Blood Ruby - grants visions of the future but ages the bearer",
            "site_hooks": "The Wyrm's lair is a Site of bleeding caverns and pulsing chambers"
        },
        "the_weeping_stones": {
            "name": "The Weeping Stones",
            "location": {"x": 11, "y": 2},
            "hex_number": 2,
            "description": "Seven standing stones that shed constant tears of pure water. The tears heal wounds but cause overwhelming sorrow. The stones are said to be petrified giants who wept for the world's suffering.",
            "manifestation": "Perfect circles of lush grass surround each stone. The sound of sobbing can be heard on the wind. Animals come here to drink but always leave looking melancholy.",
            "effects_on_hex": [
                "Constant sound of weeping on the wind",
                "All water sources have healing properties",
                "Travelers feel unexplained sadness",
                "Plants grow in perfect geometric patterns"
            ],
            "encounter_table": [
                {"roll": "1-2", "result": "A knight from the past appears, seeking absolution"},
                {"roll": "3-4", "result": "The stones share a vision of great tragedy"},
                {"roll": "5-6", "result": "Healing tears flow more freely, creating a temporary spring"}
            ],
            "truth": "The stones contain the essence of noble spirits who sacrificed themselves to save the realm",
            "treasure": "Vial of Giant's Tears - heals any wound but causes the drinker to weep for a full day",
            "site_hooks": "The stone circle is a Site where past and present intersect"
        },
        "the_midnight_court": {
            "name": "The Midnight Court",
            "location": {"x": 1, "y": 11},
            "hex_number": 3,
            "description": "The ruins of an ancient courthouse where trials were held under starlight. On certain nights, phantom judges still convene to try the sins of the living. Their verdicts echo across the moors.",
            "manifestation": "Broken stone benches and a crumbling judge's seat. At midnight, ghostly figures appear to hold court. The hex is always cold, even in summer.",
            "effects_on_hex": [
                "Temperature drops significantly at night",
                "Sounds of gavel strikes echo in the darkness",
                "Guilty consciences are supernaturally amplified",
                "Justice symbols appear burned into trees and stones"
            ],
            "encounter_table": [
                {"roll": "1-2", "result": "Phantom judges demand the party stand trial"},
                {"roll": "3-4", "result": "Echoes reveal a hidden crime in the party's past"},
                {"roll": "5-6", "result": "A ghostly bailiff serves supernatural summons"}
            ],
            "truth": "The court was destroyed when corrupt judges made a pact with dark powers",
            "treasure": "Gavel of Truth - compels honesty but may shatter if used too often",
            "site_hooks": "The courthouse ruins form a Site where justice and corruption battle eternally"
        },
        "the_singing_bog": {
            "name": "The Singing Bog",
            "location": {"x": 10, "y": 11},
            "hex_number": 4,
            "description": "A vast wetland where the wind through the reeds creates hauntingly beautiful music. The songs tell stories of lost love and forgotten glory. Those who listen too long become entranced and may never leave.",
            "manifestation": "Ethereal music fills the air constantly. Will-o'-wisps dance between the reeds. The water reflects not the sky, but scenes from the past.",
            "effects_on_hex": [
                "Constant, beautiful music from unknown sources",
                "Reflections in water show historical events",
                "Travelers must resist being charmed by the songs",
                "Time moves differently - visitors may lose hours or days"
            ],
            "encounter_table": [
                {"roll": "1-2", "result": "The bog sings a prophetic ballad about the party's future"},
                {"roll": "3-4", "result": "Enchanted musicians from the past perform a concert"},
                {"roll": "5-6", "result": "The party member with highest Spirit must resist joining the eternal chorus"}
            ],
            "truth": "The bog is the resting place of a legendary bard whose music transcended death",
            "treasure": "Reed Pipes of Memory - play songs that reveal the past of any location",
            "site_hooks": "The bog's heart is a Site of floating islands connected by music"
        },
        "the_bone_garden": {
            "name": "The Bone Garden",
            "location": {"x": 5, "y": 1},
            "hex_number": 5,
            "description": "A field where white bone-flowers bloom from ancient burial grounds. The flowers sing lullabies in voices of the dead. Harvesting them grants knowledge but also attracts the attention of restless spirits.",
            "manifestation": "Flowers that look like delicate bones swaying in unfelt breezes. Soft whispers in the air. The ground is soft with centuries of burials.",
            "effects_on_hex": [
                "Bone-white flowers that sing in dead voices",
                "Whispers provide ancient knowledge to listeners",
                "Disturbing the flowers awakens angry spirits",
                "The dead can be spoken with more easily here"
            ],
            "encounter_table": [
                {"roll": "1-2", "result": "A helpful ghost offers cryptic advice"},
                {"roll": "3-4", "result": "Bone flowers reveal the location of hidden treasure"},
                {"roll": "5-6", "result": "Ancient warriors rise to test the party's worth"}
            ],
            "truth": "This was the final battlefield where the realm's founders defeated an undead army",
            "treasure": "Crown of Bone Flowers - allows communication with any dead spirit",
            "site_hooks": "The garden's center contains a Site leading to the realm of the dead"
        },
        "the_sunken_crown": {
            "name": "The Sunken Crown",
            "location": {"x": 8, "y": 4},
            "hex_number": 6,
            "description": "A massive golden crown half-buried in a lake, visible beneath the crystal-clear water. It belonged to the realm's first king, who cast it away in shame. The crown's light illuminates the lake bottom, revealing drowned treasures.",
            "manifestation": "A lake of perfect clarity with a golden glow from the depths. Fish swim in formation around the crown. The water never freezes or grows murky.",
            "effects_on_hex": [
                "Lake water glows with golden light at night",
                "Fish behave with supernatural intelligence", 
                "Those who gaze into the water see visions of kingship",
                "The crown occasionally rises closer to the surface"
            ],
            "encounter_table": [
                {"roll": "1-2", "result": "The ghost of the first king appears, seeking redemption"},
                {"roll": "3-4", "result": "Touching the water grants visions of the realm's true history"},
                {"roll": "5-6", "result": "The crown calls to someone with royal blood in the party"}
            ],
            "truth": "The king threw away the crown after learning it was forged through a terrible sacrifice",
            "treasure": "The Crown itself - grants royal authority but curses the wearer with impossible choices",
            "site_hooks": "The lake floor is a Site of drowned palaces and sleeping guardians"
        }
    }
    
    # Create Sites with rich content
    site_gen = SiteGenerator()
    sites_created = []
    
    # Site 1: Thornspire Keep (Seat of Power)
    site_data = site_gen.generate_site("The Inner Sanctum of Thornspire Keep", "fortress")
    # Enhance with specific content
    enhanced_site = enhance_site_with_content(site_data, {
        "theme": "Political intrigue and ancient mysteries within the realm's seat of power",
        "point_descriptions": {
            "feature_1": "Lord Voss's war room with tactical maps showing disturbing patterns",
            "feature_2": "The Brass Oracle's chamber where mechanical prophecies tick and whir", 
            "feature_3": "Ancient throne room with crimson runes pulsing in the walls",
            "danger_1": "Trapped corridors protecting the Keep's darkest secrets",
            "danger_2": "The possessed armory where weapons move on their own",
            "treasure": "The Crown Vault containing regalia that may control the realm's myths"
        },
        "npcs": ["Lord Commander Aldric Voss", "The Brass Oracle", "Captain Mira Blackthorne"],
        "secrets": ["The Keep is built on a Myth site", "Lord Voss made a pact with mechanical entities"]
    })
    
    safe_write_json(enhanced_site, f"{module_dir}/sites/site_001_thornspire_sanctum.json")
    sites_created.append({"name": "Thornspire Keep Sanctum", "file": "site_001_thornspire_sanctum.json"})
    
    # Site 2: The Crimson Wyrm's Lair
    site_gen = SiteGenerator()  # Reset
    site_data = site_gen.generate_site("The Bleeding Caverns of the Crimson Wyrm", "tomb")
    enhanced_site = enhance_site_with_content(site_data, {
        "theme": "Ancient dragon's lair where blood magic and primal power converge",
        "point_descriptions": {
            "feature_1": "Cavern of Crimson Pools where dragon's blood creates visions",
            "feature_2": "Hall of Blood Memory containing the Wyrm's ancient knowledge",
            "feature_3": "The Binding Chamber where the first lords imprisoned the beast",
            "danger_1": "Arteries of living blood that defend the lair",
            "danger_2": "The Wyrm's dreaming mind that attacks intruders psychically",
            "treasure": "The Heart's Blood Ruby and the Wyrm's scale armor"
        },
        "environment": "Pulsing walls, blood-warm air, and the distant sound of a massive heartbeat",
        "threats": ["Blood elementals", "Crimson madness", "The Wyrm's awakening"]
    })
    
    safe_write_json(enhanced_site, f"{module_dir}/sites/site_002_crimson_wyrm_lair.json")
    sites_created.append({"name": "Crimson Wyrm's Lair", "file": "site_002_crimson_wyrm_lair.json"})
    
    # Site 3: The Midnight Court Ruins
    site_gen = SiteGenerator()  # Reset
    site_data = site_gen.generate_site("The Phantom Courthouse of Midnight Justice", "tomb")
    enhanced_site = enhance_site_with_content(site_data, {
        "theme": "Spectral courthouse where justice and corruption wage eternal battle",
        "point_descriptions": {
            "feature_1": "The Gallery of Witnesses where past victims give testimony",
            "feature_2": "The Law Library containing tomes that write themselves",
            "feature_3": "The Sentencing Chamber where verdicts echo through time",
            "danger_1": "The Jury of the Damned who judge visitors harshly",
            "danger_2": "Corruption Incarnate that seeks to pervert justice",
            "treasure": "The Gavel of Truth and the Scales of Absolute Justice"
        },
        "supernatural": "Ghostly judges, phantom evidence, and spectral punishments",
        "moral_challenges": ["Past crimes judged", "Corruption tempting visitors", "Justice demanding sacrifice"]
    })
    
    safe_write_json(enhanced_site, f"{module_dir}/sites/site_003_midnight_court.json")
    sites_created.append({"name": "Midnight Court Ruins", "file": "site_003_midnight_court.json"})
    
    # Create the main module file
    module_metadata = {
        "moduleName": "The Bloodmoor Reaches",
        "moduleDescription": "A dark and mystical realm where ancient powers stir beneath the moors, and the line between legend and reality grows ever thinner. Knights must navigate political intrigue, supernatural mysteries, and the weight of terrible choices.",
        "moduleMetadata": {
            "author": "Mythic Bastionland Rich Content Demo",
            "version": "1.0.0", 
            "gloryRange": {"min": 0, "max": 5},
            "estimatedPlayTime": "8-12 sessions",
            "moduleType": "realm_exploration",
            "system": "Mythic Bastionland",
            "themes": ["Political intrigue", "Supernatural horror", "Moral choices", "Ancient mysteries"]
        },
        "realm": {
            "name": realm_name,
            "description": "A windswept realm of dark moors and ancient secrets, where four Holdings struggle against both political discord and supernatural threats. Strange lights dance in the marshes, ancient powers stir beneath the earth, and the past refuses to stay buried.",
            "atmosphere": "Gothic fantasy with themes of sacrifice, redemption, and the price of power",
            "structure": "12x12 hex map with detailed Holdings, rich Myths, and meaningful Landmarks"
        },
        "holdings": {
            "total": 4,
            "detailed": "Each holding has rich NPCs, political conflicts, and connections to the realm's mysteries",
            "list": list(holdings_data.keys())
        },
        "myths": {
            "total": 6,
            "detailed": "Each myth has supernatural manifestations, encounter tables, and hidden truths",
            "list": [myth["name"] for myth in myths_data.values()]
        },
        "sites": {
            "total": len(sites_created),
            "method": "7-point hex with rich narrative content and meaningful choices",
            "list": [site["name"] for site in sites_created]
        },
        "campaign_hooks": [
            "Lord Voss requests the party investigate strange omens affecting the realm",
            "The party inherits a mysterious map pointing to one of the Myth locations",
            "A dying messenger brings word that 'the old pacts are breaking' and begs for aid",
            "The party arrives as refugees from another realm, seeking shelter and purpose"
        ]
    }
    
    # Save all the rich content
    safe_write_json(holdings_data, f"{module_dir}/holdings_detailed.json")
    safe_write_json(myths_data, f"{module_dir}/myths_detailed.json") 
    safe_write_json(module_metadata, f"{module_dir}/bloodmoor_reaches_module.json")
    
    # Create adventure structure
    adventure_structure = {
        "title": "Echoes of the Bloodmoor",
        "acts": [
            {
                "name": "Act I: Gathering Storms",
                "description": "Knights arrive in the realm and discover the growing supernatural threats",
                "goals": ["Meet the rulers of each Holding", "Investigate initial supernatural incidents", "Choose which factions to support"],
                "locations": ["All 4 Holdings", "1-2 Myth sites", "Several Landmarks"]
            },
            {
                "name": "Act II: Deepening Mysteries", 
                "description": "The true scope of the supernatural crisis becomes clear",
                "goals": ["Explore Sites in detail", "Uncover the truth behind the Myths", "Navigate political consequences"],
                "locations": ["All 3 Sites", "Remaining Myth locations", "Key Landmarks"]
            },
            {
                "name": "Act III: The Choice of Crowns",
                "description": "Knights must make crucial decisions about the realm's future",
                "goals": ["Confront the source of the supernatural threats", "Resolve political conflicts", "Decide the fate of ancient powers"],
                "climax": "The Sunken Crown calls for a new ruler, but claiming it requires terrible sacrifice"
            }
        ],
        "major_npcs": [npc for holding in holdings_data.values() for npc in [holding["ruler"]] + holding.get("notable_npcs", [])],
        "recurring_themes": ["The price of power", "Justice vs. mercy", "Past sins coming to light", "Sacrifice for the greater good"]
    }
    
    safe_write_json(adventure_structure, f"{module_dir}/adventure_structure.json")
    
    print(f"\n🎉 Rich Mythic Bastionland Realm Created!")
    print(f"📍 Realm: {realm_name}")
    print(f"🏰 Holdings: 4 detailed locations with rich NPCs and conflicts")
    print(f"📜 Myths: 6 supernatural sites with full manifestations and secrets")
    print(f"🎯 Sites: {len(sites_created)} detailed exploration areas")
    print(f"📖 Content: Political intrigue, supernatural horror, moral choices")
    print(f"🎮 Ready for multi-session campaign play!")
    print(f"\n📂 All files in: modules/{module_name}/")
    
    return module_dir

def enhance_site_with_content(base_site, enhancement_data):
    """Add rich narrative content to a base site"""
    enhanced = base_site.copy()
    enhanced["narrative_theme"] = enhancement_data.get("theme", "")
    enhanced["atmosphere"] = enhancement_data.get("environment", "")
    enhanced["key_npcs"] = enhancement_data.get("npcs", [])
    enhanced["secrets"] = enhancement_data.get("secrets", [])
    enhanced["threats"] = enhancement_data.get("threats", [])
    
    # Enhance point descriptions
    point_descriptions = enhancement_data.get("point_descriptions", {})
    for point_id, point_data in enhanced["points"].items():
        if point_data["type"] == "feature" and "feature_1" in point_descriptions:
            point_data["description"] = point_descriptions.pop("feature_1")
        elif point_data["type"] == "feature" and "feature_2" in point_descriptions:
            point_data["description"] = point_descriptions.pop("feature_2") 
        elif point_data["type"] == "feature" and "feature_3" in point_descriptions:
            point_data["description"] = point_descriptions.pop("feature_3")
        elif point_data["type"] == "danger" and "danger_1" in point_descriptions:
            point_data["description"] = point_descriptions.pop("danger_1")
        elif point_data["type"] == "danger" and "danger_2" in point_descriptions:
            point_data["description"] = point_descriptions.pop("danger_2")
        elif point_data["type"] == "treasure":
            point_data["description"] = point_descriptions.get("treasure", point_data["description"])
    
    return enhanced

if __name__ == "__main__":
    create_rich_realm_content()