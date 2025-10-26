import React from 'react';
import { Clock, ChevronRight } from 'lucide-react';

interface SearchHistoryBadgeProps {
  isOpen: boolean;
  onClick: () => void;
  user: any;
}

const SearchHistoryBadge: React.FC<SearchHistoryBadgeProps> = ({ isOpen, onClick, user }) => {
  if (!user) return null;

  return (
    <div className="fixed top-1/4 left-4 transform -translate-y-1/2 z-30">
      <button
        onClick={onClick}
        className={`group relative flex items-center space-x-3 px-4 py-3 rounded-2xl shadow-lg transition-all duration-300 hover:scale-105 ${
          isOpen 
            ? 'bg-green-600 text-white shadow-green-200' 
            : 'bg-white text-gray-700 hover:bg-green-50 hover:text-green-600'
        }`}
      >
        {/* Arrow Indicator */}
        <div className={`transition-transform duration-300 ${
          isOpen ? 'rotate-180' : 'rotate-0'
        }`}>
          <ChevronRight className={`h-5 w-5 transition-colors ${
            isOpen ? 'text-white' : 'text-gray-400 group-hover:text-green-500'
          }`} />
        </div>

        {/* Badge Content */}
        <div className="flex items-center space-x-2">
          <div className="text-left">
            <div className={`text-sm font-semibold transition-colors ${
              isOpen ? 'text-white' : 'text-gray-900 group-hover:text-green-600'
            }`}>
              Search
            </div>
            <div className={`text-xs transition-colors ${
              isOpen ? 'text-green-100' : 'text-gray-500 group-hover:text-green-500'
            }`}>
              History
            </div>
          </div>
          
          <div className={`p-2 rounded-xl transition-colors ${
            isOpen ? 'bg-white bg-opacity-20' : 'bg-green-100 group-hover:bg-green-200'
          }`}>
            <Clock className={`h-5 w-5 transition-colors ${
              isOpen ? 'text-white' : 'text-green-600'
            }`} />
          </div>
        </div>

        {/* Pulse Animation */}
        {!isOpen && (
          <div className="absolute -top-1 -left-1 w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
        )}
      </button>
    </div>
  );
};

export default SearchHistoryBadge;
