import React, { useState, useMemo } from 'react';
import { Sparkles, TrendingDown, Star, ShoppingCart, X, Check, AlertCircle } from 'lucide-react';
import type { Product } from '../types/product';

interface SmartDecisionAgentProps {
  isOpen: boolean;
  onClose: () => void;
  selectedProducts: Product[];
  onClearSelection: () => void;
  onRemoveProduct: (productId: string) => void;
}

interface ProductComparison {
  averagePrice: number;
  minPrice: number;
  maxPrice: number;
  averageRating: number;
  sourceCount: { [key: string]: number };
  bestDeal: Product | null;
  recommendation: string;
}

export default function SmartDecisionAgent({ 
  isOpen, 
  onClose, 
  selectedProducts,
  onClearSelection,
  onRemoveProduct
}: SmartDecisionAgentProps) {
  const [showComparison, setShowComparison] = useState(false);

  const comparison: ProductComparison = useMemo(() => {
    if (selectedProducts.length === 0) {
      return {
        averagePrice: 0,
        minPrice: 0,
        maxPrice: 0,
        averageRating: 0,
        sourceCount: {},
        bestDeal: null,
        recommendation: ''
      };
    }

    const prices = selectedProducts.map(p => p.price || 0);
    const ratings = selectedProducts.map(p => p.rating || 0);
    
    const sourceCount: { [key: string]: number } = {};
    selectedProducts.forEach(p => {
      sourceCount[p.source] = (sourceCount[p.source] || 0) + 1;
    });

    // Find best deal based on price and rating
    const bestDeal = selectedProducts.reduce((best, current) => {
      if (!best) return current;
      
      const bestScore = (best.rating || 0) * 20 - (best.price || 0);
      const currentScore = (current.rating || 0) * 20 - (current.price || 0);
      
      return currentScore > bestScore ? current : best;
    }, selectedProducts[0]);

    const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;
    const avgRating = ratings.reduce((a, b) => a + b, 0) / ratings.length;

    let recommendation = '';
    if (bestDeal) {
      const priceDifference = ((bestDeal.price || 0) / avgPrice - 1) * 100;
      recommendation = `${bestDeal.source.toUpperCase()} offers the best value at $${bestDeal.price?.toFixed(2)} with a ${bestDeal.rating?.toFixed(1)}-star rating`;
      
      if (priceDifference < 0) {
        recommendation += ` — $${(avgPrice - (bestDeal.price || 0)).toFixed(2)} below average!`;
      }
    }

    return {
      averagePrice: avgPrice,
      minPrice: Math.min(...prices),
      maxPrice: Math.max(...prices),
      averageRating: avgRating,
      sourceCount,
      bestDeal,
      recommendation
    };
  }, [selectedProducts]);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(price);
  };

  const getTop3Prices = () => {
    return [...selectedProducts]
      .sort((a, b) => (a.price || 0) - (b.price || 0))
      .slice(0, 3)
      .map(p => ({ price: p.price || 0, source: p.source }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed top-20 left-1/2 transform -translate-x-1/2 w-11/12 max-w-5xl bg-white bg-opacity-95 backdrop-blur-lg shadow-2xl rounded-2xl z-50 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-6 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-white bg-opacity-20 rounded-lg">
            <Sparkles className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-2xl font-bold">Smart Decision Agent</h2>
            <p className="text-sm text-purple-100">Finding the best deal for you</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
        >
          <X className="h-6 w-6" />
        </button>
      </div>

      <div className="p-6 overflow-y-auto max-h-[70vh]">
        {/* Selected Products */}
        {selectedProducts.length === 0 ? (
          <div className="text-center py-12">
            <ShoppingCart className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No products selected</h3>
            <p className="text-gray-600">Select products from search results to compare</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Selection Summary */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Check className="h-5 w-5 text-blue-600" />
                  <h3 className="text-lg font-semibold text-gray-900">
                    {selectedProducts.length} {selectedProducts.length === 1 ? 'product' : 'products'} selected
                  </h3>
                </div>
                <button
                  onClick={onClearSelection}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  Clear all
                </button>
              </div>

              {/* Selected Products Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {selectedProducts.map((product) => (
                  <div key={product.id} className="bg-white rounded-lg p-4 border border-gray-200 relative group">
                    <button
                      onClick={() => onRemoveProduct(product.id)}
                      className="absolute top-2 right-2 p-1 hover:bg-red-100 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Remove from comparison"
                    >
                      <X className="h-4 w-4 text-red-600" />
                    </button>
                    
                    <div className="h-32 bg-gray-100 rounded-lg mb-2 overflow-hidden">
                      <img
                        src={product.image_url || 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop'}
                        alt={product.title}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    
                    <h4 className="font-semibold text-sm text-gray-900 mb-1 line-clamp-2">
                      {product.title}
                    </h4>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-lg font-bold text-gray-900">
                        ${product.price?.toFixed(2)}
                      </span>
                      <div className="flex items-center space-x-1">
                        <Star className="h-4 w-4 text-yellow-400 fill-current" />
                        <span className="text-sm text-gray-600">{product.rating?.toFixed(1)}</span>
                      </div>
                    </div>
                    
                    <div className="mt-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        product.source === 'amazon' ? 'bg-orange-100 text-orange-800' :
                        product.source === 'ebay' ? 'bg-blue-100 text-blue-800' :
                        'bg-sky-100 text-sky-800'
                      }`}>
                        {product.source}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Comparison Analysis */}
            <div className="space-y-4">
              <button
                onClick={() => setShowComparison(!showComparison)}
                className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-6 py-4 rounded-xl font-semibold hover:from-purple-700 hover:to-indigo-700 transition-all duration-200 flex items-center justify-between shadow-lg"
              >
                <span className="flex items-center space-x-2">
                  <Sparkles className="h-5 w-5" />
                  <span>Analyze & Find Best Deal</span>
                </span>
                <span className={`transform transition-transform duration-200 ${showComparison ? 'rotate-180' : ''}`}>
                  ▼
                </span>
              </button>

              {showComparison && (
                <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-xl p-6 border border-purple-100 space-y-4">
                  {/* Top 3 Prices */}
                  <div className="bg-white rounded-lg p-4 shadow-sm">
                    <h4 className="font-semibold text-gray-900 mb-3 flex items-center space-x-2">
                      <TrendingDown className="h-5 w-5 text-green-600" />
                      <span>Top 3 Prices</span>
                    </h4>
                    <div className="space-y-2">
                      {getTop3Prices().map((item, index) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                          <span className="text-sm font-medium text-gray-900 capitalize">
                            {item.source}
                          </span>
                          <span className="text-sm font-semibold text-green-600">
                            {formatPrice(item.price)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Price Analysis */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-white rounded-lg p-4 shadow-sm">
                      <div className="text-sm text-gray-600 mb-1">Average Price</div>
                      <div className="text-2xl font-bold text-gray-900">
                        {formatPrice(comparison.averagePrice)}
                      </div>
                    </div>
                    
                    <div className="bg-white rounded-lg p-4 shadow-sm">
                      <div className="text-sm text-gray-600 mb-1">Lowest Price</div>
                      <div className="text-2xl font-bold text-green-600">
                        {formatPrice(comparison.minPrice)}
                      </div>
                    </div>
                    
                    <div className="bg-white rounded-lg p-4 shadow-sm">
                      <div className="text-sm text-gray-600 mb-1">Highest Price</div>
                      <div className="text-2xl font-bold text-red-600">
                        {formatPrice(comparison.maxPrice)}
                      </div>
                    </div>
                  </div>

                  {/* Best Deal Recommendation */}
                  {comparison.bestDeal && (
                    <div className="bg-white rounded-lg p-6 shadow-sm border-2 border-purple-200">
                      <div className="flex items-start space-x-4">
                        <div className="p-3 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-lg">
                          <Sparkles className="h-6 w-6 text-white" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-bold text-gray-900 mb-2 text-lg">✨ Best Deal Found!</h4>
                          <p className="text-gray-700 mb-3">{comparison.recommendation}</p>
                          
                          <div className="grid grid-cols-2 gap-3 mt-4">
                            <div>
                              <div className="text-xs text-gray-600 mb-1">Price</div>
                              <div className="text-lg font-bold text-purple-600">
                                {formatPrice(comparison.bestDeal.price || 0)}
                              </div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-600 mb-1">Rating</div>
                              <div className="flex items-center space-x-1">
                                <Star className="h-5 w-5 text-yellow-400 fill-current" />
                                <span className="text-lg font-bold text-gray-900">
                                  {comparison.bestDeal.rating?.toFixed(1)}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Average Rating */}
                  <div className="bg-white rounded-lg p-4 shadow-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Average Rating</span>
                      <div className="flex items-center space-x-2">
                        <Star className="h-5 w-5 text-yellow-400 fill-current" />
                        <span className="text-lg font-bold text-gray-900">
                          {comparison.averageRating.toFixed(1)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

