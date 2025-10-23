import { useState } from "react";

export default function HomePage() {
  const [query, setQuery] = useState("");

  const handleSearch = () => {
    console.log("Searching:", query);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Shop smarter with your voice 🎤</h1>

      {/* Search section */}
      <div className="flex gap-3">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search products or say something..."
          className="flex-1 border rounded-xl px-4 py-3 outline-none focus:ring"
        />
        <button
          onClick={handleSearch}
          className="px-5 py-3 rounded-xl bg-black text-white"
        >
          Search
        </button>
        <button
          className="px-4 py-3 rounded-xl border bg-white"
          title="Voice search (coming soon)"
        >
          🎤
        </button>
      </div>

      {/* Placeholder sections for next steps */}
      <section className="border rounded-xl bg-white p-4">
        <p className="text-gray-500 text-sm">Filters will appear here...</p>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="border rounded-xl bg-white p-4">Amazon</div>
        <div className="border rounded-xl bg-white p-4">eBay</div>
        <div className="border rounded-xl bg-white p-4">Walmart</div>
      </section>
    </div>
  );
}
