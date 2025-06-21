/**
 * Utility functions for the game interface
 */

// Utility functions
function scrollToBottom(element) {
    if (element) {
        element.scrollTop = element.scrollHeight;
    }
}

function getModifier(score) {
    return Math.floor((score - 10) / 2);
}

function formatModifier(modifier) {
    return modifier >= 0 ? `+${modifier}` : `${modifier}`;
}

function formatCurrency(amount) {
    return amount.toLocaleString();
}

function formatWeight(weight) {
    return weight.toFixed(1);
}

// Date/time formatting
function formatTimestamp(date) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function getCurrentTimestamp() {
    return formatTimestamp(new Date());
}

// DOM utility functions
function createElement(tag, className, content) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (content) element.textContent = content;
    return element;
}

function toggleClass(element, className, condition) {
    if (condition) {
        element.classList.add(className);
    } else {
        element.classList.remove(className);
    }
}

function showElement(element) {
    element.style.display = 'block';
}

function hideElement(element) {
    element.style.display = 'none';
}

// Debounce function for performance
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Event handling utilities
function addEventListeners(element, events) {
    Object.entries(events).forEach(([event, handler]) => {
        element.addEventListener(event, handler);
    });
}

// Data validation
function isValidNumber(value) {
    return !isNaN(value) && isFinite(value);
}

function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
}

// String utilities
function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

function pluralize(word, count) {
    return count === 1 ? word : `${word}s`;
}

// Array utilities
function removeFromArray(array, item) {
    const index = array.indexOf(item);
    if (index > -1) {
        array.splice(index, 1);
    }
    return array;
}

function groupBy(array, key) {
    return array.reduce((groups, item) => {
        const group = item[key];
        if (!groups[group]) {
            groups[group] = [];
        }
        groups[group].push(item);
        return groups;
    }, {});
}

// Local storage helpers
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
    } catch (error) {
        console.error('Failed to save to localStorage:', error);
    }
}

function loadFromLocalStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.error('Failed to load from localStorage:', error);
        return defaultValue;
    }
}

// Color utilities for HP bars, etc.
function getHealthColor(current, max) {
    const percentage = current / max;
    if (percentage > 0.6) return '#4CAF50'; // Green
    if (percentage > 0.3) return '#ff9800'; // Orange
    return '#f44336'; // Red
}

// Export for module systems (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        scrollToBottom,
        getModifier,
        formatModifier,
        formatCurrency,
        formatWeight,
        formatTimestamp,
        getCurrentTimestamp,
        createElement,
        toggleClass,
        showElement,
        hideElement,
        debounce,
        addEventListeners,
        isValidNumber,
        clamp,
        capitalize,
        pluralize,
        removeFromArray,
        groupBy,
        saveToLocalStorage,
        loadFromLocalStorage,
        getHealthColor
    };
}