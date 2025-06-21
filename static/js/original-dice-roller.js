// Dice Rolling Functions from original game_interface.html

let diceRolls = {
    d20: [],
    damage: []
};

function rollDice(sides) {
    // Use crypto.getRandomValues for true randomness
    const array = new Uint32Array(1);
    crypto.getRandomValues(array);
    const result = (array[0] % sides) + 1;
    
    // Store the roll
    if (sides === 20) {
        diceRolls.d20.push(result);
    } else {
        diceRolls.damage.push({sides: sides, result: result});
    }
    
    updateDiceDisplay();
}

function updateDiceDisplay() {
    const resultsDiv = document.getElementById('dice-results');
    let html = '';
    
    // Show d20 rolls
    if (diceRolls.d20.length > 0) {
        html += '<span class="dice-result-item">d20: ' + diceRolls.d20.join(', d20: ') + '</span>';
    }
    
    // Show damage rolls with total
    if (diceRolls.damage.length > 0) {
        const damageStrings = diceRolls.damage.map(roll => `d${roll.sides}: ${roll.result}`);
        const damageTotal = diceRolls.damage.reduce((sum, roll) => sum + roll.result, 0);
        
        if (html) html += ' | ';
        html += '<span class="dice-result-item">' + damageStrings.join(', ') + '</span>';
        html += '<span class="dice-total">Total: ' + damageTotal + '</span>';
    }
    
    if (html) {
        resultsDiv.innerHTML = html;
        resultsDiv.style.display = 'block';
    } else {
        resultsDiv.style.display = 'none';
    }
}

function clearDiceResults() {
    diceRolls.d20 = [];
    diceRolls.damage = [];
    updateDiceDisplay();
}