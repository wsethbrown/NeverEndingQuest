// Tab Management System
class TabManager {
    constructor(tabContainer) {
        this.tabContainer = tabContainer;
        this.tabs = new Map();
        this.activeTab = null;
        this.init();
    }
    
    init() {
        if (!this.tabContainer) {
            console.error('Tab container not found');
            return;
        }
        
        // Find all tab buttons and content panels
        const tabButtons = this.tabContainer.querySelectorAll('.tab-button');
        const tabContents = this.tabContainer.querySelectorAll('.tab-content');
        
        // Set up tabs
        tabButtons.forEach((button, index) => {
            const tabId = button.dataset.tab || `tab-${index}`;
            const content = tabContents[index] || null;
            
            this.tabs.set(tabId, {
                button,
                content,
                index
            });
            
            // Add click event listener
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(tabId);
            });
        });
        
        // Activate the first tab by default
        if (this.tabs.size > 0) {
            const firstTabId = this.tabs.keys().next().value;
            this.switchTab(firstTabId);
        }
    }
    
    switchTab(tabId) {
        if (!this.tabs.has(tabId)) {
            console.error(`Tab ${tabId} not found`);
            return false;
        }
        
        // Deactivate current tab
        if (this.activeTab) {
            const currentTab = this.tabs.get(this.activeTab);
            if (currentTab) {
                currentTab.button.classList.remove('active');
                if (currentTab.content) {
                    currentTab.content.classList.remove('active');
                }
            }
        }
        
        // Activate new tab
        const newTab = this.tabs.get(tabId);
        newTab.button.classList.add('active');
        if (newTab.content) {
            newTab.content.classList.add('active');
        }
        
        this.activeTab = tabId;
        
        // Trigger custom event
        this.triggerTabChange(tabId);
        
        return true;
    }
    
    addTab(tabId, buttonElement, contentElement) {
        if (this.tabs.has(tabId)) {
            console.warn(`Tab ${tabId} already exists`);
            return false;
        }
        
        const index = this.tabs.size;
        
        this.tabs.set(tabId, {
            button: buttonElement,
            content: contentElement,
            index
        });
        
        // Add click event listener
        buttonElement.addEventListener('click', (e) => {
            e.preventDefault();
            this.switchTab(tabId);
        });
        
        return true;
    }
    
    removeTab(tabId) {
        if (!this.tabs.has(tabId)) {
            console.error(`Tab ${tabId} not found`);
            return false;
        }
        
        const tab = this.tabs.get(tabId);
        
        // Remove elements from DOM if they exist
        if (tab.button && tab.button.parentNode) {
            tab.button.parentNode.removeChild(tab.button);
        }
        if (tab.content && tab.content.parentNode) {
            tab.content.parentNode.removeChild(tab.content);
        }
        
        // Remove from tabs map
        this.tabs.delete(tabId);
        
        // If this was the active tab, switch to another
        if (this.activeTab === tabId) {
            this.activeTab = null;
            if (this.tabs.size > 0) {
                const firstTabId = this.tabs.keys().next().value;
                this.switchTab(firstTabId);
            }
        }
        
        return true;
    }
    
    getActiveTab() {
        return this.activeTab;
    }
    
    getTab(tabId) {
        return this.tabs.get(tabId) || null;
    }
    
    getAllTabs() {
        return Array.from(this.tabs.keys());
    }
    
    enableTab(tabId) {
        const tab = this.tabs.get(tabId);
        if (tab && tab.button) {
            tab.button.removeAttribute('disabled');
            tab.button.classList.remove('disabled');
        }
    }
    
    disableTab(tabId) {
        const tab = this.tabs.get(tabId);
        if (tab && tab.button) {
            tab.button.setAttribute('disabled', 'true');
            tab.button.classList.add('disabled');
            
            // If this is the active tab, switch to another
            if (this.activeTab === tabId) {
                const enabledTabs = this.getAllTabs().filter(id => {
                    const t = this.tabs.get(id);
                    return t && !t.button.hasAttribute('disabled');
                });
                
                if (enabledTabs.length > 0) {
                    this.switchTab(enabledTabs[0]);
                }
            }
        }
    }
    
    updateTabContent(tabId, content) {
        const tab = this.tabs.get(tabId);
        if (tab && tab.content) {
            if (typeof content === 'string') {
                tab.content.innerHTML = content;
            } else if (content instanceof HTMLElement) {
                tab.content.innerHTML = '';
                tab.content.appendChild(content);
            }
        }
    }
    
    updateTabTitle(tabId, title) {
        const tab = this.tabs.get(tabId);
        if (tab && tab.button) {
            tab.button.textContent = title;
        }
    }
    
    triggerTabChange(tabId) {
        const event = new CustomEvent('tabchange', {
            detail: {
                tabId,
                previousTab: this.activeTab !== tabId ? this.activeTab : null
            }
        });
        
        this.tabContainer.dispatchEvent(event);
    }
    
    // Keyboard navigation
    enableKeyboardNavigation() {
        this.tabContainer.addEventListener('keydown', (e) => {
            const activeElement = document.activeElement;
            
            if (!activeElement.classList.contains('tab-button')) {
                return;
            }
            
            const currentTabId = activeElement.dataset.tab;
            const tabIds = this.getAllTabs();
            const currentIndex = tabIds.indexOf(currentTabId);
            
            let newIndex = currentIndex;
            
            switch (e.key) {
                case 'ArrowLeft':
                case 'ArrowUp':
                    e.preventDefault();
                    newIndex = currentIndex > 0 ? currentIndex - 1 : tabIds.length - 1;
                    break;
                case 'ArrowRight':
                case 'ArrowDown':
                    e.preventDefault();
                    newIndex = currentIndex < tabIds.length - 1 ? currentIndex + 1 : 0;
                    break;
                case 'Home':
                    e.preventDefault();
                    newIndex = 0;
                    break;
                case 'End':
                    e.preventDefault();
                    newIndex = tabIds.length - 1;
                    break;
                case 'Enter':
                case ' ':
                    e.preventDefault();
                    this.switchTab(currentTabId);
                    return;
            }
            
            if (newIndex !== currentIndex) {
                const newTabId = tabIds[newIndex];
                const newTab = this.tabs.get(newTabId);
                if (newTab && newTab.button && !newTab.button.hasAttribute('disabled')) {
                    newTab.button.focus();
                    this.switchTab(newTabId);
                }
            }
        });
    }
}