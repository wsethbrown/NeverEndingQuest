// Socket handling and message display from original game_interface.html

const socket = io();
let connected = false;
let gameStarted = false;

// Auto-scroll to bottom function
function scrollToBottom(elementId) {
    const element = document.getElementById(elementId);
    element.scrollTop = element.scrollHeight;
}

// Format timestamp
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
}

// Add message to output with Tavern AI style
function addMessage(outputId, message) {
    const output = document.getElementById(outputId);
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${message.type}`;
    
    // Handle different message types
    if (message.type === 'narration') {
        // DM message with avatar and header
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        
        const avatarImg = document.createElement('img');
        avatarImg.src = '/static/dm_logo.png';
        avatarImg.alt = 'DM';
        avatar.appendChild(avatarImg);
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const header = document.createElement('div');
        header.className = 'message-header';
        
        const author = document.createElement('span');
        author.className = 'message-author';
        author.textContent = 'Dungeon Master';
        
        const badge = document.createElement('span');
        badge.className = 'message-badge';
        badge.textContent = 'DM';
        
        const text = document.createElement('div');
        text.className = 'message-text';
        text.textContent = message.content;
        
        header.appendChild(author);
        header.appendChild(badge);
        contentDiv.appendChild(header);
        contentDiv.appendChild(text);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        
    } else if (message.type === 'user-input') {
        // Player message with avatar and header
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = '⚔️';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const header = document.createElement('div');
        header.className = 'message-header';
        
        const author = document.createElement('span');
        author.className = 'message-author';
        author.textContent = 'You';
        
        const text = document.createElement('div');
        text.className = 'message-text';
        text.textContent = message.content;
        
        header.appendChild(author);
        contentDiv.appendChild(header);
        contentDiv.appendChild(text);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        
    } else if (message.type === 'system' || message.type === 'error') {
        // System/error messages (centered, no avatar)
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const text = document.createElement('div');
        text.className = 'message-text';
        text.textContent = message.content;
        
        contentDiv.appendChild(text);
        messageDiv.appendChild(contentDiv);
        
    } else if (message.type === 'debug') {
        // Debug messages (simple format for debug panel)
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Add timestamp for debug messages
        if (message.timestamp && outputId === 'debug-output') {
            const timestamp = document.createElement('span');
            timestamp.className = 'timestamp';
            timestamp.textContent = formatTimestamp(message.timestamp);
            contentDiv.appendChild(timestamp);
        }
        
        const text = document.createElement('div');
        text.className = 'message-text';
        text.textContent = message.content;
        
        contentDiv.appendChild(text);
        messageDiv.appendChild(contentDiv);
    }
    
    output.appendChild(messageDiv);
    scrollToBottom(outputId);
}

// Socket event handlers
socket.on('connect', () => {
    connected = true;
    document.getElementById('status-text').textContent = 'Connected';
    document.getElementById('status-indicator').classList.add('connected');
    
    // Load location data and character stats when connected
    loadLocationData();
    loadCharacterStats();
});

socket.on('disconnect', () => {
    connected = false;
    gameStarted = false;
    document.getElementById('status-text').textContent = 'Disconnected';
    document.getElementById('status-indicator').classList.remove('connected');
    document.getElementById('user-input').disabled = true;
    document.getElementById('send-button').disabled = true;
});

socket.on('game_started', (data) => {
    gameStarted = true;
    document.getElementById('start-button').textContent = 'Game Running';
    document.getElementById('start-button').disabled = true;
    document.getElementById('user-input').disabled = false;
    document.getElementById('send-button').disabled = false;
    document.getElementById('user-input').focus();
    
    addMessage('game-output', {
        type: 'system',
        content: 'Game started! You can now enter commands.'
    });
    
    // Refresh location data and character stats when game starts
    loadLocationData();
    loadCharacterStats();
});

socket.on('game_output', (message) => {
    addMessage('game-output', message);
});

socket.on('debug_output', (message) => {
    addMessage('debug-output', message);
});

socket.on('error', (error) => {
    addMessage('game-output', {
        type: 'error',
        content: error.message
    });
});

socket.on('status_update', (data) => {
    const input = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    
    if (data.is_processing) {
        // Show status message and disable input
        input.placeholder = data.message;
        input.disabled = true;
        sendButton.disabled = true;
    } else {
        // Clear status and enable input
        input.placeholder = "Enter your command...";
        input.disabled = false;
        sendButton.disabled = false;
        input.focus();
    }
});

socket.on('location_data_response', (response) => {
    const { data, error } = response;
    
    if (error) {
        console.error('Error loading location data:', error);
        document.getElementById('location-name').textContent = 'Location Unknown';
        document.getElementById('location-details').textContent = '';
        return;
    }
    
    if (data) {
        const locationName = data.currentLocation || 'Unknown Location';
        const locationArea = data.currentArea || '';
        const timeInfo = data.time && data.day && data.month && data.year ? 
            `${data.month} ${data.day}, ${data.year} - ${data.time}` : '';
        
        document.getElementById('location-name').textContent = locationName;
        document.getElementById('location-details').textContent = locationArea + (timeInfo ? ` | ${timeInfo}` : '');
    }
});

// User interaction functions
function startGame() {
    if (connected && !gameStarted) {
        socket.emit('start_game');
    }
}