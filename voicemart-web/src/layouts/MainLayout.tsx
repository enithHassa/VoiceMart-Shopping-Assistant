import { Outlet, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { useAuthStore } from "../lib/auth-store";
import { getUserData, isAuthenticated } from "../lib/storage";

export default function MainLayout() {
  const [userName, setUserName] = useState<string | null>(null);
  const { user, logout, isAuthenticated: isAuth } = useAuthStore();

  useEffect(() => {
    // Check if user is authenticated and get user data
    const userData = getUserData();
    if (userData) {
      setUserName(userData.name);
    } else if (user) {
      // Fallback to Zustand store
      setUserName(user.name);
    }
  }, [user]);

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 text-gray-900">
      {/* Header */}
      <header className="h-16 flex items-center justify-between px-6 border-b bg-white">
        <Link to="/" className="text-xl font-semibold">
          VoiceMart
        </Link>
        <nav className="flex gap-4 text-sm text-gray-600 items-center">
          <Link to="/" className="hover:text-black">
            Home
          </Link>
          {userName || isAuth ? (
            <>
              <span className="text-indigo-600 font-medium">👋 {userName}</span>
              <button
                onClick={() => {
                  logout();
                  setUserName(null);
                  localStorage.clear();
                }}
                className="hover:text-red-600 transition-colors"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="hover:text-black">
                Login
              </Link>
              <Link to="/signup" className="hover:text-black">
                Sign Up
              </Link>
            </>
          )}
          <a
            href="https://github.com"
            target="_blank"
            className="hover:text-black"
            rel="noreferrer"
          >
            GitHub
          </a>
        </nav>
      </header>

      {/* Page content */}
      <main className="flex-1 max-w-7xl mx-auto w-full p-6">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="h-14 flex items-center justify-center text-sm text-gray-500 border-t bg-white">
        © {new Date().getFullYear()} VoiceMart
      </footer>
    </div>
  );
}
