# Storage Corruption Investigation Plan

## Goal
Identify the root cause of character data corruption during storage operations, specifically:
- Why currency is deducted before item validation
- How negative currency values are created
- The sequence of operations that leads to partial completion and corruption

## Investigation Steps

1. **Find Storage-Related Files**
   - Look for storage_manager.py and related storage handling files
   - Search for storage processor or transaction handling code
   - Find character update mechanisms

2. **Analyze Transaction Flow**
   - Identify the order of operations in storage transactions
   - Look for currency deduction logic
   - Find item validation checks
   - Understand rollback/error handling

3. **Trace the Bug Pattern**
   - Currency deducted: 2 silver
   - Item validation fails: "Character does not have"
   - Result: Negative currency (-2 silver)
   - Character update fails due to validation

4. **Find the Fix**
   - Ensure item validation happens BEFORE currency deduction
   - Implement proper transaction rollback
   - Add safeguards against negative currency

## Expected Files to Examine
- storage_manager.py
- storage_processor.py
- Character update utilities
- Currency/inventory management code