# Load Game Dialog UI Improvements Plan

## Current Issues:
1. Save game entries are cramped and hard to read
2. Text wrapping poorly - module names, locations, and descriptions run together
3. Poor spacing and visual hierarchy
4. Information appears as one continuous block of text

## Planned Improvements:

### 1. CSS Enhancements:
- Increase padding and spacing for save items
- Add proper line height for readability
- Create visual separation between different information elements
- Style individual data fields distinctly

### 2. HTML Structure:
- Restructure save item display with proper semantic elements
- Add CSS classes for each data field (date, module, location, etc.)
- Implement better typography hierarchy

### 3. Visual Design:
- Add subtle background variations for selected/hover states
- Use color coding for different information types
- Add icons or visual indicators for save modes
- Improve overall contrast and readability

## Implementation:
Will modify the CSS for `.save-item`, `.save-item-header`, `.save-item-details` and update the JavaScript that generates the HTML structure.