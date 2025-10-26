import React from 'react';
import { Sparkles, ChevronLeft } from 'lucide-react';

interface RecommendationBadgeProps {
  isOpen: boolean;
  onClick: () => void;
  user: any;
}

const RecommendationBadge: React.FC<RecommendationBadgeProps> = ({ isOpen, onClick, user }) => {
  if (!user) return null;

  return (
    <div className="fixed top-3/4 right-4 transform -translate-y-1/2 z-30">
      <button
        onClick={onClick}
        className={`group relative flex items-center space-x-3 px-4 py-3 rounded-2xl shadow-lg transition-all duration-300 hover:scale-105 ${
          isOpen 
            ? 'bg-blue-600 text-white shadow-blue-200' 
            : 'bg-white text-gray-700 hover:bg-blue-50 hover:text-blue-600'
        }`}
      >
        {/* Badge Content */}
        <div className="flex items-center space-x-2">
          <div className={`p-2 rounded-xl transition-colors ${
            isOpen ? 'bg-white bg-opacity-20' : 'bg-blue-100 group-hover:bg-blue-200'
          }`}>
            <Sparkles className={`h-5 w-5 transition-colors ${
              isOpen ? 'text-white' : 'text-blue-600'
            }`} />
          </div>
          
          <div className="text-left">
            <div className={`text-sm font-semibold transition-colors ${
              isOpen ? 'text-white' : 'text-gray-900 group-hover:text-blue-600'
            }`}>
              Recommended
            </div>
            <div className={`text-xs transition-colors ${
              isOpen ? 'text-blue-100' : 'text-gray-500 group-hover:text-blue-500'
            }`}>
              for You
            </div>
          </div>
        </div>

        {/* Arrow Indicator */}
        <div className={`transition-transform duration-300 ${
          isOpen ? 'rotate-180' : 'rotate-0'
        }`}>
          <ChevronLeft className={`h-5 w-5 transition-colors ${
            isOpen ? 'text-white' : 'text-gray-400 group-hover:text-blue-500'
          }`} />
        </div>

        {/* Pulse Animation */}
        {!isOpen && (
          <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
        )}
      </button>
    </div>
  );
};

export default RecommendationBadge;
