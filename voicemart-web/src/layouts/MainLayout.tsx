import { Outlet, Link } from "react-router-dom";

export default function MainLayout() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50 text-gray-900">
      {/* Header */}
      <header className="h-16 flex items-center justify-between px-6 border-b bg-white">
        <Link to="/" className="text-xl font-semibold">
          VoiceMart
        </Link>
        <nav className="flex gap-4 text-sm text-gray-600">
          <Link to="/" className="hover:text-black">
            Home
          </Link>
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
