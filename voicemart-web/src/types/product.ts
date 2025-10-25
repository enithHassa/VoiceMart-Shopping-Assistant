export type Product = {
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

export type ProductSearchRequest = {
  query: string;
  category?: string | null;
  min_price?: number | null;
  max_price?: number | null;
  brand?: string | null;
  limit?: number;               // default 10
  sources?: string[];           // ["amazon","ebay","walmart"]
  fallback?: boolean;           // true
};

export type ProductSearchResponse = {
  products: Product[];
  total_results: number;
  query: string;
  filters_applied: Record<string, unknown>;
};

export type VoiceUnderstandResponse = {
  transcript: {
    text: string;
    language: string;
    confidence?: number | null;
    duration?: number | null;
    segments?: { start: number; end: number; text: string }[];
  };
  query: {
    intent: string;
    confidence: number;
    slots: any;
    reply?: string;
    action?: any;
    user_id?: string;
    locale?: string;
  };
  products?: Product[] | null;
  product_search_performed?: boolean;
};
