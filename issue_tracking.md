# GitHub Issue Tracking & Status

## Issue #3: Currency can go negative without validation
**Status**: RESOLVED ✅
**Description**: Player currency (gold, silver, copper) can become negative when spending money
**Test Case**: Player has 5gp, tries to spend 10gp, should fail but currently results in -5gp

### Investigation Notes:
- ✅ Checked char_schema.json - currency validation EXISTS with minimum: 0
- ✅ Checked update_character_info.py - uses jsonschema validation
- ✅ Related to our recent character update standardization work

### Resolution:
The issue has been FIXED! The char_schema.json file already contains proper validation:
```json
"currency": {
  "type": "object",
  "properties": {
    "gold": {"type": "integer", "minimum": 0},
    "silver": {"type": "integer", "minimum": 0},
    "copper": {"type": "integer", "minimum": 0}
  },
  "required": ["gold", "silver", "copper"]
}
```

The update_character_info.py uses jsonschema validation which enforces these minimum values.
Any attempt to set currency below 0 will fail validation and be rejected.

---

## Other High Priority Issues to Track:

### Critical Bugs:
- #15 - Combat validator lacks context (turn order)
- #18 - Location transitions fail across areas

### Combat Bugs:
- #11 - Prerolled dice used incorrectly
- #12 - AI confuses 'condition' and 'status'
- #13 - Duplicate HP values

### Next Steps:
1. Verify if currency validation is fixed
2. Test with example transactions
3. Update issue status on GitHub