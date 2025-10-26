import { useState, useEffect, useRef } from 'react';
import { Clock, Search, Trash2, ExternalLink, ChevronRight } from 'lucide-react';
import { useAuthStore } from '../lib/auth-store';
import { getSearchHistory, clearSearchHistory, deleteSearchHistoryItem } from '../lib/searchHistory';

export interface SearchHistoryItem {
  id: string;
  query: string;
  sources: string[];
  timestamp: number;
  resultCount: number;
  userId: string;
}

interface SearchHistorySidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onSearchFromHistory: (query: string, sources: string[]) => void;
}

export default function SearchHistorySidebar({ 
  isOpen, 
  onClose, 
  onSearchFromHistory 
}: SearchHistorySidebarProps) {
  const { user } = useAuthStore();
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);

  // Load search history when sidebar opens
  useEffect(() => {
    if (isOpen && user) {
      loadSearchHistory();
    }
  }, [isOpen, user]);

  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (sidebarRef.current && !sidebarRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen, onClose]);

  const loadSearchHistory = async () => {
    setLoading(true);
    try {
      if (user?.id) {
        const history = await getSearchHistory(user.id);
        setSearchHistory(history.sort((a: SearchHistoryItem, b: SearchHistoryItem) => b.timestamp - a.timestamp));
      }
    } catch (error) {
      console.error('Failed to load search history:', error);
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = async () => {
    if (!user) return;
    
    try {
      const success = await clearSearchHistory(user.id);
      if (success) {
        setSearchHistory([]);
      }
    } catch (error) {
      console.error('Failed to clear search history:', error);
    }
  };

  const deleteHistoryItem = async (itemId: string) => {
    if (!user) return;
    
    try {
      const success = await deleteSearchHistoryItem(user.id, itemId);
      if (success) {
        setSearchHistory(prev => prev.filter(item => item.id !== itemId));
      }
    } catch (error) {
      console.error('Failed to delete history item:', error);
    }
  };

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 1) {
      return 'Just now';
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else if (diffInHours < 168) { // 7 days
      return `${Math.floor(diffInHours / 24)}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const getSourceColor = (source: string) => {
    const colors: Record<string, string> = {
      amazon: 'bg-orange-100 text-orange-800',
      ebay: 'bg-blue-100 text-blue-800',
      walmart: 'bg-sky-100 text-sky-800',
    };
    return colors[source.toLowerCase()] || 'bg-gray-100 text-gray-800';
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Sidebar */}
      <div ref={sidebarRef} className="fixed left-0 top-0 h-full w-80 bg-white bg-opacity-95 backdrop-blur-lg shadow-2xl z-50 transform transition-transform duration-300 ease-in-out">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 relative">
            {/* Collapse Button - Only show when open */}
            {isOpen && (
              <button
                onClick={onClose}
                className="absolute -right-5 h-14 bg-green-600 hover:bg-green-700 text-white px-1 rounded-r-lg transition-all duration-300 hover:scale-110 flex items-center justify-center"
                title="Collapse search history"
                style={{ top: '50%', transform: 'translateY(-50%)' }}
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            )}

            <div className="flex items-center space-x-2">
              <Search className="h-5 w-5 text-blue-600" />
              <h2 className="text-lg font-semibold text-gray-900">Search History</h2>
            </div>
          </div>

          {/* User Info */}
          {user ? (
            <div className="p-4 bg-gray-50 border-b border-gray-200">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">
                    {user.name?.charAt(0).toUpperCase() || 'U'}
                  </span>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">{user.name}</p>
                  <p className="text-xs text-gray-500">{user.email}</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-4 bg-yellow-50 border-b border-yellow-200">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">!</span>
                </div>
                <div>
                  <p className="text-sm font-medium text-yellow-800">Not Logged In</p>
                  <p className="text-xs text-yellow-600">Please login to view your search history</p>
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          {user && (
            <div className="p-4 border-b border-gray-200">
              <button
                onClick={clearHistory}
                disabled={searchHistory.length === 0}
                className="flex items-center space-x-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Trash2 className="h-4 w-4" />
                <span>Clear All History</span>
              </button>
            </div>
          )}

          {/* History List */}
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : !user ? (
              <div className="flex flex-col items-center justify-center h-32 text-gray-500">
                <Search className="h-8 w-8 mb-2 opacity-50" />
                <p className="text-sm">Please login to view search history</p>
                <p className="text-xs">Your searches will be saved when logged in</p>
              </div>
            ) : searchHistory.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-32 text-gray-500">
                <Search className="h-8 w-8 mb-2 opacity-50" />
                <p className="text-sm">No search history yet</p>
                <p className="text-xs">Your searches will appear here</p>
              </div>
            ) : (
              <div className="p-4 space-y-3">
                {searchHistory.map((item) => (
                  <div
                    key={item.id}
                    className="group p-3 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-all duration-200"
                  >
                    {/* Query and Timestamp */}
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {item.query}
                        </p>
                        <div className="flex items-center space-x-1 mt-1">
                          <Clock className="h-3 w-3 text-gray-400" />
                          <span className="text-xs text-gray-500">
                            {formatTimestamp(item.timestamp)}
                          </span>
                          <span className="text-xs text-gray-400">•</span>
                          <span className="text-xs text-gray-500">
                            {item.resultCount} results
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() => deleteHistoryItem(item.id)}
                        className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded transition-all duration-200"
                      >
                        <Trash2 className="h-3 w-3 text-red-500" />
                      </button>
                    </div>

                    {/* Sources */}
                    <div className="flex flex-wrap gap-1 mb-3">
                      {item.sources.map((source) => (
                        <span
                          key={source}
                          className={`px-2 py-1 text-xs rounded-full ${getSourceColor(source)}`}
                        >
                          {source.charAt(0).toUpperCase() + source.slice(1)}
                        </span>
                      ))}
                    </div>

                    {/* Action Button */}
                    <button
                      onClick={() => onSearchFromHistory(item.query, item.sources)}
                      className="w-full flex items-center justify-center space-x-2 px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    >
                      <ExternalLink className="h-4 w-4" />
                      <span>Search Again</span>
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-gray-200 bg-gray-50">
            <p className="text-xs text-gray-500 text-center">
              Search history helps us personalize your experience
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
