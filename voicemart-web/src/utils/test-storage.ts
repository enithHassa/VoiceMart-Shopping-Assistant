/**
 * Test utility to demonstrate and verify localStorage functionality
 * Run this in the browser console after signup to see stored data
 */

import { getUserData, saveUserData, isAuthenticated, clearUserData } from "../lib/storage";

export function testLocalStorage() {
  console.log("=== Testing VoiceMart LocalStorage ===\n");

  // Test 1: Check if authenticated
  console.log("1. Is Authenticated:", isAuthenticated());

  // Test 2: Get user data
  const user = getUserData();
  if (user) {
    console.log("2. User Data:", user);
    console.log("   - Name:", user.name);
    console.log("   - Email:", user.email);
    console.log("   - Phone:", user.phone || "Not provided");
  } else {
    console.log("2. No user data found in localStorage");
  }

  // Test 3: Check all localStorage keys
  console.log("\n3. All VoiceMart localStorage keys:");
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key?.startsWith("voicemart")) {
      console.log(`   - ${key}:`, localStorage.getItem(key));
    }
  }

  // Test 4: Check Zustand persisted data
  const zustandData = localStorage.getItem("voicemart-auth");
  if (zustandData) {
    console.log("\n4. Zustand Auth Data:", JSON.parse(zustandData));
  }

  console.log("\n=== Test Complete ===\n");
}

// Call this function in the browser console after signup
// Example: window.testStorage() (after importing/exporting)
if (typeof window !== "undefined") {
  (window as any).testStorage = testLocalStorage;
}
