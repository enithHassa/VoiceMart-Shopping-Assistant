import React, { useState, useEffect } from 'react';
import { Star, TrendingUp, Users, Tag, Sparkles, ChevronLeft, ChevronRight } from 'lucide-react';
import type { Product } from '../types/product';
import { API } from '../lib/api';

interface RecommendationProduct extends Product {
  recommendation_type: string;
  recommendation_reason: string;
  recommendation_score: number;
}

interface RecommendationSectionProps {
  userId: string;
  title?: string;
  limit?: number;
  isOpen: boolean;
  onClose: () => void;
}

const getRecommendationIcon = (type: string) => {
  switch (type) {
    case 'content_based':
      return <Sparkles className="h-3 w-3" />;
    case 'collaborative':
      return <Users className="h-3 w-3" />;
    case 'trending':
      return <TrendingUp className="h-3 w-3" />;
    case 'category_based':
      return <Tag className="h-3 w-3" />;
    default:
      return <Star className="h-3 w-3" />;
  }
};

export default function RecommendationSection({ 
  userId, 
  title = "Recommended for You", 
  limit = 8,
  isOpen,
  onClose
}: RecommendationSectionProps) {
  const [recommendations, setRecommendations] = useState<RecommendationProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!userId || !isOpen) {
        setLoading(false);
        return;
      }

       try {
         setLoading(true);
         setError(null);
         
         console.log('🎯 Making API call to:', `${API}/v1/recommendations/products/${userId}?limit=${limit}`);
         const response = await fetch(`${API}/v1/recommendations/products/${userId}?limit=${limit}`);
         
         console.log('🎯 Response status:', response.status);
         console.log('🎯 Response ok:', response.ok);
         
         if (!response.ok) {
           throw new Error(`Failed to fetch recommendations: ${response.statusText}`);
         }
        
         const data = await response.json();
         console.log('🎯 Recommendation data received:', data);
         console.log('🎯 First recommendation:', data.recommendations?.[0]);
         
         // Add a test product to see if rendering works
         const testProduct = {
           id: 'test-123',
           title: 'Test Product Title',
           price: 99.99,
           currency: 'USD',
           image_url: 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop',
           rating: 4.5,
           source: 'amazon',
           recommendation_type: 'test',
           recommendation_reason: 'This is a test product',
           recommendation_score: 0.8
         };
         
         const allRecommendations = [testProduct, ...(data.recommendations || [])];
         console.log('🎯 Setting recommendations:', allRecommendations);
         setRecommendations(allRecommendations);
        
      } catch (err) {
        console.error('Failed to fetch recommendations:', err);
        setError('Failed to load recommendations');
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [userId, limit, isOpen]);

  if (!userId) {
    return null;
  }

  return (
    <>
      {/* Sidebar */}
      <div className={`fixed top-0 right-0 h-full w-3/5 max-w-2xl bg-white bg-opacity-95 backdrop-blur-lg shadow-2xl z-50 transform transition-transform duration-500 ease-in-out ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      }`}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-blue-600 to-indigo-600 text-white relative">
          {/* Collapse Button - Only show when open */}
          {isOpen && (
            <button
              onClick={onClose}
              className="absolute -left-5 h-14 bg-blue-600 hover:bg-blue-700 text-white px-1 rounded-l-lg transition-all duration-300 hover:scale-110 flex items-center justify-center"
              title="Collapse recommendations"
              style={{ top: '50%', transform: 'translateY(-50%)' }}
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
          )}

          <div className="flex items-center">
            <Sparkles className="h-6 w-6 mr-3" />
            <h2 className="text-xl font-bold">{title}</h2>
          </div>
        </div>

        {/* Content */}
        <div className="h-full overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading recommendations...</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="text-red-500 text-4xl mb-4">⚠️</div>
                <p className="text-gray-600 mb-4">{error}</p>
                <button 
                  onClick={() => window.location.reload()}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Retry
                </button>
              </div>
            </div>
          ) : (
            <div className="p-6">
              {/* Stats */}
              <div className="mb-6 text-center">
                <div className="inline-flex items-center px-4 py-2 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                  <Sparkles className="w-4 h-4 mr-2" />
                  {recommendations.length} personalized items
                </div>
              </div>

              {/* Products Grid - Horizontal Scrollable */}
              <div className="flex gap-6 overflow-x-auto pb-4" style={{
                scrollbarWidth: 'thin',
                scrollbarColor: '#cbd5e1 #f1f5f9'
              }}>
                {recommendations.map((product, index) => (
                  <div 
                    key={product.id} 
                    className="flex-shrink-0 w-80 bg-white rounded-xl border border-gray-200 overflow-hidden cursor-pointer hover:shadow-lg transition-all duration-300 hover:scale-105"
                    onClick={() => {
                      if (product.url) {
                        window.open(product.url, '_blank', 'noopener,noreferrer');
                      }
                    }}
                  >
                    {/* Product Image */}
                    <div className="relative h-48 bg-gray-100 overflow-hidden">
                      <img
                        src={product.image_url && product.image_url !== 'undefined' ? product.image_url : 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop'}
                        alt={product.title}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          target.src = 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=400&fit=crop';
                        }}
                      />
                    </div>
                    
                    {/* Product Info */}
                    <div className="p-4">
                      <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
                        {product.title}
                      </h3>
                      
                      <p className="text-xs text-gray-600 mb-3 line-clamp-2">
                        {product.recommendation_reason}
                      </p>
                      
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <span className="text-lg font-bold text-gray-900">
                            ${product.price?.toFixed(2) || '0.00'}
                          </span>
                          <span className="text-xs text-gray-500">
                            {product.currency || 'USD'}
                          </span>
                        </div>
                        
                        <div className="flex items-center gap-1">
                          <Star className="w-4 h-4 text-yellow-400 fill-current" />
                          <span className="text-sm text-gray-600">
                            {product.rating?.toFixed(1) || '4.0'}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          product.source === 'amazon' ? 'bg-orange-100 text-orange-800' : 
                          product.source === 'ebay' ? 'bg-blue-100 text-blue-800' : 'bg-blue-100 text-blue-800'
                        }`}>
                          {product.source}
                        </span>
                        
                        {product.brand && (
                          <span className="text-xs text-gray-500 truncate max-w-20">
                            {product.brand}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Scroll Indicator */}
              {recommendations.length > 3 && (
                <div className="mt-4 text-center">
                  <div className="inline-flex items-center text-sm text-gray-500">
                    <ChevronLeft className="w-4 h-4 mr-1" />
                    Scroll to see more recommendations
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </div>
                </div>
              )}

              {/* Recommendation Types Legend */}
              <div className="mt-6 pt-4 border-t border-gray-200">
                <div className="flex flex-wrap items-center justify-center space-x-4 text-xs text-gray-500">
                  <div className="flex items-center space-x-1">
                    <Sparkles className="h-3 w-3 text-blue-500" />
                    <span>Content-based</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Users className="h-3 w-3 text-green-500" />
                    <span>Collaborative</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <TrendingUp className="h-3 w-3 text-orange-500" />
                    <span>Trending</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Tag className="h-3 w-3 text-purple-500" />
                    <span>Category-based</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}