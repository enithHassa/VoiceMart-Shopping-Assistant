import { useEffect, useMemo, useReducer, useState, useCallback } from "react";
import VoiceRecorder from "../components/VoiceRecorder";
import ProductCard from "../components/ProductCard";
import SearchHistorySidebar from "../components/SearchHistorySidebar";
import RecommendationSection from "../components/RecommendationSection";
import RecommendationBadge from "../components/RecommendationBadge";
import SearchHistoryBadge from "../components/SearchHistoryBadge";
import SmartDecisionAgent from "../components/SmartDecisionAgent";
import { searchProducts } from "../lib/api";
import { saveSearchToHistory } from "../lib/searchHistory";
import { useAuthStore } from "../lib/auth-store";
import { 
  Search, 
  Mic, 
  Filter, 
  X, 
  ChevronDown, 
  Sparkles, 
  ShoppingBag,
  Star,
  TrendingUp,
  Zap
} from "lucide-react";

// ---------- Types ----------
type Product = {
  id: string;
  title: string;
  price: number;
  currency: string;
  image_url?: string | null;
  description?: string | null;
  brand?: string | null;
  category?: string | null;
  rating?: number | null;
  availability?: string | null;
  url?: string | null;
  source: "amazon" | "ebay" | "walmart" | string;
};

type ProductSearchPayload = {
  query: string;
  category?: string | null;
  min_price?: number | null;
  max_price?: number | null;
  brand?: string | null;
  limit?: number;
  sources?: string[];
  fallback?: boolean;
};

type VoiceShopResponse = {
  transcript: {
    text: string;
    language: string;
    duration: number;
  };
  query: {
    intent: string;
    reply?: string;
    slots?: Record<string, any>;
  };
  products?: Product[] | null;
  product_search_performed: boolean;
};

// ---------- Config ----------
const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

// ---------- Helpers ----------
function classNames(...xs: (string | false | null | undefined)[]) {
  return xs.filter(Boolean).join(" ");
}

function formatPrice(p: number, currency = "USD") {
  try {
    return new Intl.NumberFormat(undefined, { style: "currency", currency }).format(p);
  } catch {
    return `$${p.toFixed(2)}`;
  }
}

// ---------- State / Reducer for Filters ----------
type Filters = {
  brand: string;
  minPrice: string;
  maxPrice: string;
  category: string;
  sources: Record<"amazon" | "ebay" | "walmart", boolean>;
  limit: number;
};

type Action =
  | { type: "SET_QUERY"; value: string }
  | { type: "SET_BRAND"; value: string }
  | { type: "SET_MIN"; value: string }
  | { type: "SET_MAX"; value: string }
  | { type: "SET_CATEGORY"; value: string }
  | { type: "TOGGLE_SOURCE"; source: keyof Filters["sources"] }
  | { type: "SET_LIMIT"; value: number }
  | { type: "RESET" };

const initialFilters: Filters = {
  brand: "",
  minPrice: "",
  maxPrice: "",
  category: "",
  sources: { amazon: false, ebay: false, walmart: false }, // Default to no sources selected
  limit: 12,
};

function filtersReducer(state: { query: string; filters: Filters }, action: Action | { type: "SET_QUERY"; value: string }) {
  switch (action.type) {
    case "SET_QUERY":
      return { ...state, query: action.value };
    case "SET_BRAND":
      return { ...state, filters: { ...state.filters, brand: action.value } };
    case "SET_MIN":
      return { ...state, filters: { ...state.filters, minPrice: action.value } };
    case "SET_MAX":
      return { ...state, filters: { ...state.filters, maxPrice: action.value } };
    case "SET_CATEGORY":
      return { ...state, filters: { ...state.filters, category: action.value } };
    case "TOGGLE_SOURCE":
      return {
        ...state,
        filters: {
          ...state.filters,
          sources: { ...state.filters.sources, [action.source]: !state.filters.sources[action.source] },
        },
      };
    case "SET_LIMIT":
      return { ...state, filters: { ...state.filters, limit: action.value } };
    case "RESET":
      return { query: "", filters: initialFilters };
    default:
      return state;
  }
}

// ---------- Main Page ----------
export default function HomePage() {
  const [{ query, filters }, dispatch] = useReducer(filtersReducer, {
    query: "",
    filters: initialFilters,
  });

  const { user } = useAuthStore();
  
  // Debug user state
  useEffect(() => {
    console.log("👤 User state changed:", user);
  }, [user]);
  
  const [loading, setLoading] = useState(false);
  const [voiceLoading, setVoiceLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [showHistorySidebar, setShowHistorySidebar] = useState(false);
  const [showRecommendationSidebar, setShowRecommendationSidebar] = useState(false);
  const [showSmartAgent, setShowSmartAgent] = useState(false);
  const [selectedProducts, setSelectedProducts] = useState<Product[]>([]);
  const [searchTimeout, setSearchTimeout] = useState<number | null>(null);
  const [isDebouncing, setIsDebouncing] = useState(false);

  const activeSources = useMemo(
    () => (Object.entries(filters.sources).filter(([, on]) => on).map(([k]) => k) as string[]),
    [filters.sources]
  );

  // Store all products from API (not just filtered ones)
  const [allProducts, setAllProducts] = useState<Product[]>([]);

  // ----- API Calls -----
  const searchByText = useCallback(async () => {
    setError(null);
    setLoading(true);
    
    // Check if at least one source is selected
    if (activeSources.length === 0) {
      setError("Please select at least one source (Amazon, eBay, or Walmart)");
      setLoading(false);
      return;
    }

    if (!query.trim()) {
      setError("Please enter a search query");
      setLoading(false);
      return;
    }

    try {
      const payload: ProductSearchPayload = {
        query: query.trim(),
        category: filters.category || null,
        min_price: filters.minPrice ? parseFloat(filters.minPrice) : null,
        max_price: filters.maxPrice ? parseFloat(filters.maxPrice) : null,
        brand: filters.brand || null,
        limit: filters.limit,
        sources: activeSources,
        fallback: true,
      };

      console.log("🔍 Searching products with payload:", payload);
      console.log("📍 Active sources:", activeSources);
      console.log("⚙️ Current filters.sources:", filters.sources);
      console.log("🌐 API URL:", import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000");

      const result = await searchProducts(payload);
      console.log("✅ Products received from API:", result);
      console.log("📊 Product count:", result.products?.length || 0);
      console.log("🏷️ Product sources:", result.products?.map(p => p.source) || []);

      if (result.products && result.products.length > 0) {
        console.log("✅ Setting real products from API");
        setProducts(result.products);
        setAllProducts(result.products);
        setHasSearched(true);
        setError(null);
        
        // Save search to history if user is logged in
        if (user) {
          try {
            await saveSearchToHistory(
              query.trim(),
              activeSources,
              result.products.length,
              user.id
            );
            console.log("💾 Search saved to history for user:", user.name);
          } catch (error) {
            console.error("Failed to save search to history:", error);
          }
        }
      } else {
        // Generate demo products as fallback
        console.log("⚠️ No products from API, generating demo products");
        const demoProducts = generateDemoProducts(query, activeSources);
        console.log("🎭 Demo products generated:", demoProducts);
        setProducts(demoProducts);
        setAllProducts(demoProducts);
        setHasSearched(true);
        setError("No products found. Showing demo results. Make sure the backend API is running at http://localhost:8000 for real results.");
      }
    } catch (error: any) {
      console.error("❌ Search error:", error);
      console.error("❌ Error details:", error.message);
      setError(`Failed to search products: ${error.message}`);
      
      // Generate demo products as fallback
      console.log("🎭 Generating demo products due to error");
      const demoProducts = generateDemoProducts(query, activeSources);
      setProducts(demoProducts);
      setAllProducts(demoProducts);
      setHasSearched(true);
    } finally {
      setLoading(false);
    }
  }, [query, filters, activeSources]);

  // ----- Debounced Search -----
  const debouncedSearch = useCallback(() => {
    // Clear existing timeout
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }
    
    // Set debouncing state
    setIsDebouncing(true);
    
    // Set new timeout
    const timeout = setTimeout(() => {
      console.log("🔍 Debounced search triggered");
      setIsDebouncing(false);
      searchByText();
    }, 1500); // 1.5 second delay
    
    setSearchTimeout(timeout);
  }, [searchTimeout, searchByText]);

  const handleVoiceTranscript = useCallback((transcript: string) => {
    console.log("🎤 Voice transcript received:", transcript);
    dispatch({ type: "SET_QUERY", value: transcript });
    
    // Automatically search when we get a transcript
    if (transcript.trim()) {
      setTimeout(() => {
        searchByText();
      }, 500); // Small delay to ensure the query state is updated
    }
  }, [searchByText]);

  const searchByVoiceFile = useCallback(async (file: File) => {
    console.log("🎤 Simple voice search started");
    console.log("📦 File details:", { 
      name: file.name, 
      size: file.size, 
      type: file.type
    });

    // Basic file validation
    if (!file || file.size === 0) {
      setError("No audio recorded. Please try again.");
      return;
    }
    
    console.log(`✅ Audio file size: ${file.size} bytes`);
    
    setError(null);
    setVoiceLoading(true);

    try {
      const formData = new FormData();
      
      // Create a new File with explicit MIME type to ensure proper content-type
      const audioFile = new File([file], file.name, { 
        type: "audio/webm;codecs=opus" 
      });
      
      formData.append("file", audioFile);
      formData.append("locale", "en-US");

      console.log("🎤 Sending to backend...");
      console.log("🎤 File MIME type:", audioFile.type);

      const response = await fetch(`${API_BASE}/v1/voice:shop`, {
        method: "POST",
        body: formData,
        mode: 'cors',
        credentials: 'omit',
        headers: {
          'Accept': 'application/json',
        },
      });

      console.log("🎤 Response status:", response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("❌ Voice API error:", response.status, errorText);
        throw new Error(`Voice search failed: ${response.status}`);
      }

      const data = await response.json();
      console.log("🎤 Response:", data);

      if (data.transcript?.text) {
        console.log("✅ Transcript:", data.transcript.text);
        dispatch({ type: "SET_QUERY", value: data.transcript.text });
        setError(null);
      } else {
        console.log("❌ No transcript received");
        setError("Could not understand the audio. Please try speaking more clearly.");
      }
    } catch (error: any) {
      console.error("❌ Voice search error:", error);
      
      if (error.message.includes("Failed to fetch")) {
        setError("Cannot connect to voice service. Please check if the backend is running on port 8000.");
      } else {
        setError(`Voice search failed: ${error.message || 'Unknown error'}`);
      }
    } finally {
      setVoiceLoading(false);
      console.log("🎤 Voice search completed");
    }
  }, []);

  // Generate demo products
  const generateDemoProducts = (searchQuery: string, sources: string[]): Product[] => {
    const baseProducts = [
      {
        id: "demo-1",
        title: `${searchQuery} - Premium Quality`,
        price: 299.99,
        currency: "USD",
        image_url: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=300&h=300&fit=crop",
        description: "High-quality product with excellent features",
        brand: "Premium Brand",
        category: "Electronics",
        rating: 4.5,
        availability: "In Stock",
        url: "https://example.com",
        source: "amazon" as const,
      },
      {
        id: "demo-2",
        title: `${searchQuery} - Best Value`,
        price: 199.99,
        currency: "USD",
        image_url: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=300&h=300&fit=crop",
        description: "Great value for money with reliable performance",
        brand: "Value Brand",
        category: "Electronics",
        rating: 4.2,
        availability: "In Stock",
        url: "https://example.com",
        source: "ebay" as const,
      },
      {
        id: "demo-3",
        title: `${searchQuery} - Budget Friendly`,
        price: 99.99,
        currency: "USD",
        image_url: "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=300&h=300&fit=crop",
        description: "Affordable option with good quality",
        brand: "Budget Brand",
        category: "Electronics",
        rating: 3.8,
        availability: "In Stock",
        url: "https://example.com",
        source: "walmart" as const,
      },
    ];

    return baseProducts.filter(product => sources.includes(product.source));
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (searchTimeout) {
        clearTimeout(searchTimeout);
        setIsDebouncing(false);
      }
    };
  }, [searchTimeout]);

  // Handle Enter key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      searchByText();
    }
  };

  // Handle source toggle
  const handleSourceToggle = (source: keyof Filters["sources"]) => {
    console.log(`Toggling source: ${source}, current state:`, filters.sources);
    dispatch({ type: "TOGGLE_SOURCE", source });
  };

  // Trigger search when sources change (but not on initial load)
  useEffect(() => {
    console.log(`🔄 Source change detected:`, {
      hasSearched,
      query: query.trim(),
      activeSources,
      activeSourcesLength: activeSources.length
    });
    
    if (hasSearched && query.trim() && activeSources.length > 0) {
      console.log(`✅ Sources changed, triggering debounced search with:`, activeSources);
      debouncedSearch();
    } else {
      console.log(`⏸️ Not triggering search:`, {
        reason: !hasSearched ? 'not searched yet' : !query.trim() ? 'no query' : 'no sources selected'
      });
    }
  }, [activeSources, hasSearched, query, debouncedSearch]);

  // Handle search from history
  const handleSearchFromHistory = useCallback((query: string, sources: string[]) => {
    console.log(`🔄 Searching from history:`, { query, sources });
    
    // Clear any pending debounced search
    if (searchTimeout) {
      clearTimeout(searchTimeout);
      setSearchTimeout(null);
      setIsDebouncing(false);
    }
    
    // Update the query
    dispatch({ type: "SET_QUERY", value: query });
    
    // Update sources
    const newSources = { amazon: false, ebay: false, walmart: false };
    sources.forEach(source => {
      if (source in newSources) {
        newSources[source as keyof typeof newSources] = true;
      }
    });
    
    // Update filters with new sources
    Object.entries(newSources).forEach(([source, isSelected]) => {
      if (isSelected !== filters.sources[source as keyof typeof filters.sources]) {
        dispatch({ type: "TOGGLE_SOURCE", source: source as keyof typeof filters.sources });
      }
    });
    
    // Close the sidebar
    setShowHistorySidebar(false);
    
    // Trigger search immediately (no debouncing for history searches)
    setTimeout(() => {
      searchByText();
     }, 100);
   }, [filters.sources, searchByText, searchTimeout]);

  // Handle product selection for Smart Agent
  const handleToggleProductSelection = useCallback((product: Product) => {
    setSelectedProducts(prev => {
      const isSelected = prev.some(p => p.id === product.id);
      if (isSelected) {
        return prev.filter(p => p.id !== product.id);
      } else {
        return [...prev, product];
      }
    });
  }, []);

  const handleClearSelection = useCallback(() => {
    setSelectedProducts([]);
  }, []);

  const handleRemoveProduct = useCallback((productId: string) => {
    setSelectedProducts(prev => prev.filter(p => p.id !== productId));
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-white">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/5 to-indigo-600/5"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <div className="flex items-center justify-center mb-6">
              <div className="p-3 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl shadow-lg">
                <Sparkles className="h-8 w-8 text-white" />
              </div>
            </div>
             <div className="flex items-center justify-center mb-6">
               <h1 className="text-4xl md:text-6xl font-bold text-gray-900">
                 Find Your Perfect
                 <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                   {" "}Products
                 </span>
               </h1>
             </div>
            <p className="text-xl text-gray-600 mb-12 max-w-3xl mx-auto">
              Search across Amazon, eBay, and Walmart with voice or text. 
              Get the best deals and compare prices instantly.
            </p>

            {/* Search Bar */}
            <div className="max-w-4xl mx-auto">
              <div className="relative">
                <div className="flex items-center bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden">
                  <div className="flex-1 flex items-center px-6 py-4">
                    <Search className="h-6 w-6 text-gray-400 mr-4" />
                    <input
                      type="text"
                      value={query}
                      onChange={(e) => dispatch({ type: "SET_QUERY", value: e.target.value })}
                      onKeyPress={handleKeyPress}
                      placeholder="Search for products... (e.g., 'wireless headphones', 'laptop')"
                      className="flex-1 text-lg border-none outline-none placeholder-gray-500"
                    />
                  </div>
                    <div className="flex items-center space-x-2 pr-4">
                      <VoiceRecorder
                        onTranscript={handleVoiceTranscript}
                        autoSend={true}
                        label="Hold to talk"
                        onComplete={() => {}} // Required prop but not used
                      />
                    <button
                      onClick={searchByText}
                      disabled={loading || !query.trim() || activeSources.length === 0}
                      className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-8 py-3 rounded-xl font-semibold hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center space-x-2"
                    >
                      {loading ? (
                        <>
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                          <span>Searching...</span>
                        </>
                      ) : isDebouncing ? (
                        <>
                          <div className="animate-pulse rounded-full h-5 w-5 bg-white opacity-70"></div>
                          <span>Typing...</span>
                        </>
                      ) : (
                        <>
                          <Search className="h-5 w-5" />
                          <span>Search</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* Source Selection Helper */}
              {activeSources.length === 0 && (
                <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-xl p-4">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="w-5 h-5 bg-yellow-400 rounded-full flex items-center justify-center">
                        <span className="text-yellow-800 text-xs font-bold">!</span>
                      </div>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-yellow-800">
                        <strong>Please select at least one source</strong> (Amazon, eBay, or Walmart) to search for products.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Quick Stats */}
              <div className="mt-8 flex justify-center space-x-8 text-sm text-gray-600">
                <div className="flex items-center space-x-2">
                  <TrendingUp className="h-4 w-4 text-green-500" />
                  <span>Compare Prices</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Zap className="h-4 w-4 text-yellow-500" />
                  <span>Instant Results</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Star className="h-4 w-4 text-blue-500" />
                  <span>Best Deals</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Filters & Results Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Filters Sidebar */}
          <div className={`lg:w-80 ${showFilters ? 'block' : 'hidden lg:block'}`}>
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 sticky top-8">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <Filter className="h-5 w-5 mr-2" />
                  Filters
                </h3>
                <button
                  onClick={() => setShowFilters(false)}
                  className="lg:hidden p-1 hover:bg-gray-100 rounded-lg"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Source Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Sources
                </label>
                <div className="space-y-3">
                  {[
                    { key: "amazon", label: "Amazon", color: "bg-orange-500" },
                    { key: "ebay", label: "eBay", color: "bg-blue-500" },
                    { key: "walmart", label: "Walmart", color: "bg-sky-500" },
                  ].map(({ key, label, color }) => (
                    <label key={key} className="flex items-center cursor-pointer group">
                      <input
                        type="checkbox"
                        checked={filters.sources[key as keyof typeof filters.sources]}
                        onChange={() => handleSourceToggle(key as keyof typeof filters.sources)}
                        className="sr-only"
                      />
                      <div className={`w-5 h-5 rounded border-2 mr-3 transition-all duration-200 ${
                        filters.sources[key as keyof typeof filters.sources]
                          ? `${color} border-transparent`
                          : 'border-gray-300 group-hover:border-gray-400'
                      }`}>
                        {filters.sources[key as keyof typeof filters.sources] && (
                          <div className="w-full h-full flex items-center justify-center">
                            <div className="w-2 h-2 bg-white rounded-sm"></div>
                          </div>
                        )}
                      </div>
                      <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900">
                        {label}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Price Range */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Price Range
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <input
                      type="number"
                      placeholder="Min"
                      value={filters.minPrice}
                      onChange={(e) => dispatch({ type: "SET_MIN", value: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <input
                      type="number"
                      placeholder="Max"
                      value={filters.maxPrice}
                      onChange={(e) => dispatch({ type: "SET_MAX", value: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>

              {/* Brand */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Brand
                </label>
                <input
                  type="text"
                  placeholder="e.g., Apple, Samsung"
                  value={filters.brand}
                  onChange={(e) => dispatch({ type: "SET_BRAND", value: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Category */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Category
                </label>
                <select
                  value={filters.category}
                  onChange={(e) => dispatch({ type: "SET_CATEGORY", value: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">All Categories</option>
                  <option value="electronics">Electronics</option>
                  <option value="clothing">Clothing</option>
                  <option value="home">Home & Garden</option>
                  <option value="sports">Sports</option>
                  <option value="books">Books</option>
                </select>
              </div>

              {/* Results Limit */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Results per page
                </label>
                <select
                  value={filters.limit}
                  onChange={(e) => dispatch({ type: "SET_LIMIT", value: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value={12}>12</option>
                  <option value={24}>24</option>
                  <option value={48}>48</option>
                </select>
              </div>

              {/* Reset Button */}
              <button
                onClick={() => dispatch({ type: "RESET" })}
                className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2 px-4 rounded-lg transition-colors duration-200"
              >
                Reset Filters
              </button>
            </div>
          </div>

          {/* Results */}
          <div className="flex-1">
            {/* Mobile Filter Toggle */}
            <div className="lg:hidden mb-6">
              <button
                onClick={() => setShowFilters(true)}
                className="flex items-center space-x-2 bg-white border border-gray-300 rounded-lg px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                <Filter className="h-4 w-4" />
                <span>Filters</span>
                <ChevronDown className="h-4 w-4" />
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-6 bg-red-50 border border-red-200 rounded-xl p-4">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <X className="h-5 w-5 text-red-400" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Results Header */}
            {hasSearched && (
              <div className="mb-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-bold text-gray-900">
                    {products.length > 0 ? `${products.length} Products Found` : 'No Products Found'}
                  </h2>
                  {products.length > 0 && (
                    <div className="text-sm text-gray-600">
                      Showing results for "{query}"
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Products Grid */}
             {loading ? (
               <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
                 {[...Array(6)].map((_, i) => (
                   <div key={i} className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden animate-pulse">
                     <div className="h-64 bg-gray-200"></div>
                     <div className="p-6">
                       <div className="h-5 bg-gray-200 rounded mb-3"></div>
                       <div className="h-4 bg-gray-200 rounded mb-2"></div>
                       <div className="h-4 bg-gray-200 rounded mb-4 w-3/4"></div>
                       <div className="h-8 bg-gray-200 rounded w-1/2"></div>
                     </div>
                   </div>
                 ))}
               </div>
             ) : products.length > 0 ? (
               <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
                 {products.map((product) => (
                   <ProductCard 
                     key={product.id} 
                     product={product}
                     isSelected={selectedProducts.some(p => p.id === product.id)}
                     onSelect={() => handleToggleProductSelection(product)}
                   />
                 ))}
               </div>
            ) : hasSearched ? (
              <div className="text-center py-16">
                <ShoppingBag className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">No products found</h3>
                <p className="text-gray-600 mb-6">Try adjusting your search terms or filters</p>
                <button
                  onClick={() => dispatch({ type: "RESET" })}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
                >
                  Clear Filters
                </button>
              </div>
            ) : (
              <div className="text-center py-16">
                <Search className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Start your search</h3>
                <p className="text-gray-600">Enter a product name or use voice search to find what you're looking for</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Search History Sidebar */}
      <SearchHistorySidebar
        isOpen={showHistorySidebar}
        onClose={() => setShowHistorySidebar(false)}
        onSearchFromHistory={handleSearchFromHistory}
      />

      {/* Recommendation Badge */}
      <RecommendationBadge
        isOpen={showRecommendationSidebar}
        onClick={() => setShowRecommendationSidebar(!showRecommendationSidebar)}
        user={user}
      />

      {/* Search History Badge */}
      <SearchHistoryBadge
        isOpen={showHistorySidebar}
        onClick={() => setShowHistorySidebar(!showHistorySidebar)}
        user={user}
      />

      {/* Recommendation Sidebar */}
      {user && (
        <RecommendationSection
          userId={user.id}
          title="Recommended for You"
          limit={8}
          isOpen={showRecommendationSidebar}
          onClose={() => setShowRecommendationSidebar(false)}
        />
      )}

      {/* Smart Decision Agent Button */}
      {selectedProducts.length > 0 && (
        <button
          onClick={() => setShowSmartAgent(true)}
          className="fixed bottom-8 right-8 bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-4 rounded-full shadow-2xl hover:from-purple-700 hover:to-indigo-700 transition-all duration-300 hover:scale-110 flex items-center space-x-3 z-30"
        >
          <div className="relative">
            <Sparkles className="h-6 w-6" />
            <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
              {selectedProducts.length}
            </span>
          </div>
          <span className="font-semibold">Find Best Deal</span>
        </button>
      )}

      {/* Smart Decision Agent Modal */}
      <SmartDecisionAgent
        isOpen={showSmartAgent}
        onClose={() => setShowSmartAgent(false)}
        selectedProducts={selectedProducts}
        onClearSelection={handleClearSelection}
        onRemoveProduct={handleRemoveProduct}
      />
    </div>
  );
}