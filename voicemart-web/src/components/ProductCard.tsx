import { useState } from "react";
import type { Product } from "../types/product";
import { ExternalLink, Star, ShoppingCart, Heart, Eye } from "lucide-react";

function getSourceColor(source: string) {
  const colors: Record<string, { bg: string; text: string; border: string; accent: string }> = {
    amazon: {
      bg: "bg-orange-50",
      text: "text-orange-700",
      border: "border-orange-200",
      accent: "bg-orange-500",
    },
    ebay: {
      bg: "bg-blue-50",
      text: "text-blue-700",
      border: "border-blue-200",
      accent: "bg-blue-500",
    },
    walmart: {
      bg: "bg-sky-50",
      text: "text-sky-700",
      border: "border-sky-200",
      accent: "bg-sky-500",
    },
  };
  return colors[source.toLowerCase()] || {
    bg: "bg-gray-50",
    text: "text-gray-700",
    border: "border-gray-200",
    accent: "bg-gray-500",
  };
}

export default function ProductCard({ product }: { product: Product }) {
  const sourceColor = getSourceColor(product.source);
  const [imageError, setImageError] = useState(false);
  const [isLiked, setIsLiked] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  
  const formatPrice = (price: number, currency = "USD") => {
    try {
      return new Intl.NumberFormat(undefined, { style: "currency", currency }).format(price);
    } catch {
      return `$${price.toFixed(2)}`;
    }
  };

  return (
    <div 
      className="group relative bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden hover:shadow-2xl hover:scale-[1.02] transition-all duration-300"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Image Container */}
      <div className="aspect-square w-full overflow-hidden bg-gradient-to-br from-gray-50 to-gray-100 relative">
        {product.image_url && !imageError ? (
          <img
            src={product.image_url}
            alt={product.title}
            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
            loading="lazy"
            onError={() => {
              console.warn(`Failed to load image for ${product.source}:`, product.image_url);
              setImageError(true);
            }}
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200">
            <div className="text-6xl mb-2 opacity-50">📦</div>
            <div className="text-sm font-medium text-gray-500 capitalize">{product.source}</div>
          </div>
        )}
        
        {/* Source Badge */}
        <div className={`absolute top-3 left-3 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${sourceColor.bg} ${sourceColor.text} backdrop-blur-sm`}>
          {product.source}
        </div>

        {/* Action Buttons */}
        <div className={`absolute top-3 right-3 flex flex-col gap-2 transition-all duration-300 ${
          isHovered ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-2'
        }`}>
          <button
            onClick={(e) => {
              e.preventDefault();
              setIsLiked(!isLiked);
            }}
            className={`p-2 rounded-full backdrop-blur-sm transition-all duration-200 ${
              isLiked 
                ? 'bg-red-500 text-white' 
                : 'bg-white/80 text-gray-600 hover:bg-red-50 hover:text-red-500'
            }`}
          >
            <Heart className={`h-4 w-4 ${isLiked ? 'fill-current' : ''}`} />
          </button>
          <button className="p-2 rounded-full bg-white/80 text-gray-600 hover:bg-blue-50 hover:text-blue-500 backdrop-blur-sm transition-all duration-200">
            <Eye className="h-4 w-4" />
          </button>
        </div>

        {/* Quick View Overlay */}
        <div className={`absolute inset-0 bg-black/40 flex items-center justify-center transition-all duration-300 ${
          isHovered ? 'opacity-100' : 'opacity-0'
        }`}>
          <button className="bg-white text-gray-900 px-6 py-3 rounded-full font-semibold hover:bg-gray-100 transition-colors flex items-center space-x-2">
            <Eye className="h-4 w-4" />
            <span>Quick View</span>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-4">
        {/* Title */}
        <div className="min-h-[3rem]">
          <h3 className="text-lg font-semibold text-gray-900 line-clamp-2 group-hover:text-blue-600 transition-colors leading-tight">
            {product.title}
          </h3>
        </div>

        {/* Brand & Category */}
        <div className="flex items-center justify-between text-sm">
          {product.brand && (
            <span className="text-gray-600 font-medium">
              {product.brand}
            </span>
          )}
          {product.category && (
            <span className="text-gray-500 bg-gray-100 px-2 py-1 rounded-full text-xs">
              {product.category}
            </span>
          )}
        </div>

        {/* Rating */}
        {typeof product.rating === "number" && product.rating > 0 && (
          <div className="flex items-center gap-2">
            <div className="flex items-center">
              {[...Array(5)].map((_, i) => (
                <Star 
                  key={i} 
                  className={`h-4 w-4 ${
                    i < Math.round(product.rating!) 
                      ? "text-yellow-400 fill-current" 
                      : "text-gray-300"
                  }`} 
                />
              ))}
            </div>
            <span className="text-sm text-gray-600 font-medium">
              {product.rating.toFixed(1)}
            </span>
            <span className="text-xs text-gray-500">(4.2k reviews)</span>
          </div>
        )}

        {/* Price */}
        <div className="flex items-baseline justify-between">
          <div className="flex items-baseline gap-1">
            <span className="text-sm text-gray-500 uppercase tracking-wide">
              {product.currency || "USD"}
            </span>
            <span className="text-2xl font-bold text-gray-900 ml-1">
              {formatPrice(product.price, product.currency)}
            </span>
          </div>
          {product.availability && (
            <div className="text-right">
              {product.availability.toLowerCase().includes('in stock') ? (
                <span className="inline-flex items-center text-green-600 text-sm font-medium">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  In Stock
                </span>
              ) : product.availability.toLowerCase().includes('out of stock') ? (
                <span className="text-red-600 text-sm font-medium">Out of Stock</span>
              ) : (
                <span className="text-gray-600 text-sm">{product.availability}</span>
              )}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 pt-2">
          <a
            href={product.url || "#"}
            target="_blank"
            rel="noreferrer"
            className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 px-4 rounded-xl font-semibold hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 flex items-center justify-center space-x-2 group"
          >
            <ExternalLink className="h-4 w-4" />
            <span>View Product</span>
          </a>
          <button className="bg-gray-100 hover:bg-gray-200 text-gray-700 py-3 px-4 rounded-xl font-semibold transition-colors duration-200 flex items-center justify-center">
            <ShoppingCart className="h-4 w-4" />
          </button>
        </div>

        {/* Description */}
        {product.description && (
          <div className="pt-2 border-t border-gray-100">
            <p className="text-sm text-gray-600 line-clamp-2">
              {product.description}
            </p>
          </div>
        )}
      </div>

      {/* Hover Effect Border */}
      <div className={`absolute inset-0 rounded-2xl border-2 transition-all duration-300 pointer-events-none ${
        isHovered ? 'border-blue-200' : 'border-transparent'
      }`}></div>
    </div>
  );
}