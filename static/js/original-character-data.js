// Character data display functions from original game_interface.html

// Global variable to store original inventory data for filtering
let originalInventoryData = null;

// Inventory filtering and sorting functions
let currentSearchTerm = '';
let currentFilter = '';
let currentSortedData = null;
let filtersActive = false;
let currentSort = 'name-asc';

// Display inventory data
function displayInventory(data, preserveOriginal = false) {
    const container = document.getElementById('inventory-content');
    if (!data) {
        container.innerHTML = '<div class="loading">No inventory data available</div>';
        return;
    }
    
    // If this is fresh data from server and we have active filters/sort, reapply them
    const hasCustomSort = currentSort !== 'name-asc';
    if (!preserveOriginal && originalInventoryData && (filtersActive || hasCustomSort)) {
        // Store the new original data
        originalInventoryData = data;
        // Reapply current filters
        applyFiltersAndSort();
        return;
    }
    
    // Store original data for filtering only if this is the initial load
    if (!preserveOriginal) {
        originalInventoryData = data;
    }
    
    let html = '<div class="inventory-sheet">';
    if (data.currency) {
        const gold = data.currency.gold || 0;
        const silver = data.currency.silver || 0;
        const copper = data.currency.copper || 0;
        
        html += `<div class="inventory-header"><div class="currency-display"><div class="currency-title">Currency</div><div class="currency-grid"><div class="currency-item"><span class="currency-amount">${gold}</span><span class="currency-type">GP</span></div><div class="currency-item"><span class="currency-amount">${silver}</span><span class="currency-type">SP</span></div><div class="currency-item"><span class="currency-amount">${copper}</span><span class="currency-type">CP</span></div></div></div></div>`;
    }
    
    // Add compact inventory controls between currency and equipment
    html += `<div class="inventory-controls">
        <button class="search-btn" onclick="openSearchPopup()">Search</button>
        <select class="inventory-sort" id="inventory-sort" onchange="sortInventory()">
            <option value="name-asc">Sort: Name A-Z</option>
            <option value="name-desc">Sort: Name Z-A</option>
            <option value="type">Sort: Type</option>
            <option value="quantity">Sort: Quantity</option>
        </select>
        <select class="filter-dropdown" id="filter-dropdown" onchange="changeFilter()">
            <option value="">Filter</option>
            <option value="weapon">Weapons</option>
            <option value="armor">Armor</option>
            <option value="consumable">Consumables</option>
            <option value="magical">Magical</option>
            <option value="equipped">Equipped</option>
        </select>
        <button class="search-btn" onclick="clearAllFilters()">Clear</button>
    </div>`;
    
    // Equipment section - always show
    html += '<div class="equipment-section"><h4>Equipment</h4>';
    if (data.equipment && data.equipment.length > 0) {
        data.equipment.forEach(item => {
            const qty = item.quantity || 1;
            const qtyStr = qty > 1 ? ` ×${qty}` : '';
            const type = (item.item_type || 'misc').toLowerCase();
            const desc = (item.description || '').substr(0, 80);
            html += `<div class="inventory-item" title="${desc}"><span class="feature-bullet">●</span><span class="item-name">${item.item_name}${qtyStr}</span><span class="item-type"> (${type})</span></div>`;
        });
    } else {
        html += '<div class="inventory-item"><span class="feature-bullet">●</span><span class="item-name">No equipment</span></div>';
    }
    html += '</div>';
    
    // Main inventory sections in grid layout
    html += '<div class="inventory-sections">';
    
    // Weapons and attacks
    if (data.attacksAndSpellcasting && data.attacksAndSpellcasting.length > 0) {
        html += '<div class="inventory-section"><h4>Weapons & Attacks</h4>';
        data.attacksAndSpellcasting.forEach(weapon => {
            const damage = weapon.damage || `${weapon.damageDice}+${weapon.damageBonus}`;
            const attack = weapon.attackBonus >= 0 ? `+${weapon.attackBonus}` : weapon.attackBonus;
            const damageInfo = `Damage: ${damage} (${weapon.damageType || 'damage'})`;
            const fullDesc = weapon.description || '';
            html += `<div class="inventory-item" title="${fullDesc}"><div class="item-main"><span class="item-name">${weapon.name}</span><span class="weapon-bonus">${attack}</span></div><div class="item-details"><span class="weapon-damage">${damageInfo}</span></div></div>`;
        });
        html += '</div>';
    }
    
    // Ammunition
    if (data.ammunition && data.ammunition.length > 0) {
        html += '<div class="inventory-section"><h4>Ammunition</h4>';
        data.ammunition.forEach(ammo => {
            const desc = (ammo.description || '');
            html += `<div class="inventory-item" title="${desc}"><div class="item-main"><span class="item-name">${ammo.name}</span><span class="item-qty">×${ammo.quantity}</span></div></div>`;
        });
        html += '</div>';
    }
    
    html += '</div>'; // End inventory-sections
    html += '</div>'; // End inventory-sheet
    container.innerHTML = html;
    
    // Restore dropdown values after HTML regeneration
    const sortDropdown = document.getElementById('inventory-sort');
    const filterDropdown = document.getElementById('filter-dropdown');
    if (sortDropdown && currentSort) {
        sortDropdown.value = currentSort;
    }
    if (filterDropdown && currentFilter) {
        filterDropdown.value = currentFilter;
    }
}

// Display character stats
function displayCharacterStats(data) {
    const container = document.getElementById('stats-content');
    if (!data) {
        container.innerHTML = '<div class="loading">No character data available</div>';
        return;
    }
    
    // Calculate ability modifiers
    function getModifier(score) {
        const mod = Math.floor((score - 10) / 2);
        return mod >= 0 ? `+${mod}` : `${mod}`;
    }
    
    // Calculate HP percentage
    const hpPercent = (data.hitPoints / data.maxHitPoints) * 100;
    
    // Simplified character sheet HTML (the original is very long)
    let html = '<div class="character-sheet-wrapper">';
    html += '<div class="character-sheet">';
    html += `<div class="character-header"><div class="character-name">${data.name || 'Unknown Character'}</div><div class="character-details"><div class="detail-left"><div><span class="orange">Level ${data.level || 1}</span> ${data.race || 'Unknown'} ${data.class || 'Unknown'}</div><div><span class="orange">Background:</span> ${data.background || 'Unknown'} • <span class="orange">Alignment:</span> ${data.alignment || 'Unknown'}</div></div><div class="detail-right"><div><span class="orange">HP:</span> ${data.hitPoints}/${data.maxHitPoints} • <span class="orange">AC:</span> ${data.armorClass || 10}</div><div><span class="orange">Speed:</span> ${data.speed || 30} ft • <span class="orange">Prof:</span> +${data.proficiencyBonus || 2}</div></div></div></div>`;
    
    // Add ability scores if available
    const abilities = data.abilities || data.abilityScores;
    if (abilities) {
        html += '<div class="abilities-row">';
        ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'].forEach(ability => {
            const score = abilities[ability] || abilities[ability.charAt(0).toUpperCase() + ability.slice(1)] || 10;
            const abilityName = ability.charAt(0).toUpperCase() + ability.slice(1);
            html += `<div class="ability-score"><div class="ability-name">${abilityName.substr(0,3)}</div><div class="ability-value">${score}</div><div class="ability-modifier">${getModifier(score)}</div></div>`;
        });
        html += '</div>';
    }
    
    // Add skills and saving throws section
    html += '<div class="skills-saves-container">';
    
    // Saving Throws
    if (data.savingThrows && Array.isArray(data.savingThrows)) {
        html += '<div class="stat-group">';
        html += '<h4>Saving Throws</h4>';
        html += '<div class="stat-group-content">';
        
        ['Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma'].forEach(save => {
            const ability = save.toLowerCase();
            const abilityScore = abilities ? (abilities[ability] || abilities[save] || 10) : 10;
            const modifier = Math.floor((abilityScore - 10) / 2);
            const isProficient = data.savingThrows.includes(save);
            const bonus = modifier + (isProficient ? (data.proficiencyBonus || 2) : 0);
            const profIcon = isProficient ? '●' : '○';
            
            html += `<div class="save-item"><span class="prof-indicator">${profIcon}</span><span class="save-name">${save}</span><span class="save-bonus">${bonus >= 0 ? '+' + bonus : bonus}</span></div>`;
        });
        
        html += '</div></div>';
    }
    
    // Skills
    if (data.skills && Object.keys(data.skills).length > 0) {
        html += '<div class="stat-group">';
        html += '<h4>Skills</h4>';
        html += '<div class="stat-group-content">';
        
        Object.entries(data.skills).forEach(([skillName, bonus]) => {
            html += `<div class="skill-item"><span class="prof-indicator">●</span><span class="skill-name">${skillName}</span><span class="skill-bonus">+${bonus}</span></div>`;
        });
        
        html += '</div></div>';
    }
    
    html += '</div>'; // End skills-saves-container
    
    // Add class features section
    if (data.classFeatures && Array.isArray(data.classFeatures)) {
        html += '<div class="class-features-section">';
        html += '<h4>Class Features</h4>';
        
        data.classFeatures.forEach(feature => {
            let usageInfo = '';
            if (feature.usage) {
                const current = feature.usage.current || 0;
                const max = feature.usage.max || 0;
                if (max > 0) {
                    // Create circular usage indicators
                    const filledCircles = '●'.repeat(current);
                    const emptyCircles = '○'.repeat(max - current);
                    usageInfo = ` <span class="usage-circles">${filledCircles}${emptyCircles}</span>`;
                }
            }
            const desc = (feature.description || '').replace(/"/g, '&quot;');
            
            html += `<div class="feature-item" title="${desc}"><span class="feature-name">${feature.name}</span><span class="feature-usage">${usageInfo}</span></div>`;
        });
        
        html += '</div>';
    }
    
    html += '</div>'; // End character-sheet
    html += '</div>'; // End wrapper
    
    container.innerHTML = html;
}

// Enhanced spells and magic display
function displaySpellsAndMagic(data) {
    const container = document.getElementById('spells-content');
    
    // Check if character has any spellcasting abilities or magic items
    const hasSpellcasting = data && data.spellcasting && 
        (data.spellcasting.spellSaveDC > 0 || 
         (data.spellcasting.spells && Object.values(data.spellcasting.spells).some(spells => Array.isArray(spells) && spells.length > 0)));
    
    const hasMagicItems = data && data.equipment && data.equipment.some(item => item.magical);
    
    if (!hasSpellcasting && !hasMagicItems) {
        container.innerHTML = '<div class="no-spellcasting-message">This character does not have spellcasting abilities.</div>';
        return;
    }
    
    let html = '<div class="spells-magic-sheet">';
    
    // Spellcasting Section
    if (hasSpellcasting) {
        html += '<div class="spellcasting-section">';
        html += '<h3>SPELLCASTING</h3>';
        html += `<div class="spell-stats"><span>Spell Attack: +${data.spellcasting.spellAttackBonus || 0}</span><span>Save DC: ${data.spellcasting.spellSaveDC || 8}</span></div>`;
        
        // Display spells by level
        if (data.spellcasting.spells) {
            const spellLevels = ['cantrips', 'level1', 'level2', 'level3', 'level4', 'level5', 'level6', 'level7', 'level8', 'level9'];
            
            spellLevels.forEach(level => {
                const spells = data.spellcasting.spells[level];
                if (Array.isArray(spells) && spells.length > 0) {
                    // Spell level header
                    let levelName = level === 'cantrips' ? 'CANTRIPS' : `${level.replace('level', '')}${level === 'level1' ? 'st' : level === 'level2' ? 'nd' : level === 'level3' ? 'rd' : 'th'} LEVEL`;
                    
                    // Spell slots display for non-cantrips
                    let slotsDisplay = '';
                    if (level !== 'cantrips' && data.spellcasting.spellSlots && data.spellcasting.spellSlots[level]) {
                        const slots = data.spellcasting.spellSlots[level];
                        const current = slots.current || 0;
                        const max = slots.max || 0;
                        const percentage = max > 0 ? (current / max) * 100 : 0;
                        let slotsClass = 'available';
                        if (current === 0) slotsClass = 'exhausted';
                        else if (percentage <= 50) slotsClass = 'low';
                        
                        // Create circular spell slot indicators
                        const filledSlots = '●'.repeat(current);
                        const emptySlots = '○'.repeat(max - current);
                        slotsDisplay = ` <span class="spell-slots ${slotsClass}"><span class="slot-circles">${filledSlots}${emptySlots}</span> ${current}/${max}</span>`;
                    }
                    
                    html += `<div class="spell-level"><h4>${levelName}${slotsDisplay}</h4><div class="spells-grid">`;
                    
                    // Display spells
                    spells.forEach(spellName => {
                        const isPrepared = data.spellcasting.preparedSpells && data.spellcasting.preparedSpells.includes(spellName);
                        const preparedBadge = isPrepared ? ' <span class="spell-badge prepared">[P]</span>' : '';
                        
                        html += `<div class="spell-item"><span class="spell-name">${spellName}</span>${preparedBadge}</div>`;
                    });
                    
                    html += '</div></div>';
                }
            });
        }
        
        html += '</div>';
    }
    
    // Magic Items Section
    if (hasMagicItems) {
        const magicItems = data.equipment.filter(item => item.magical);
        const scrolls = magicItems.filter(item => item.item_subtype === 'scroll');
        const potions = magicItems.filter(item => item.item_subtype === 'potion');
        const otherMagicItems = magicItems.filter(item => item.item_subtype !== 'scroll' && item.item_subtype !== 'potion');
        
        html += '<div class="magic-items-section">';
        
        // Scrolls
        if (scrolls.length > 0) {
            html += '<h4>SCROLLS</h4><div class="magic-items-grid">';
            scrolls.forEach(item => {
                const levelBadge = item.spellLevel ? ` <span class="spell-level-badge">Level ${item.spellLevel}</span>` : '';
                const quantity = item.quantity > 1 ? ` <span class="item-quantity">[${item.quantity}x]</span>` : '';
                html += `<div class="magic-item"><span class="item-name">${item.item_name}</span>${levelBadge}${quantity}</div>`;
            });
            html += '</div>';
        }
        
        // Potions
        if (potions.length > 0) {
            html += '<h4>POTIONS</h4><div class="magic-items-grid">';
            potions.forEach(item => {
                const quantity = item.quantity > 1 ? ` <span class="item-quantity">[${item.quantity}x]</span>` : '';
                html += `<div class="magic-item"><span class="item-name">${item.item_name}</span>${quantity}</div>`;
            });
            html += '</div>';
        }
        
        // Other Magic Items
        if (otherMagicItems.length > 0) {
            html += '<h4>MAGIC ITEMS</h4><div class="magic-items-grid">';
            otherMagicItems.forEach(item => {
                let chargesDisplay = '';
                if (item.charges) {
                    const current = item.charges.current || 0;
                    const max = item.charges.max || 0;
                    const percentage = max > 0 ? (current / max) * 100 : 0;
                    let chargesClass = 'available';
                    if (current === 0) chargesClass = 'exhausted';
                    else if (percentage <= 50) chargesClass = 'low';
                    
                    chargesDisplay = ` <span class="charges ${chargesClass}">${current}/${max}</span>`;
                }
                html += `<div class="magic-item"><span class="item-name">${item.item_name}</span>${chargesDisplay}</div>`;
            });
            html += '</div>';
        }
        
        html += '</div>';
    }
    
    html += '</div>';
    container.innerHTML = html;
}

function displayNPCs(data) {
    const container = document.getElementById('npcs-content');
    if (!data || data.length === 0) {
        container.innerHTML = '<div class="loading">No NPC data available</div>';
        return;
    }
    
    // Enhanced NPC display with more details
    let html = '';
    data.forEach(npc => {
        const abilities = npc.abilities || npc.abilityScores;
        const getModifier = (score) => {
            const mod = Math.floor((score - 10) / 2);
            return mod >= 0 ? `+${mod}` : `${mod}`;
        };
        
        // Calculate health status for HP bar
        const currentHP = npc.hitPoints || 0;
        const maxHP = npc.maxHitPoints || 1;
        const hpPercent = (currentHP / maxHP) * 100;
        let healthClass = 'healthy';
        if (hpPercent <= 25) healthClass = 'critical';
        else if (hpPercent <= 50) healthClass = 'bloodied';
        else if (hpPercent <= 75) healthClass = 'injured';
        
        // Build buttons based on available data
        let buttonsHTML = '<div class="npc-skills-saves-container">';
        
        // Saving Throws button (if NPC has saving throw data)
        if (npc.savingThrows && Array.isArray(npc.savingThrows) && npc.savingThrows.length > 0) {
            buttonsHTML += '<div class="stat-group"><button class="npc-detail-button" onclick="showNPCSaves(\'' + npc.name + '\')">Saving Throws</button></div>';
        }
        
        // Skills button (if NPC has skills data)
        if (npc.skills && Object.keys(npc.skills).length > 0) {
            buttonsHTML += '<div class="stat-group"><button class="npc-detail-button" onclick="showNPCSkills(\'' + npc.name + '\')">Skills</button></div>';
        }
        
        // Spellcasting button (if NPC has spells)
        if (npc.spellcasting && npc.spellcasting.spells && Object.keys(npc.spellcasting.spells).length > 0) {
            buttonsHTML += '<div class="stat-group"><button class="npc-detail-button" onclick="showNPCSpells(\'' + npc.name + '\')">Spellcasting</button></div>';
        }
        
        // Inventory button (if NPC has equipment)
        if (npc.equipment && Array.isArray(npc.equipment) && npc.equipment.length > 0) {
            buttonsHTML += '<div class="stat-group"><button class="npc-detail-button" onclick="showNPCInventory(\'' + npc.name + '\')">Inventory</button></div>';
        }
        
        buttonsHTML += '</div>';
        
        html += `<div class="npc-character-sheet"><div class="npc-header"><div class="npc-name">${npc.name || 'Unnamed NPC'}</div><div class="npc-details">${npc.race || 'Unknown'} ${npc.class || npc.characterClass || 'Unknown'} • Level ${npc.level || 1} • ${npc.alignment || 'Neutral'}</div></div><div class="npc-abilities"><div class="ability-score npc-combat-stat"><div class="ability-name">HP</div><div class="ability-value">${currentHP}/${maxHP}</div><div class="hp-bar"><div class="hp-fill ${healthClass}" style="width: ${hpPercent}%"></div></div></div><div class="ability-score npc-combat-stat npc-no-circle"><div class="ability-name">AC</div><div class="ability-value">${npc.armorClass || 10}</div></div><div class="ability-score npc-combat-stat npc-no-circle"><div class="ability-name">INIT</div><div class="ability-value">${getModifier(abilities ? (abilities.dexterity || abilities.Dexterity || 10) : 10)}</div></div>${abilities ? `<div class="ability-score"><div class="ability-name">STR</div><div class="ability-value">${abilities.strength || abilities.Strength || 10}</div><div class="ability-modifier">${getModifier(abilities.strength || abilities.Strength || 10)}</div></div><div class="ability-score"><div class="ability-name">DEX</div><div class="ability-value">${abilities.dexterity || abilities.Dexterity || 10}</div><div class="ability-modifier">${getModifier(abilities.dexterity || abilities.Dexterity || 10)}</div></div><div class="ability-score"><div class="ability-name">CON</div><div class="ability-value">${abilities.constitution || abilities.Constitution || 10}</div><div class="ability-modifier">${getModifier(abilities.constitution || abilities.Constitution || 10)}</div></div><div class="ability-score"><div class="ability-name">INT</div><div class="ability-value">${abilities.intelligence || abilities.Intelligence || 10}</div><div class="ability-modifier">${getModifier(abilities.intelligence || abilities.Intelligence || 10)}</div></div><div class="ability-score"><div class="ability-name">WIS</div><div class="ability-value">${abilities.wisdom || abilities.Wisdom || 10}</div><div class="ability-modifier">${getModifier(abilities.wisdom || abilities.Wisdom || 10)}</div></div><div class="ability-score"><div class="ability-name">CHA</div><div class="ability-value">${abilities.charisma || abilities.Charisma || 10}</div><div class="ability-modifier">${getModifier(abilities.charisma || abilities.Charisma || 10)}</div></div>` : ''}</div>${buttonsHTML}</div>`;
    });
    
    container.innerHTML = html;
}

// Socket event handlers for data response
socket.on('player_data_response', (response) => {
    const { dataType, data, error } = response;
    
    if (error) {
        console.error(`Error loading ${dataType}:`, error);
        return;
    }
    
    switch (dataType) {
        case 'inventory':
            displayInventory(data);
            break;
        case 'stats':
            displayCharacterStats(data);
            break;
        case 'spells':
            displaySpellsAndMagic(data);
            break;
        case 'npcs':
            displayNPCs(data);
            break;
    }
});

// Filtering and sorting functions
function applyFiltersAndSort() {
    if (!originalInventoryData) return;
    
    // Start with original data
    let data = JSON.parse(JSON.stringify(originalInventoryData));
    
    // Apply sorting first
    if (data.equipment && currentSort) {
        data.equipment.sort((a, b) => {
            switch (currentSort) {
                case 'name-asc':
                    return a.item_name.localeCompare(b.item_name);
                case 'name-desc':
                    return b.item_name.localeCompare(a.item_name);
                case 'type':
                    return a.item_type.localeCompare(b.item_type) || a.item_name.localeCompare(b.item_name);
                case 'quantity':
                    return (b.quantity || 1) - (a.quantity || 1) || a.item_name.localeCompare(b.item_name);
                default:
                    return 0;
            }
        });
    }
    
    // Store sorted data
    currentSortedData = data;
    
    // Apply filters
    if (data.equipment) {
        data.equipment = data.equipment.filter(item => {
            // Search filter
            const matchesSearch = !currentSearchTerm || 
                item.item_name.toLowerCase().includes(currentSearchTerm) ||
                (item.description && item.description.toLowerCase().includes(currentSearchTerm)) ||
                item.item_type.toLowerCase().includes(currentSearchTerm);
            
            // Type filter
            let matchesFilter = true;
            if (currentFilter) {
                switch (currentFilter) {
                    case 'weapon':
                        matchesFilter = item.item_type === 'weapon';
                        break;
                    case 'armor':
                        matchesFilter = item.item_type === 'armor';
                        break;
                    case 'consumable':
                        matchesFilter = item.item_type === 'consumable' || item.consumable;
                        break;
                    case 'magical':
                        matchesFilter = item.magical;
                        break;
                    case 'equipped':
                        matchesFilter = item.equipped;
                        break;
                }
            }
            
            return matchesSearch && matchesFilter;
        });
    }
    
    // Update display with filtered and sorted data
    displayInventory(data, true);
}

function sortInventory() {
    const sortDropdown = document.getElementById('inventory-sort');
    if (sortDropdown) {
        currentSort = sortDropdown.value;
        filtersActive = true;
        applyFiltersAndSort();
    }
}

function changeFilter() {
    currentFilter = document.getElementById('filter-dropdown').value;
    filtersActive = true;
    applyFiltersAndSort();
}

function openSearchPopup() {
    document.getElementById('search-popup').style.display = 'block';
    document.getElementById('search-popup-input').focus();
}

function closeSearchPopup() {
    document.getElementById('search-popup').style.display = 'none';
}

function performSearch() {
    currentSearchTerm = document.getElementById('search-popup-input').value.toLowerCase();
    filtersActive = true;
    applyFiltersAndSort();
}

function clearAllFilters() {
    currentSearchTerm = '';
    currentFilter = '';
    currentSort = 'name-asc';
    filtersActive = false;
    document.getElementById('search-popup-input').value = '';
    document.getElementById('filter-dropdown').value = '';
    const sortDropdown = document.getElementById('inventory-sort');
    if (sortDropdown) {
        sortDropdown.value = 'name-asc';
    }
    applyFiltersAndSort();
}