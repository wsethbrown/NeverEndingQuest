// WebSocket Connection Manager
class SocketManager {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.messageQueue = [];
        this.callbacks = {
            connect: [],
            disconnect: [],
            message: [],
            error: []
        };
    }
    
    connect() {
        try {
            this.socket = io();
            this.setupEventListeners();
        } catch (error) {
            console.error('Socket connection error:', error);
            this.triggerCallback('error', error);
        }
    }
    
    setupEventListeners() {
        if (!this.socket) return;
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus(true);
            this.processMessageQueue();
            this.triggerCallback('connect');
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.isConnected = false;
            this.updateConnectionStatus(false);
            this.triggerCallback('disconnect');
            this.attemptReconnect();
        });
        
        this.socket.on('response', (data) => {
            console.log('Received response:', data);
            this.triggerCallback('message', data);
        });
        
        this.socket.on('error', (error) => {
            console.error('Socket error:', error);
            this.triggerCallback('error', error);
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('Connection error:', error);
            this.isConnected = false;
            this.updateConnectionStatus(false);
            this.triggerCallback('error', error);
        });
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                if (!this.isConnected) {
                    this.connect();
                }
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('Max reconnection attempts reached');
        }
    }
    
    sendMessage(message, callback) {
        const messageData = {
            message: message,
            timestamp: new Date().toISOString()
        };
        
        if (this.isConnected && this.socket) {
            try {
                this.socket.emit('message', messageData);
                if (callback) callback(null, messageData);
            } catch (error) {
                console.error('Send message error:', error);
                if (callback) callback(error);
            }
        } else {
            // Queue message for when connection is restored
            this.messageQueue.push({ messageData, callback });
            console.log('Message queued (not connected)');
        }
    }
    
    processMessageQueue() {
        while (this.messageQueue.length > 0 && this.isConnected) {
            const { messageData, callback } = this.messageQueue.shift();
            try {
                this.socket.emit('message', messageData);
                if (callback) callback(null, messageData);
            } catch (error) {
                console.error('Queued message send error:', error);
                if (callback) callback(error);
            }
        }
    }
    
    updateConnectionStatus(connected) {
        const indicators = Utils.$$('.status-indicator');
        indicators.forEach(indicator => {
            if (connected) {
                indicator.classList.remove('disconnected');
                indicator.classList.add('connected');
            } else {
                indicator.classList.remove('connected');
                indicator.classList.add('disconnected');
            }
        });
        
        // Update any status text
        const statusTexts = Utils.$$('.connection-status');
        statusTexts.forEach(text => {
            text.textContent = connected ? 'Connected' : 'Disconnected';
        });
    }
    
    on(event, callback) {
        if (this.callbacks[event]) {
            this.callbacks[event].push(callback);
        }
    }
    
    off(event, callback) {
        if (this.callbacks[event]) {
            const index = this.callbacks[event].indexOf(callback);
            if (index > -1) {
                this.callbacks[event].splice(index, 1);
            }
        }
    }
    
    triggerCallback(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Callback error for ${event}:`, error);
                }
            });
        }
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        this.isConnected = false;
        this.updateConnectionStatus(false);
    }
    
    getConnectionState() {
        return {
            isConnected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            queuedMessages: this.messageQueue.length
        };
    }
    
    clearMessageQueue() {
        this.messageQueue = [];
    }
}