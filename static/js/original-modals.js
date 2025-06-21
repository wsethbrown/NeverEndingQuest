// Modal functions from original game_interface.html

// NPC Details Modal functions
function showNPCDetails(npcName) {
    // Request detailed NPC data
    socket.emit('request_npc_details', { npcName: npcName });
}

// NPC Saving Throws Modal function
function showNPCSaves(npcName) {
    // Request NPC saving throws data
    socket.emit('request_npc_saves', { npcName: npcName });
}

// NPC Skills Modal function  
function showNPCSkills(npcName) {
    // Request NPC skills data
    socket.emit('request_npc_skills', { npcName: npcName });
}

// NPC Spellcasting Modal function
function showNPCSpells(npcName) {
    // Request NPC spellcasting data
    socket.emit('request_npc_spells', { npcName: npcName });
}

function closeNPCDetails() {
    document.getElementById('npc-details-modal').style.display = 'none';
}

// NPC Inventory Modal functions
function showNPCInventory(npcName) {
    // Request NPC inventory data
    socket.emit('request_npc_inventory', { npcName: npcName });
}

function closeNPCInventory() {
    document.getElementById('npc-inventory-modal').style.display = 'none';
}

// Socket event handlers for modal data
socket.on('npc_details_response', (response) => {
    const { npcName, data, error, modalType } = response;
    
    if (error) {
        console.error(`Error loading NPC details for ${npcName}:`, error);
        return;
    }
    
    let title = `${npcName} - Details`;
    let html = '';
    
    if (modalType === 'skills' && data.skills) {
        title = `${npcName} - Skills`;
        html += '<h4>Skills</h4>';
        Object.entries(data.skills).forEach(([skill, bonus]) => {
            html += `<div class="npc-details-item"><span class="npc-details-name">${skill}</span><span class="npc-details-bonus">+${bonus}</span></div>`;
        });
    } else if (modalType === 'saves' && data.savingThrows) {
        title = `${npcName} - Saving Throws`;
        html += '<h4>Saving Throws</h4>';
        const abilities = data.abilities || {};
        ['Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma'].forEach(save => {
            const ability = save.toLowerCase();
            const abilityScore = abilities[ability] || abilities[save] || 10;
            const modifier = Math.floor((abilityScore - 10) / 2);
            const isProficient = data.savingThrows.includes(save);
            const bonus = modifier + (isProficient ? (data.proficiencyBonus || 2) : 0);
            const profIcon = isProficient ? '●' : '○';
            
            html += `<div class="npc-details-item"><span class="prof-indicator">${profIcon}</span><span class="npc-details-name">${save}</span><span class="npc-details-bonus">${bonus >= 0 ? '+' + bonus : bonus}</span></div>`;
        });
    } else if (modalType === 'spells' && data.spellcasting) {
        title = `${npcName} - Spellcasting`;
        const spellcasting = data.spellcasting;
        html += `<h4>Spellcasting</h4><div class="spell-info"><strong>Spell Save DC:</strong> ${spellcasting.spellSaveDC || 8}<br><strong>Spell Attack Bonus:</strong> +${spellcasting.spellAttackBonus || 0}</div>`;
        
        if (spellcasting.spells) {
            Object.entries(spellcasting.spells).forEach(([level, spells]) => {
                if (Array.isArray(spells) && spells.length > 0) {
                    const levelName = level === 'cantrips' ? 'Cantrips' : `Level ${level.replace('level', '')}`;
                    const slots = spellcasting.spellSlots && spellcasting.spellSlots[level] ? 
                        ` (${spellcasting.spellSlots[level].current}/${spellcasting.spellSlots[level].max} slots)` : '';
                    html += `<h5>${levelName}${slots}</h5>`;
                    spells.forEach(spell => {
                        html += `<div class="spell-item">${spell}</div>`;
                    });
                }
            });
        }
    } else {
        // Default details view
        if (data.skills) {
            html += '<h4>Skills</h4>';
            Object.entries(data.skills).forEach(([skill, bonus]) => {
                html += `<div class="npc-details-item"><span class="npc-details-name">${skill}</span><span class="npc-details-bonus">+${bonus}</span></div>`;
            });
        }
        
        if (data.savingThrows) {
            html += '<h4>Saving Throws</h4>';
            data.savingThrows.forEach(save => {
                html += `<div class="npc-details-item"><span class="npc-details-name">${save}</span><span class="npc-details-bonus">Proficient</span></div>`;
            });
        }
    }
    
    document.getElementById('npc-details-title').textContent = title;
    document.getElementById('npc-details-body').innerHTML = html;
    document.getElementById('npc-details-modal').style.display = 'block';
});

socket.on('npc_inventory_response', (response) => {
    const { npcName, data, error } = response;
    
    if (error) {
        console.error(`Error loading NPC inventory for ${npcName}:`, error);
        return;
    }
    
    // Display NPC inventory in modal
    document.getElementById('npc-inventory-title').textContent = `${npcName} - Inventory`;
    
    let html = '';
    if (data && data.length > 0) {
        data.forEach(item => {
            html += `<div class="npc-inventory-item">
                <div class="npc-inventory-item-header">
                    <span class="npc-inventory-item-name">${item.item_name || item.name || 'Unknown Item'}</span>
                    <span class="npc-inventory-item-quantity">×${item.quantity || 1}</span>
                </div>
                <div class="npc-inventory-item-details">${item.item_type || item.type || 'Item'}</div>
                <div class="npc-inventory-item-description">${item.description || ''}</div>
            </div>`;
        });
    } else {
        html = '<div class="loading">No inventory items found</div>';
    }
    
    document.getElementById('npc-inventory-body').innerHTML = html;
    document.getElementById('npc-inventory-modal').style.display = 'block';
});

// Close modal when clicking outside of it
window.onclick = function(event) {
    const inventoryModal = document.getElementById('npc-inventory-modal');
    const detailsModal = document.getElementById('npc-details-modal');
    const searchPopup = document.getElementById('search-popup');
    
    if (event.target === inventoryModal) {
        closeNPCInventory();
    }
    if (event.target === detailsModal) {
        closeNPCDetails();
    }
    if (event.target === searchPopup) {
        closeSearchPopup();
    }
};

// Handle escape key for search popup
window.onkeydown = function(event) {
    if (event.key === 'Escape') {
        const searchPopup = document.getElementById('search-popup');
        if (searchPopup && searchPopup.style.display === 'block') {
            closeSearchPopup();
        }
    }
};