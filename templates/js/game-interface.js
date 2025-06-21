/**
 * Main game interface functionality
 */

// Game state variables
let gameStarted = false;
let currentScale = 0.65; // For character sheet scaling

// Initialize the game interface when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeGameInterface();
});

function initializeGameInterface() {
    // Get socket manager instance
    const socketManager = getSocketManager();
    
    // Set up game-specific socket event handlers
    setupGameSocketHandlers(socketManager);
    
    // Set up UI event handlers
    setupUIHandlers();
    
    // Initialize default tab
    const tabManager = getTabManager();
    if (tabManager.hasTab('stats')) {
        tabManager.switchTab('stats');
    }
}

function setupGameSocketHandlers(socketManager) {
    // Game started event
    socketManager.on('game_started', (data) => {
        gameStarted = true;
        updateGameStartedState();
        
        addMessage('game-output', {
            type: 'system',
            content: 'Game started! You can now enter commands.'
        });
        
        // Load character stats when game starts
        loadCharacterStats();
    });
    
    // Game output
    socketManager.on('game_output', (message) => {
        addMessage('game-output', message);
    });
    
    // Debug output
    socketManager.on('debug_output', (message) => {
        addMessage('debug-output', message);
    });
    
    // Character data
    socketManager.on('character_data', (data) => {
        displayCharacterData(data);
    });
    
    // Inventory data
    socketManager.on('inventory_data', (data) => {
        displayInventoryData(data);
    });
    
    // Location data
    socketManager.on('location_data', (data) => {
        displayLocationData(data);
    });
    
    // NPCs data
    socketManager.on('npcs_data', (data) => {
        displayNPCsData(data);
    });
    
    // Spells data
    socketManager.on('spells_data', (data) => {
        displaySpellsData(data);
    });
    
    // Status update
    socketManager.on('status_update', (data) => {
        updateInputStatus(data);
    });
    
    // Error handling
    socketManager.on('error', (error) => {
        addMessage('game-output', {
            type: 'error',
            content: error.message
        });
    });
    
    // Connection events
    socketManager.on('connected', () => {
        // Load character stats when connected
        loadCharacterStats();
    });
    
    socketManager.on('disconnected', () => {
        gameStarted = false;
        updateGameStartedState();
    });
}

function setupUIHandlers() {
    // Start game button
    const startButton = document.getElementById('start-button');
    if (startButton) {
        startButton.addEventListener('click', startGame);
    }
    
    // Send button
    const sendButton = document.getElementById('send-button');
    if (sendButton) {
        sendButton.addEventListener('click', sendInput);
    }
    
    // Input field
    const userInput = document.getElementById('user-input');
    if (userInput) {
        userInput.addEventListener('keypress', handleKeyPress);
    }
    
    // Tab callbacks
    const tabManager = getTabManager();
    tabManager.onTabActivated('stats', loadCharacterStats);
    tabManager.onTabActivated('inventory', loadInventory);
    tabManager.onTabActivated('spells', loadSpellsAndMagic);
    tabManager.onTabActivated('npcs', loadNPCs);
    // Debug tab doesn't need special loading
}

function updateGameStartedState() {
    const startButton = document.getElementById('start-button');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    
    if (gameStarted) {
        if (startButton) {
            startButton.textContent = 'Game Running';
            startButton.disabled = true;
        }
        if (userInput) {
            userInput.disabled = false;
            userInput.focus();
        }
        if (sendButton) {
            sendButton.disabled = false;
        }
    } else {
        if (startButton) {
            startButton.textContent = 'Start Game';
            startButton.disabled = false;
        }
        if (userInput) {
            userInput.disabled = true;
        }
        if (sendButton) {
            sendButton.disabled = true;
        }
    }
}

function updateInputStatus(data) {
    const input = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    
    if (data.is_processing) {
        // Show status message and disable input
        if (input) {
            input.placeholder = data.message;
            input.disabled = true;
        }
        if (sendButton) {
            sendButton.disabled = true;
        }
    } else {
        // Clear status and enable input
        if (input) {
            input.placeholder = 'Enter your command...';
            input.disabled = false;
            input.focus();
        }
        if (sendButton) {
            sendButton.disabled = false;
        }
    }
}

// Message handling
function addMessage(outputId, message) {
    const output = document.getElementById(outputId);
    if (!output) return;
    
    const messageDiv = createElement('div', `message ${message.type || 'default'}`);
    
    if (message.type === 'narration') {
        // DM message with avatar and header
        const avatar = createElement('div', 'message-avatar');
        const avatarImg = createElement('img');
        avatarImg.src = '/static/dm_logo.png';
        avatarImg.alt = 'DM';
        avatar.appendChild(avatarImg);
        
        const contentDiv = createElement('div', 'message-content');
        const header = createElement('div', 'message-header');
        const author = createElement('span', 'message-author', 'Dungeon Master');
        const badge = createElement('span', 'message-badge', 'DM');
        const text = createElement('div', 'message-text', message.content);
        
        header.appendChild(author);
        header.appendChild(badge);
        contentDiv.appendChild(header);
        contentDiv.appendChild(text);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        
    } else if (message.type === 'user-input') {
        // Player message with avatar and header
        const avatar = createElement('div', 'message-avatar', '⚔️');
        const contentDiv = createElement('div', 'message-content');
        const header = createElement('div', 'message-header');
        const author = createElement('span', 'message-author', 'You');
        const text = createElement('div', 'message-text', message.content);
        
        header.appendChild(author);
        contentDiv.appendChild(header);
        contentDiv.appendChild(text);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        
    } else if (message.type === 'system' || message.type === 'error') {
        // System/error messages (centered, no avatar)
        const contentDiv = createElement('div', 'message-content');
        const text = createElement('div', 'message-text', message.content);
        contentDiv.appendChild(text);
        messageDiv.appendChild(contentDiv);
        
    } else if (message.type === 'debug') {
        // Debug messages (simple format for debug panel)
        const contentDiv = createElement('div', 'message-content');
        
        // Add timestamp for debug messages
        if (message.timestamp && outputId === 'debug-output') {
            const timestamp = createElement('span', 'timestamp', formatTimestamp(message.timestamp));
            contentDiv.appendChild(timestamp);
        }
        
        const text = createElement('div', 'message-text', message.content);
        contentDiv.appendChild(text);
        messageDiv.appendChild(contentDiv);
    }
    
    output.appendChild(messageDiv);
    scrollToBottom(output);
}

// User interaction functions
function startGame() {
    const socketManager = getSocketManager();
    if (socketManager.isSocketConnected() && !gameStarted) {
        socketManager.startGame();
    }
}

function sendInput() {
    const input = document.getElementById('user-input');
    const value = input ? input.value.trim() : '';
    
    if (value && gameStarted) {
        const socketManager = getSocketManager();
        socketManager.sendUserInput(value);
        
        if (input) {
            input.value = '';
            input.focus();
        }
    }
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendInput();
    }
}

// Data loading functions
function loadCharacterStats() {
    const socketManager = getSocketManager();
    socketManager.requestCharacterData();
}

function loadInventory() {
    const socketManager = getSocketManager();
    socketManager.requestInventoryData();
}

function loadSpellsAndMagic() {
    const socketManager = getSocketManager();
    socketManager.requestSpellsData();
}

function loadNPCs() {
    const socketManager = getSocketManager();
    socketManager.requestNPCsData();
}

function loadLocationData() {
    const socketManager = getSocketManager();
    socketManager.requestLocationData();
}

// Data display functions
function displayCharacterData(data) {
    const content = document.getElementById('stats-content');
    if (!content) return;
    
    if (data && data.character_sheet_html) {
        content.innerHTML = `<div class="character-sheet-wrapper" style="transform: scale(${currentScale});">${data.character_sheet_html}</div>`;
    } else {
        content.innerHTML = '<div class="loading">No character data available</div>';
    }
}

function displayInventoryData(data) {
    const content = document.getElementById('inventory-content');
    if (!content) return;
    
    if (data && data.inventory_html) {
        content.innerHTML = data.inventory_html;
        
        // Set up inventory controls if they exist
        setupInventoryControls();
    } else {
        content.innerHTML = '<div class="loading">No inventory data available</div>';
    }
}

function displayLocationData(data) {
    const locationName = document.getElementById('location-name');
    const locationDetails = document.getElementById('location-details');
    
    if (data) {
        if (locationName) {
            locationName.textContent = data.name || 'Unknown Location';
        }
        if (locationDetails) {
            locationDetails.textContent = data.details || '';
        }
    }
}

function displayNPCsData(data) {
    const content = document.getElementById('npcs-content');
    if (!content) return;
    
    if (data && data.npcs_html) {
        content.innerHTML = data.npcs_html;
        
        // Set up NPC interaction handlers
        setupNPCHandlers();
    } else {
        content.innerHTML = '<div class="loading">No NPCs in this area</div>';
    }
}

function displaySpellsData(data) {
    const content = document.getElementById('spells-content');
    if (!content) return;
    
    if (data && data.spells_html) {
        content.innerHTML = data.spells_html;
    } else {
        content.innerHTML = '<div class="loading">No spellcasting data available</div>';
    }
}

// Inventory controls
function setupInventoryControls() {
    // Search functionality
    const searchBtn = document.querySelector('.search-btn');
    if (searchBtn) {
        searchBtn.addEventListener('click', openSearchPopup);
    }
    
    // Sort functionality
    const sortSelect = document.querySelector('.inventory-sort');
    if (sortSelect) {
        sortSelect.addEventListener('change', sortInventory);
    }
    
    // Filter functionality
    const filterSelect = document.querySelector('.filter-dropdown');
    if (filterSelect) {
        filterSelect.addEventListener('change', filterInventory);
    }
}

function openSearchPopup() {
    // Implementation for search popup
    console.log('Search popup not yet implemented');
}

function sortInventory() {
    // Implementation for inventory sorting
    console.log('Inventory sorting not yet implemented');
}

function filterInventory() {
    // Implementation for inventory filtering
    console.log('Inventory filtering not yet implemented');
}

// NPC interaction handlers
function setupNPCHandlers() {
    // Set up NPC detail buttons
    const npcButtons = document.querySelectorAll('.npc-detail-button');
    npcButtons.forEach(button => {
        button.addEventListener('click', function() {
            const npcName = this.dataset.npcName;
            const detailType = this.dataset.detailType;
            showNPCDetails(npcName, detailType);
        });
    });
    
    // Set up modal close handlers
    const modals = document.querySelectorAll('.npc-details-modal, .npc-inventory-modal');
    modals.forEach(modal => {
        const closeBtn = modal.querySelector('.npc-details-close, .npc-inventory-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                modal.style.display = 'none';
            });
        }
        
        // Close on outside click
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.style.display = 'none';
            }
        });
    });
}

function showNPCDetails(npcName, detailType) {
    // Implementation for showing NPC details in modal
    console.log(`Show ${detailType} for ${npcName}`);
}

// Scale adjustment for character sheet
function adjustCharacterSheetScale(scaleFactor) {
    currentScale = Math.max(0.3, Math.min(1.5, currentScale + scaleFactor));
    const wrapper = document.querySelector('.character-sheet-wrapper');
    if (wrapper) {
        wrapper.style.transform = `scale(${currentScale})`;
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + Enter to send input
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        sendInput();
        event.preventDefault();
    }
    
    // Tab switching shortcuts (Alt + number)
    if (event.altKey && event.key >= '1' && event.key <= '5') {
        const tabIndex = parseInt(event.key) - 1;
        const tabs = ['stats', 'inventory', 'spells', 'npcs', 'debug'];
        if (tabs[tabIndex]) {
            const tabManager = getTabManager();
            tabManager.switchTab(tabs[tabIndex]);
        }
        event.preventDefault();
    }
    
    // Character sheet scaling
    if (event.ctrlKey && event.key === '+') {
        adjustCharacterSheetScale(0.1);
        event.preventDefault();
    }
    if (event.ctrlKey && event.key === '-') {
        adjustCharacterSheetScale(-0.1);
        event.preventDefault();
    }
});

// Export functions for global access
window.startGame = startGame;
window.sendInput = sendInput;
window.handleKeyPress = handleKeyPress;
window.loadCharacterStats = loadCharacterStats;
window.loadInventory = loadInventory;
window.loadSpellsAndMagic = loadSpellsAndMagic;
window.loadNPCs = loadNPCs;