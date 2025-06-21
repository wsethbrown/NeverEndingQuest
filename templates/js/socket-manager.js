/**
 * Socket.IO management for real-time communication
 */

class SocketManager {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        this.statusIndicator = document.getElementById('status-indicator');
        this.statusText = document.getElementById('status-text');
        
        this.eventHandlers = new Map();
        this.messageQueue = [];
        
        this.initialize();
    }

    initialize() {
        if (typeof io !== 'undefined') {
            this.socket = io();
            this.setupEventListeners();
        } else {
            console.error('Socket.IO not loaded');
            this.updateStatus('Socket.IO not available', false);
        }
    }

    setupEventListeners() {
        if (!this.socket) return;

        // Connection events
        this.socket.on('connect', () => {
            this.handleConnect();
        });

        this.socket.on('disconnect', (reason) => {
            this.handleDisconnect(reason);
        });

        this.socket.on('connect_error', (error) => {
            this.handleConnectionError(error);
        });

        this.socket.on('reconnect', (attemptNumber) => {
            console.log(`Reconnected after ${attemptNumber} attempts`);
            this.reconnectAttempts = 0;
        });

        this.socket.on('reconnect_attempt', (attemptNumber) => {
            console.log(`Reconnection attempt ${attemptNumber}`);
            this.updateStatus(`Reconnecting... (${attemptNumber}/${this.maxReconnectAttempts})`, false);
        });

        this.socket.on('reconnect_failed', () => {
            console.log('Failed to reconnect');
            this.updateStatus('Connection failed', false);
        });

        // Game-specific events
        this.socket.on('game_output', (data) => {
            this.emit('game_output', data);
        });

        this.socket.on('debug_output', (data) => {
            this.emit('debug_output', data);
        });

        this.socket.on('character_data', (data) => {
            this.emit('character_data', data);
        });

        this.socket.on('inventory_data', (data) => {
            this.emit('inventory_data', data);
        });

        this.socket.on('location_data', (data) => {
            this.emit('location_data', data);
        });

        this.socket.on('npcs_data', (data) => {
            this.emit('npcs_data', data);
        });

        this.socket.on('spells_data', (data) => {
            this.emit('spells_data', data);
        });

        this.socket.on('error', (error) => {
            console.error('Socket error:', error);
            this.emit('error', error);
        });
    }

    handleConnect() {
        console.log('Connected to server');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.updateStatus('Connected', true);
        
        // Process queued messages
        this.processMessageQueue();
        
        this.emit('connected');
    }

    handleDisconnect(reason) {
        console.log('Disconnected from server:', reason);
        this.isConnected = false;
        this.updateStatus('Disconnected', false);
        
        this.emit('disconnected', reason);

        // Auto-reconnect for certain reasons
        if (reason === 'io server disconnect') {
            // Server initiated disconnect, try to reconnect
            this.socket.connect();
        }
    }

    handleConnectionError(error) {
        console.error('Connection error:', error);
        this.updateStatus('Connection error', false);
        this.emit('connection_error', error);
    }

    updateStatus(text, connected) {
        if (this.statusText) {
            this.statusText.textContent = text;
        }
        
        if (this.statusIndicator) {
            toggleClass(this.statusIndicator, 'connected', connected);
        }
    }

    // Event management
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    off(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${event}:`, error);
                }
            });
        }
    }

    // Message sending
    send(event, data) {
        if (this.isConnected && this.socket) {
            this.socket.emit(event, data);
        } else {
            // Queue message for when connection is restored
            this.messageQueue.push({ event, data, timestamp: Date.now() });
            console.warn(`Queued message: ${event} (not connected)`);
        }
    }

    processMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            
            // Check if message is too old (5 minutes)
            if (Date.now() - message.timestamp > 300000) {
                console.warn('Discarding old queued message:', message.event);
                continue;
            }
            
            this.socket.emit(message.event, message.data);
        }
    }

    // Convenience methods for game actions
    sendUserInput(input) {
        this.send('user_input', { input: input });
    }

    requestCharacterData() {
        this.send('request_character_data');
    }

    requestInventoryData() {
        this.send('request_inventory_data');
    }

    requestLocationData() {
        this.send('request_location_data');
    }

    requestNPCsData() {
        this.send('request_npcs_data');
    }

    requestSpellsData() {
        this.send('request_spells_data');
    }

    startGame() {
        this.send('start_game');
    }

    // Connection management
    connect() {
        if (this.socket && !this.isConnected) {
            this.socket.connect();
        }
    }

    disconnect() {
        if (this.socket && this.isConnected) {
            this.socket.disconnect();
        }
    }

    // Utility methods
    isSocketConnected() {
        return this.isConnected && this.socket && this.socket.connected;
    }

    getConnectionState() {
        return {
            connected: this.isConnected,
            socketConnected: this.socket ? this.socket.connected : false,
            reconnectAttempts: this.reconnectAttempts,
            queuedMessages: this.messageQueue.length
        };
    }
}

// Global socket manager instance
let socketManager;

function initializeSocketManager() {
    socketManager = new SocketManager();
    return socketManager;
}

function getSocketManager() {
    if (!socketManager) {
        initializeSocketManager();
    }
    return socketManager;
}

// Global functions for backward compatibility
function sendInput() {
    const inputField = document.getElementById('user-input');
    if (inputField && inputField.value.trim()) {
        getSocketManager().sendUserInput(inputField.value.trim());
        inputField.value = '';
    }
}

function startGame() {
    getSocketManager().startGame();
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeSocketManager);

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        SocketManager,
        getSocketManager,
        sendInput,
        startGame
    };
}