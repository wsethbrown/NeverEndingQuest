// Main Game Interface Controller
class GameInterface {
    constructor() {
        this.socketManager = null;
        this.diceRoller = null;
        this.tabManager = null;
        this.elements = {};
        this.gameState = {
            isWaitingForResponse: false,
            currentModule: null,
            characterData: null
        };
        
        this.init();
    }
    
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }
    
    setup() {
        this.cacheElements();
        this.initializeComponents();
        this.setupEventListeners();
        this.loadSavedState();
    }
    
    cacheElements() {
        this.elements = {
            gameInput: Utils.$('#game-input'),
            sendButton: Utils.$('#send-button'),
            gameMessages: Utils.$('#game-messages'),
            diceResults: Utils.$('#dice-results'),
            startButton: Utils.$('#start-button'),
            tabContainer: Utils.$('.tab-container'),
            locationName: Utils.$('.location-name'),
            locationDetails: Utils.$('.location-details'),
            statusIndicator: Utils.$('.status-indicator')
        };
        
        // Cache dice buttons
        this.elements.diceButtons = {
            d4: Utils.$('#roll-d4'),
            d6: Utils.$('#roll-d6'),
            d8: Utils.$('#roll-d8'),
            d10: Utils.$('#roll-d10'),
            d12: Utils.$('#roll-d12'),
            d20: Utils.$('#roll-d20'),
            d100: Utils.$('#roll-d100'),
            advantage: Utils.$('#roll-advantage'),
            disadvantage: Utils.$('#roll-disadvantage'),
            clear: Utils.$('#clear-dice')
        };
        
        // Cache control buttons
        this.elements.controlButtons = {
            help: Utils.$('#help-button'),
            save: Utils.$('#save-button'),
            load: Utils.$('#load-button'),
            reset: Utils.$('#reset-button')
        };
    }
    
    initializeComponents() {
        // Initialize Socket Manager
        this.socketManager = new SocketManager();
        this.socketManager.on('connect', () => this.onSocketConnect());
        this.socketManager.on('disconnect', () => this.onSocketDisconnect());
        this.socketManager.on('message', (data) => this.onSocketMessage(data));
        this.socketManager.on('error', (error) => this.onSocketError(error));
        this.socketManager.connect();
        
        // Initialize Dice Roller
        this.diceRoller = new DiceRoller(this.elements.diceResults);
        
        // Initialize Tab Manager
        if (this.elements.tabContainer) {
            this.tabManager = new TabManager(this.elements.tabContainer);
            this.tabManager.enableKeyboardNavigation();
        }
    }
    
    setupEventListeners() {
        // Game input handling
        if (this.elements.gameInput) {
            this.elements.gameInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            
            // Auto-resize textarea
            this.elements.gameInput.addEventListener('input', () => {
                this.autoResizeTextarea(this.elements.gameInput);
            });
        }
        
        // Send button
        if (this.elements.sendButton) {
            this.elements.sendButton.addEventListener('click', () => this.sendMessage());
        }
        
        // Start button
        if (this.elements.startButton) {
            this.elements.startButton.addEventListener('click', () => this.startGame());
        }
        
        // Dice buttons
        Object.entries(this.elements.diceButtons).forEach(([key, button]) => {
            if (button) {
                button.addEventListener('click', () => this.handleDiceRoll(key));
            }
        });
        
        // Control buttons
        Object.entries(this.elements.controlButtons).forEach(([key, button]) => {
            if (button) {
                button.addEventListener('click', () => this.handleControlAction(key));
            }
        });
        
        // Tab change events
        if (this.elements.tabContainer) {
            this.elements.tabContainer.addEventListener('tabchange', (e) => {
                this.onTabChange(e.detail.tabId);
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
        
        // Window events
        window.addEventListener('beforeunload', () => this.saveState());
        window.addEventListener('focus', () => this.onWindowFocus());
        window.addEventListener('blur', () => this.onWindowBlur());
    }
    
    sendMessage() {
        if (!this.elements.gameInput || this.gameState.isWaitingForResponse) {
            return;
        }
        
        const message = this.elements.gameInput.value.trim();
        if (!message) {
            return;
        }
        
        // Display user message
        this.addMessage('user', message);
        
        // Clear input
        this.elements.gameInput.value = '';
        this.autoResizeTextarea(this.elements.gameInput);
        
        // Set waiting state
        this.setWaitingState(true);
        
        // Send to server
        this.socketManager.sendMessage(message, (error) => {
            if (error) {
                this.addMessage('error', `Failed to send message: ${error.message}`);
                this.setWaitingState(false);
            }
        });
    }
    
    addMessage(type, content) {
        if (!this.elements.gameMessages) return;
        
        const messageElement = Utils.createElement('div', {
            className: `message ${type}-message`
        });
        
        const timestamp = Utils.formatTimestamp();
        const formattedContent = this.formatMessageContent(content);
        
        messageElement.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${formattedContent}`;
        
        this.elements.gameMessages.appendChild(messageElement);
        this.scrollToBottom();
        
        // Limit message history
        this.limitMessageHistory();
    }
    
    formatMessageContent(content) {
        if (typeof content !== 'string') {
            content = String(content);
        }
        
        // Escape HTML and preserve line breaks
        return Utils.escapeHtml(content).replace(/\n/g, '<br>');
    }
    
    scrollToBottom() {
        if (this.elements.gameMessages) {
            this.elements.gameMessages.scrollTop = this.elements.gameMessages.scrollHeight;
        }
    }
    
    limitMessageHistory(maxMessages = 100) {
        if (!this.elements.gameMessages) return;
        
        const messages = this.elements.gameMessages.querySelectorAll('.message');
        if (messages.length > maxMessages) {
            const toRemove = messages.length - maxMessages;
            for (let i = 0; i < toRemove; i++) {
                messages[i].remove();
            }
        }
    }
    
    setWaitingState(waiting) {
        this.gameState.isWaitingForResponse = waiting;
        
        if (this.elements.sendButton) {
            this.elements.sendButton.disabled = waiting;
            this.elements.sendButton.textContent = waiting ? 'Sending...' : 'Send';
        }
        
        if (this.elements.gameInput) {
            this.elements.gameInput.disabled = waiting;
        }
    }
    
    handleDiceRoll(diceType) {
        if (!this.diceRoller) return;
        
        switch (diceType) {
            case 'd4': this.diceRoller.rollD4(); break;
            case 'd6': this.diceRoller.rollD6(); break;
            case 'd8': this.diceRoller.rollD8(); break;
            case 'd10': this.diceRoller.rollD10(); break;
            case 'd12': this.diceRoller.rollD12(); break;
            case 'd20': this.diceRoller.rollD20(); break;
            case 'd100': this.diceRoller.rollD100(); break;
            case 'advantage': this.diceRoller.rollAdvantage(); break;
            case 'disadvantage': this.diceRoller.rollDisadvantage(); break;
            case 'clear': this.diceRoller.clearResults(); break;
        }
    }
    
    handleControlAction(action) {
        switch (action) {
            case 'help':
                this.showHelp();
                break;
            case 'save':
                this.saveGame();
                break;
            case 'load':
                this.loadGame();
                break;
            case 'reset':
                this.resetGame();
                break;
        }
    }
    
    startGame() {
        this.socketManager.sendMessage('/start', (error) => {
            if (error) {
                this.addMessage('error', `Failed to start game: ${error.message}`);
            }
        });
    }
    
    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
    
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + Enter to send message
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            this.sendMessage();
        }
        
        // Escape to clear input
        if (e.key === 'Escape' && document.activeElement === this.elements.gameInput) {
            this.elements.gameInput.value = '';
            this.autoResizeTextarea(this.elements.gameInput);
        }
    }
    
    // Socket event handlers
    onSocketConnect() {
        this.addMessage('system', 'Connected to server');
    }
    
    onSocketDisconnect() {
        this.addMessage('system', 'Disconnected from server');
        this.setWaitingState(false);
    }
    
    onSocketMessage(data) {
        this.setWaitingState(false);
        
        if (data.response) {
            this.addMessage('assistant', data.response);
        }
        
        if (data.location) {
            this.updateLocationDisplay(data.location);
        }
        
        if (data.character) {
            this.updateCharacterData(data.character);
        }
    }
    
    onSocketError(error) {
        this.addMessage('error', `Connection error: ${error.message}`);
        this.setWaitingState(false);
    }
    
    // UI update methods
    updateLocationDisplay(location) {
        if (this.elements.locationName) {
            this.elements.locationName.textContent = location.name || 'Unknown Location';
        }
        
        if (this.elements.locationDetails) {
            this.elements.locationDetails.textContent = location.details || '';
        }
    }
    
    updateCharacterData(character) {
        this.gameState.characterData = character;
        // Trigger character sheet update if visible
        if (this.tabManager && this.tabManager.getActiveTab() === 'character') {
            this.refreshCharacterSheet();
        }
    }
    
    refreshCharacterSheet() {
        // This would update the character sheet display
        // Implementation depends on character sheet structure
    }
    
    onTabChange(tabId) {
        // Handle tab-specific updates
        switch (tabId) {
            case 'character':
                this.refreshCharacterSheet();
                break;
            case 'inventory':
                this.refreshInventory();
                break;
            case 'spells':
                this.refreshSpells();
                break;
        }
    }
    
    refreshInventory() {
        // Update inventory display
    }
    
    refreshSpells() {
        // Update spells display
    }
    
    // State management
    saveState() {
        const state = {
            gameState: this.gameState,
            diceHistory: this.diceRoller ? this.diceRoller.getHistory() : [],
            activeTab: this.tabManager ? this.tabManager.getActiveTab() : null,
            timestamp: new Date().toISOString()
        };
        
        Utils.storage.set('gameInterface', state);
    }
    
    loadSavedState() {
        const state = Utils.storage.get('gameInterface');
        if (state) {
            this.gameState = { ...this.gameState, ...state.gameState };
            
            if (state.activeTab && this.tabManager) {
                this.tabManager.switchTab(state.activeTab);
            }
        }
    }
    
    // Game actions
    showHelp() {
        const helpText = `
Game Commands:
- Type messages to interact with the game
- Use dice buttons to roll dice
- Press Ctrl+Enter to send messages quickly
- Press Escape to clear input

Available Commands:
- /help - Show this help
- /start - Start or restart the game
- /save - Save current game state
- /load - Load saved game state
- /reset - Reset the game
        `;
        
        this.addMessage('system', helpText.trim());
    }
    
    saveGame() {
        this.socketManager.sendMessage('/save', (error) => {
            if (error) {
                this.addMessage('error', `Failed to save game: ${error.message}`);
            } else {
                this.addMessage('system', 'Game saved successfully');
            }
        });
    }
    
    loadGame() {
        this.socketManager.sendMessage('/load', (error) => {
            if (error) {
                this.addMessage('error', `Failed to load game: ${error.message}`);
            }
        });
    }
    
    resetGame() {
        if (confirm('Are you sure you want to reset the game? This will clear all progress.')) {
            this.socketManager.sendMessage('/reset', (error) => {
                if (error) {
                    this.addMessage('error', `Failed to reset game: ${error.message}`);
                } else {
                    this.elements.gameMessages.innerHTML = '';
                    this.diceRoller.clearResults();
                }
            });
        }
    }
    
    onWindowFocus() {
        // Handle window focus (e.g., check for updates)
    }
    
    onWindowBlur() {
        // Handle window blur (e.g., save state)
        this.saveState();
    }
    
    // Public API
    getDiceRoller() {
        return this.diceRoller;
    }
    
    getSocketManager() {
        return this.socketManager;
    }
    
    getTabManager() {
        return this.tabManager;
    }
    
    getGameState() {
        return { ...this.gameState };
    }
}

// Initialize when DOM is ready
let gameInterface;
document.addEventListener('DOMContentLoaded', () => {
    gameInterface = new GameInterface();
});

// Make available globally for debugging
window.gameInterface = gameInterface;