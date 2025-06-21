/**
 * Tab management functionality
 */

class TabManager {
    constructor(tabContainer) {
        this.container = tabContainer || document.querySelector('.tabs');
        this.activeTab = null;
        this.tabs = new Map();
        this.callbacks = new Map();
        
        this.initialize();
    }

    initialize() {
        if (!this.container) {
            console.error('Tab container not found');
            return;
        }

        // Find all tab buttons and content
        const tabButtons = this.container.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            const tabId = this.getTabIdFromButton(button);
            if (tabId) {
                this.registerTab(tabId, button);
            }
        });

        // Set initial active tab
        this.setInitialActiveTab();
    }

    getTabIdFromButton(button) {
        // Extract tab ID from onclick attribute or data attribute
        const onclick = button.getAttribute('onclick');
        if (onclick) {
            const match = onclick.match(/switchTab\(['"]([^'"]+)['"]\)/);
            return match ? match[1] : null;
        }
        
        return button.dataset.tab || null;
    }

    registerTab(tabId, button) {
        const contentElement = document.getElementById(`${tabId}-tab`);
        if (!contentElement) {
            console.warn(`Tab content not found for: ${tabId}-tab`);
            return;
        }

        this.tabs.set(tabId, {
            button: button,
            content: contentElement,
            id: tabId
        });

        // Add click event listener
        button.addEventListener('click', (e) => {
            e.preventDefault();
            this.switchTab(tabId);
        });

        // Remove inline onclick if present
        button.removeAttribute('onclick');
    }

    switchTab(tabId) {
        const tab = this.tabs.get(tabId);
        if (!tab) {
            console.error(`Tab not found: ${tabId}`);
            return;
        }

        // Hide all tabs
        this.tabs.forEach((tabData, id) => {
            tabData.button.classList.remove('active');
            tabData.content.style.display = 'none';
            tabData.content.classList.remove('active');
        });

        // Show selected tab
        tab.button.classList.add('active');
        tab.content.style.display = 'block';
        tab.content.classList.add('active');

        this.activeTab = tabId;

        // Execute callback if registered
        if (this.callbacks.has(tabId)) {
            try {
                this.callbacks.get(tabId)();
            } catch (error) {
                console.error(`Error in tab callback for ${tabId}:`, error);
            }
        }

        // Trigger custom event
        const event = new CustomEvent('tabChanged', {
            detail: { tabId: tabId, tab: tab }
        });
        document.dispatchEvent(event);

        console.log(`Switched to tab: ${tabId}`);
    }

    setInitialActiveTab() {
        // Look for tab marked as active, or default to first tab
        let initialTab = null;

        this.tabs.forEach((tabData, id) => {
            if (tabData.button.classList.contains('active')) {
                initialTab = id;
            }
        });

        if (!initialTab && this.tabs.size > 0) {
            initialTab = this.tabs.keys().next().value;
        }

        if (initialTab) {
            this.switchTab(initialTab);
        }
    }

    // Register a callback for when a specific tab is activated
    onTabActivated(tabId, callback) {
        this.callbacks.set(tabId, callback);
    }

    // Remove callback for a tab
    offTabActivated(tabId) {
        this.callbacks.delete(tabId);
    }

    // Get active tab ID
    getActiveTab() {
        return this.activeTab;
    }

    // Check if tab exists
    hasTab(tabId) {
        return this.tabs.has(tabId);
    }

    // Add a new tab dynamically
    addTab(tabId, buttonElement, contentElement) {
        if (this.tabs.has(tabId)) {
            console.warn(`Tab already exists: ${tabId}`);
            return;
        }

        this.tabs.set(tabId, {
            button: buttonElement,
            content: contentElement,
            id: tabId
        });

        // Add click event listener
        buttonElement.addEventListener('click', (e) => {
            e.preventDefault();
            this.switchTab(tabId);
        });

        console.log(`Added tab: ${tabId}`);
    }

    // Remove a tab
    removeTab(tabId) {
        const tab = this.tabs.get(tabId);
        if (!tab) {
            console.warn(`Tab not found: ${tabId}`);
            return;
        }

        // If it's the active tab, switch to another tab first
        if (this.activeTab === tabId) {
            const remainingTabs = Array.from(this.tabs.keys()).filter(id => id !== tabId);
            if (remainingTabs.length > 0) {
                this.switchTab(remainingTabs[0]);
            } else {
                this.activeTab = null;
            }
        }

        // Remove from DOM
        tab.button.remove();
        tab.content.remove();

        // Remove from registry
        this.tabs.delete(tabId);
        this.callbacks.delete(tabId);

        console.log(`Removed tab: ${tabId}`);
    }

    // Enable/disable a tab
    setTabEnabled(tabId, enabled) {
        const tab = this.tabs.get(tabId);
        if (!tab) {
            console.warn(`Tab not found: ${tabId}`);
            return;
        }

        if (enabled) {
            tab.button.removeAttribute('disabled');
            tab.button.classList.remove('disabled');
        } else {
            tab.button.setAttribute('disabled', 'true');
            tab.button.classList.add('disabled');
            
            // If it's the active tab, switch to another enabled tab
            if (this.activeTab === tabId) {
                const enabledTabs = Array.from(this.tabs.values())
                    .filter(t => !t.button.disabled)
                    .map(t => t.id);
                
                if (enabledTabs.length > 0) {
                    this.switchTab(enabledTabs[0]);
                }
            }
        }
    }

    // Update tab content
    updateTabContent(tabId, content) {
        const tab = this.tabs.get(tabId);
        if (!tab) {
            console.warn(`Tab not found: ${tabId}`);
            return;
        }

        if (typeof content === 'string') {
            tab.content.innerHTML = content;
        } else if (content instanceof Element) {
            tab.content.innerHTML = '';
            tab.content.appendChild(content);
        }
    }

    // Set tab badge (notification indicator)
    setTabBadge(tabId, badge) {
        const tab = this.tabs.get(tabId);
        if (!tab) {
            console.warn(`Tab not found: ${tabId}`);
            return;
        }

        // Remove existing badge
        const existingBadge = tab.button.querySelector('.tab-badge');
        if (existingBadge) {
            existingBadge.remove();
        }

        // Add new badge if provided
        if (badge) {
            const badgeElement = createElement('span', 'tab-badge', badge);
            tab.button.appendChild(badgeElement);
        }
    }
}

// Global tab manager instance
let tabManager;

function initializeTabManager() {
    tabManager = new TabManager();
    return tabManager;
}

function getTabManager() {
    if (!tabManager) {
        initializeTabManager();
    }
    return tabManager;
}

// Global function for backward compatibility
function switchTab(tabId) {
    getTabManager().switchTab(tabId);
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeTabManager);

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        TabManager,
        getTabManager,
        switchTab
    };
}