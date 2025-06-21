/**
 * Dice rolling functionality
 */

class DiceRoller {
    constructor() {
        this.results = [];
        this.resultsElement = document.getElementById('dice-results');
        this.clearButton = null;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Add event listeners for dice buttons
        document.addEventListener('DOMContentLoaded', () => {
            // Quick roll buttons
            const diceButtons = document.querySelectorAll('.dice-button');
            diceButtons.forEach(button => {
                const sides = parseInt(button.textContent.replace('D', ''));
                if (sides) {
                    button.addEventListener('click', () => this.rollDice(sides));
                }
            });

            // Clear button
            this.clearButton = document.querySelector('.dice-clear-button');
            if (this.clearButton) {
                this.clearButton.addEventListener('click', () => this.clearResults());
            }
        });
    }

    rollDice(sides, count = 1) {
        const results = [];
        let total = 0;

        for (let i = 0; i < count; i++) {
            const result = Math.floor(Math.random() * sides) + 1;
            results.push(result);
            total += result;
        }

        const rollData = {
            sides: sides,
            count: count,
            results: results,
            total: total,
            timestamp: new Date()
        };

        this.results.push(rollData);
        this.displayResult(rollData);
        this.showResultsPanel();

        return rollData;
    }

    rollCustom(diceString) {
        // Parse dice strings like "2d6+3", "1d20", "3d8-2"
        const regex = /^(\d+)?d(\d+)([+-]\d+)?$/i;
        const match = diceString.toLowerCase().match(regex);

        if (!match) {
            console.error('Invalid dice string:', diceString);
            return null;
        }

        const count = parseInt(match[1]) || 1;
        const sides = parseInt(match[2]);
        const modifier = parseInt(match[3]) || 0;

        const baseRoll = this.rollDice(sides, count);
        if (modifier !== 0) {
            baseRoll.modifier = modifier;
            baseRoll.finalTotal = baseRoll.total + modifier;
        }

        return baseRoll;
    }

    displayResult(rollData) {
        if (!this.resultsElement) return;

        const resultDiv = createElement('div', 'dice-result-item');
        
        let resultText = '';
        if (rollData.count === 1) {
            resultText = `D${rollData.sides}: ${rollData.results[0]}`;
        } else {
            resultText = `${rollData.count}D${rollData.sides}: [${rollData.results.join(', ')}]`;
        }

        if (rollData.modifier) {
            resultText += ` ${rollData.modifier >= 0 ? '+' : ''}${rollData.modifier}`;
        }

        const totalSpan = createElement('span', 'dice-total');
        totalSpan.textContent = ` = ${rollData.finalTotal || rollData.total}`;

        resultDiv.textContent = resultText;
        resultDiv.appendChild(totalSpan);

        this.resultsElement.appendChild(resultDiv);
        this.updateDiceDisplay();
    }

    clearResults() {
        this.results = [];
        if (this.resultsElement) {
            this.resultsElement.innerHTML = '';
        }
        this.hideResultsPanel();
    }

    showResultsPanel() {
        if (this.resultsElement) {
            this.resultsElement.style.display = 'block';
        }
    }

    hideResultsPanel() {
        if (this.resultsElement) {
            this.resultsElement.style.display = 'none';
        }
    }

    updateDiceDisplay() {
        // Scroll to bottom of dice results
        if (this.resultsElement) {
            scrollToBottom(this.resultsElement);
        }
    }

    // Ability check roller
    rollAbilityCheck(abilityScore, proficient = false, advantage = false, disadvantage = false) {
        const modifier = getModifier(abilityScore);
        const proficiencyBonus = proficient ? 2 : 0; // Simplified - should come from character level
        
        let rolls = [this.rollSingleDie(20)];
        
        if (advantage || disadvantage) {
            rolls.push(this.rollSingleDie(20));
            const selectedRoll = advantage ? Math.max(...rolls) : Math.min(...rolls);
            rolls = [selectedRoll];
        }

        const total = rolls[0] + modifier + proficiencyBonus;
        
        const rollData = {
            type: 'ability_check',
            die: rolls[0],
            modifier: modifier,
            proficiencyBonus: proficiencyBonus,
            total: total,
            advantage: advantage,
            disadvantage: disadvantage,
            timestamp: new Date()
        };

        this.results.push(rollData);
        this.displayAbilityCheck(rollData);
        this.showResultsPanel();

        return rollData;
    }

    rollSingleDie(sides) {
        return Math.floor(Math.random() * sides) + 1;
    }

    displayAbilityCheck(rollData) {
        if (!this.resultsElement) return;

        const resultDiv = createElement('div', 'dice-result-item ability-check');
        
        let resultText = `D20: ${rollData.die}`;
        if (rollData.modifier !== 0) {
            resultText += ` ${rollData.modifier >= 0 ? '+' : ''}${rollData.modifier}`;
        }
        if (rollData.proficiencyBonus > 0) {
            resultText += ` +${rollData.proficiencyBonus} (prof)`;
        }

        if (rollData.advantage) {
            resultText += ' (ADV)';
        } else if (rollData.disadvantage) {
            resultText += ' (DIS)';
        }

        const totalSpan = createElement('span', 'dice-total');
        totalSpan.textContent = ` = ${rollData.total}`;

        resultDiv.textContent = resultText;
        resultDiv.appendChild(totalSpan);

        this.resultsElement.appendChild(resultDiv);
        this.updateDiceDisplay();
    }

    // Get the last roll result
    getLastRoll() {
        return this.results.length > 0 ? this.results[this.results.length - 1] : null;
    }

    // Get all rolls of a specific type
    getRollsOfType(type) {
        return this.results.filter(roll => roll.type === type);
    }

    // Statistical analysis
    getAverage() {
        if (this.results.length === 0) return 0;
        const total = this.results.reduce((sum, roll) => sum + (roll.finalTotal || roll.total), 0);
        return total / this.results.length;
    }

    getTotal() {
        return this.results.reduce((sum, roll) => sum + (roll.finalTotal || roll.total), 0);
    }
}

// Global functions for backward compatibility
let diceRoller;

function initializeDiceRoller() {
    diceRoller = new DiceRoller();
}

function rollDice(sides, count = 1) {
    if (!diceRoller) initializeDiceRoller();
    return diceRoller.rollDice(sides, count);
}

function clearDiceResults() {
    if (!diceRoller) initializeDiceRoller();
    diceRoller.clearResults();
}

function rollCustomDice(diceString) {
    if (!diceRoller) initializeDiceRoller();
    return diceRoller.rollCustom(diceString);
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeDiceRoller);

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        DiceRoller,
        rollDice,
        clearDiceResults,
        rollCustomDice
    };
}