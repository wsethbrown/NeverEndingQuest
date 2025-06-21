// UI control functions from original game_interface.html

function sendInput() {
    const input = document.getElementById('user-input');
    const value = input.value.trim();
    
    if (value && connected && gameStarted) {
        socket.emit('user_input', { input: value });
        input.value = '';
        input.focus();
    }
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendInput();
    }
}

// Tab switching function
function switchTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(tab => {
        tab.style.display = 'none';
    });
    
    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab content
    document.getElementById(`${tabName}-tab`).style.display = 'block';
    
    // Add active class to clicked button
    event.target.classList.add('active');
    
    // Load data for the selected tab
    if (tabName === 'inventory') {
        loadInventory();
    } else if (tabName === 'stats') {
        loadCharacterStats();
    } else if (tabName === 'spells') {
        loadSpellsAndMagic();
    } else if (tabName === 'npcs') {
        loadNPCs();
    }
}

// Load player inventory
function loadInventory() {
    socket.emit('request_player_data', { dataType: 'inventory' });
}

// Load character stats
function loadCharacterStats() {
    socket.emit('request_player_data', { dataType: 'stats' });
}

// Load spells and magic items
function loadSpellsAndMagic() {
    socket.emit('request_player_data', { dataType: 'spells' });
}

// Load NPC information
function loadNPCs() {
    socket.emit('request_player_data', { dataType: 'npcs' });
}

// Load current location data
function loadLocationData() {
    socket.emit('request_location_data');
}