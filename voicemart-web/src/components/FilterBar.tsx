type Props = {
  brand: string;
  setBrand: (v: string) => void;
  minPrice: string;
  setMinPrice: (v: string) => void;
  maxPrice: string;
  setMaxPrice: (v: string) => void;
  sources: Record<string, boolean>;
  toggleSource: (s: string) => void;
  onApply: () => void;
};

export default function FilterBar({
  brand, setBrand, minPrice, setMinPrice, maxPrice, setMaxPrice, sources, toggleSource, onApply,
}: Props) {
  return (
    <div className="border rounded-xl bg-white p-4 flex flex-wrap gap-3 items-end">
      <div>
        <label className="text-xs text-gray-500">Brand</label>
        <input value={brand} onChange={(e) => setBrand(e.target.value)} className="block border rounded-lg px-3 py-2" placeholder="e.g. sony" />
      </div>
      <div>
        <label className="text-xs text-gray-500">Min</label>
        <input value={minPrice} onChange={(e) => setMinPrice(e.target.value)} className="block border rounded-lg px-3 py-2 w-28" placeholder="0" />
      </div>
      <div>
        <label className="text-xs text-gray-500">Max</label>
        <input value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)} className="block border rounded-lg px-3 py-2 w-28" placeholder="200" />
      </div>
      <div className="flex items-center gap-3 text-sm">
        {["amazon", "ebay", "walmart"].map((s) => (
          <label key={s} className="flex items-center gap-1">
            <input type="checkbox" checked={!!sources[s]} onChange={() => toggleSource(s)} />
            {s}
          </label>
        ))}
      </div>
      <button onClick={onApply} className="ml-auto px-4 py-2 rounded-lg bg-black text-white">Apply</button>
    </div>
  );
}
