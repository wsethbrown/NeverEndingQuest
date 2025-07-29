# Warfare System Usage Examples - Mythic Bastionland

This document shows how the AI can use the Warfare system during gameplay when Knights are leading Warbands or participating in large-scale combat.

## When to Use Warfare Rules

The AI should use Warfare rules and the `warfareCombat` action when:

- Knights are leading Warbands (groups of ~24 combatants)
- Conducting sieges against fortifications
- Naval battles with multiple ships
- Large-scale battles between armies
- Knights fighting alongside military units

For individual Knights fighting alone or in small groups, use regular combat rules.

## Example AI Response - Siege Scenario

```json
{
  "narration": "As you approach the castle gates with your militia force, you see the defenders manning the ramparts. The enemy has positioned a unit of mercenaries behind the gate, while skirmishers patrol the walls. Your battering ram team prepares for the assault. How do you wish to proceed with the siege?",
  "actions": [
    {
      "action": "warfareCombat",
      "parameters": {
        "scenarioType": "siege",
        "warbands": [
          {
            "type": "militia",
            "name": "Your Loyal Militia",
            "allegiance": "attacker"
          },
          {
            "type": "mercenaries", 
            "name": "Castle Guard",
            "allegiance": "defender"
          },
          {
            "type": "skirmishers",
            "name": "Wall Archers",
            "allegiance": "defender"
          }
        ],
        "structures": [
          {
            "type": "gate",
            "name": "Castle Gate"
          },
          {
            "type": "rampart",
            "name": "Outer Defenses"
          }
        ],
        "knightLeadership": {
          "Sir Aldric": {
            "warband": "Your Loyal Militia",
            "leadingFromFront": true
          }
        }
      }
    }
  ]
}
```

## Example AI Response - Field Battle

```json
{
  "narration": "The two armies meet on the open field. Your knights charge forward while your mercenaries form a battle line. The enemy riders attempt to flank while their militia holds the center. The clash of steel rings across the battlefield!",
  "actions": [
    {
      "action": "warfareCombat", 
      "parameters": {
        "scenarioType": "battle",
        "warbands": [
          {
            "type": "knights",
            "name": "Royal Heavy Cavalry", 
            "allegiance": "player"
          },
          {
            "type": "mercenaries",
            "name": "Professional Infantry",
            "allegiance": "player" 
          },
          {
            "type": "riders",
            "name": "Enemy Light Cavalry",
            "allegiance": "enemy"
          },
          {
            "type": "militia", 
            "name": "Conscript Spearmen",
            "allegiance": "enemy"
          }
        ],
        "structures": [],
        "knightLeadership": {
          "Lady Brianna": {
            "warband": "Royal Heavy Cavalry",
            "leadingFromFront": true
          },
          "Sir Edmund": {
            "warband": "Professional Infantry", 
            "leadingFromFront": false
          }
        }
      }
    }
  ]
}
```

## Example AI Response - Naval Battle

```json
{
  "narration": "Your longship closes with the enemy warship as waves crash over the bow. Your warband grips their weapons as the ships prepare to collide. The enemy vessel bristles with armed soldiers ready to repel boarders!",
  "actions": [
    {
      "action": "warfareCombat",
      "parameters": {
        "scenarioType": "naval",
        "warbands": [
          {
            "type": "skirmishers",
            "name": "Ship's Crew",
            "allegiance": "player"
          },
          {
            "type": "mercenaries", 
            "name": "Enemy Marines",
            "allegiance": "enemy"
          }
        ],
        "structures": [
          {
            "type": "longship",
            "name": "Your Ship"
          },
          {
            "type": "warship",
            "name": "Enemy Vessel"
          }
        ],
        "knightLeadership": {
          "Captain Gareth": {
            "warband": "Ship's Crew",
            "leadingFromFront": true
          }
        }
      }
    }
  ]
}
```

## Handling Warband Damage and Morale

The AI can represent ongoing battles by including damage and spirit loss:

```json
{
  "narration": "Your militia has taken heavy casualties and their morale is wavering. The mercenaries press their advantage, but your leadership holds the line together.",
  "actions": [
    {
      "action": "warfareCombat",
      "parameters": {
        "scenarioType": "battle",
        "warbands": [
          {
            "type": "militia",
            "name": "Battered Militia",
            "allegiance": "player",
            "damage": 4,
            "spirit_loss": 2
          },
          {
            "type": "mercenaries",
            "name": "Fresh Mercenaries", 
            "allegiance": "enemy"
          }
        ],
        "knightLeadership": {
          "Your Knight": {
            "warband": "Battered Militia",
            "leadingFromFront": true
          }
        }
      }
    }
  ]
}
```

## Key Reminders for AI Usage

1. **Scale Matters**: Only use warfare rules for groups of ~24 combatants
2. **Leadership Roles**: Knights can lead from the front (taking damage) or command safely
3. **Morale is Critical**: Track SPI for broken/routed warbands
4. **Structure Rules**: Castle walls can't be breached conventionally - target the gates!
5. **Glory Opportunities**: Successful warfare leadership provides significant Glory rewards
6. **Individual vs Warband**: Individual Knights vs Warbands get +d12 and Blast damage
7. **Mixed Combat**: Can have both individual combat and warfare in the same scene

## System Response

When the AI uses the `warfareCombat` action, the system will:

- Set up the warfare scenario with all specified warbands and structures
- Handle Knight leadership and "leading from the front" mechanics
- Generate a complete battle report with current status of all units
- Determine if the battle has ended and who won
- Provide Glory potential for Knights based on their leadership roles
- Return all information for the AI to continue narrating the battle

This allows for dynamic, large-scale combat scenarios that follow the official Mythic Bastionland Warfare rules while maintaining the focus on Knight leadership and tactical decision-making.