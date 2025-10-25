# Utils Directory

This directory contains utility functions and test helpers for the VoiceMart application.

## Files

### `test-storage.ts`
Provides a test function to verify localStorage functionality. Can be called from the browser console after signup to check stored user data.

**Usage:**
```javascript
// In browser console after signup
testStorage()
```

This will display:
- Authentication status
- User data from localStorage
- All VoiceMart-related localStorage keys
- Zustand persisted auth state
