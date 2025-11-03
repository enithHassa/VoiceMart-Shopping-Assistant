import { useState } from 'react';
import { X, MessageCircle, Mic } from 'lucide-react';

interface ConversationBannerProps {
  question: string;
  onAnswer: (answer: string) => void;
  onClose?: () => void;
}

export default function ConversationBanner({ question, onAnswer, onClose }: ConversationBannerProps) {
  const [answer, setAnswer] = useState('');
  const [isListening, setIsListening] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (answer.trim()) {
      onAnswer(answer.trim());
      setAnswer('');
    }
  };

  const handleVoiceAnswer = () => {
    // Start listening for voice answer
    setIsListening(true);
    // This will be handled by the HomePage voice recorder
  };

  return (
    <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 w-11/12 max-w-2xl z-50 animate-slide-up">
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-purple-300">
          <div className="flex items-center space-x-2">
            <MessageCircle className="h-5 w-5" />
            <span className="font-semibold">VoiceMart</span>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 hover:bg-purple-500 rounded-lg transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Question */}
        <div className="p-6">
          <div className="bg-white bg-opacity-20 rounded-xl p-4 mb-4">
            <p className="text-lg font-medium">{question}</p>
          </div>

          {/* Answer Form */}
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              type="text"
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Type your answer..."
              className="flex-1 px-4 py-3 rounded-xl text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-white"
              autoFocus
            />
            <button
              type="submit"
              disabled={!answer.trim()}
              className="px-6 py-3 bg-white text-purple-600 rounded-xl font-semibold hover:bg-purple-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
            <button
              type="button"
              onClick={handleVoiceAnswer}
              className="px-4 py-3 bg-white bg-opacity-20 text-white rounded-xl hover:bg-opacity-30 transition-colors"
              title="Answer with voice"
            >
              <Mic className="h-5 w-5" />
            </button>
          </form>

          {/* Quick Answer Buttons */}
          <div className="mt-4 flex gap-2 flex-wrap">
            {question.toLowerCase().includes('gaming or office') && (
              <>
                <button
                  onClick={() => onAnswer('Gaming')}
                  className="px-4 py-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-lg text-sm font-medium transition-colors"
                >
                  🎮 Gaming
                </button>
                <button
                  onClick={() => onAnswer('Office')}
                  className="px-4 py-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-lg text-sm font-medium transition-colors"
                >
                  💼 Office
                </button>
              </>
            )}
            {question.toLowerCase().includes('category') && (
              <>
                <button
                  onClick={() => onAnswer('Laptop')}
                  className="px-4 py-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-lg text-sm font-medium transition-colors"
                >
                  💻 Laptop
                </button>
                <button
                  onClick={() => onAnswer('Phone')}
                  className="px-4 py-2 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-lg text-sm font-medium transition-colors"
                >
                  📱 Phone
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}


