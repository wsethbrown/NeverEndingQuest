// Dice Rolling System
class DiceRoller {
    constructor(resultsContainer) {
        this.resultsContainer = resultsContainer;
        this.rollHistory = [];
        this.maxHistory = 100;
    }
    
    roll(diceNotation) {
        try {
            const result = this.parseDiceNotation(diceNotation);
            this.addToHistory(result);
            this.displayResult(result);
            return result;
        } catch (error) {
            console.error('Dice roll error:', error);
            this.displayError(`Error rolling ${diceNotation}: ${error.message}`);
            return null;
        }
    }
    
    parseDiceNotation(notation) {
        // Handle basic dice notation like "1d20", "2d6+3", "1d20+5"
        const match = notation.match(/^(\d+)?d(\d+)([+\-]\d+)?$/i);
        
        if (!match) {
            throw new Error('Invalid dice notation');
        }
        
        const numDice = parseInt(match[1] || '1');
        const dieSize = parseInt(match[2]);
        const modifier = parseInt(match[3] || '0');
        
        if (numDice <= 0 || numDice > 100) {
            throw new Error('Number of dice must be between 1 and 100');
        }
        
        if (dieSize <= 0 || dieSize > 1000) {
            throw new Error('Die size must be between 1 and 1000');
        }
        
        const rolls = [];
        let total = 0;
        
        for (let i = 0; i < numDice; i++) {
            const roll = Utils.randomBetween(1, dieSize);
            rolls.push(roll);
            total += roll;
        }
        
        const finalTotal = total + modifier;
        
        return {
            notation,
            numDice,
            dieSize,
            modifier,
            rolls,
            total,
            finalTotal,
            timestamp: new Date()
        };
    }
    
    addToHistory(result) {
        this.rollHistory.unshift(result);
        if (this.rollHistory.length > this.maxHistory) {
            this.rollHistory = this.rollHistory.slice(0, this.maxHistory);
        }
    }
    
    displayResult(result) {
        if (!this.resultsContainer) return;
        
        const resultElement = Utils.createElement('div', {
            className: 'dice-result'
        });
        
        let resultText = `${result.notation}: `;
        
        if (result.numDice > 1) {
            resultText += `[${result.rolls.join(', ')}]`;
            if (result.modifier !== 0) {
                resultText += ` ${result.modifier >= 0 ? '+' : ''}${result.modifier}`;
            }
            resultText += ` = ${result.finalTotal}`;
        } else {
            resultText += result.rolls[0];
            if (result.modifier !== 0) {
                resultText += ` ${result.modifier >= 0 ? '+' : ''}${result.modifier} = ${result.finalTotal}`;
            }
        }
        
        resultElement.textContent = `[${Utils.formatTimestamp(result.timestamp)}] ${resultText}`;
        
        this.resultsContainer.insertBefore(resultElement, this.resultsContainer.firstChild);
        
        // Limit displayed results
        const results = this.resultsContainer.querySelectorAll('.dice-result');
        if (results.length > 20) {
            results[results.length - 1].remove();
        }
    }
    
    displayError(message) {
        if (!this.resultsContainer) return;
        
        const errorElement = Utils.createElement('div', {
            className: 'dice-result error-message'
        });
        
        errorElement.textContent = `[${Utils.formatTimestamp()}] ${message}`;
        this.resultsContainer.insertBefore(errorElement, this.resultsContainer.firstChild);
    }
    
    clearResults() {
        if (this.resultsContainer) {
            this.resultsContainer.innerHTML = '';
        }
        this.rollHistory = [];
    }
    
    getHistory() {
        return [...this.rollHistory];
    }
    
    getLastRoll() {
        return this.rollHistory.length > 0 ? this.rollHistory[0] : null;
    }
    
    // Predefined common rolls
    rollD20() { return this.roll('1d20'); }
    rollD12() { return this.roll('1d12'); }
    rollD10() { return this.roll('1d10'); }
    rollD8() { return this.roll('1d8'); }
    rollD6() { return this.roll('1d6'); }
    rollD4() { return this.roll('1d4'); }
    rollD100() { return this.roll('1d100'); }
    
    // Advantage/Disadvantage
    rollAdvantage() {
        const roll1 = Utils.randomBetween(1, 20);
        const roll2 = Utils.randomBetween(1, 20);
        const higher = Math.max(roll1, roll2);
        
        const result = {
            notation: '2d20 (Advantage)',
            numDice: 2,
            dieSize: 20,
            modifier: 0,
            rolls: [roll1, roll2],
            total: higher,
            finalTotal: higher,
            timestamp: new Date(),
            special: 'advantage'
        };
        
        this.addToHistory(result);
        this.displayAdvantageResult(result, 'Advantage');
        return result;
    }
    
    rollDisadvantage() {
        const roll1 = Utils.randomBetween(1, 20);
        const roll2 = Utils.randomBetween(1, 20);
        const lower = Math.min(roll1, roll2);
        
        const result = {
            notation: '2d20 (Disadvantage)',
            numDice: 2,
            dieSize: 20,
            modifier: 0,
            rolls: [roll1, roll2],
            total: lower,
            finalTotal: lower,
            timestamp: new Date(),
            special: 'disadvantage'
        };
        
        this.addToHistory(result);
        this.displayAdvantageResult(result, 'Disadvantage');
        return result;
    }
    
    displayAdvantageResult(result, type) {
        if (!this.resultsContainer) return;
        
        const resultElement = Utils.createElement('div', {
            className: 'dice-result'
        });
        
        const resultText = `${type}: [${result.rolls.join(', ')}] = ${result.finalTotal}`;
        resultElement.textContent = `[${Utils.formatTimestamp(result.timestamp)}] ${resultText}`;
        
        this.resultsContainer.insertBefore(resultElement, this.resultsContainer.firstChild);
    }
}