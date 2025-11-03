import { useState } from 'react';
import { testVoiceConversation, type ConversationResponse } from '../lib/api';

export default function ConversationTest() {
  const [sessionId] = useState(() => `test-${Date.now()}`);
  const [responses, setResponses] = useState<ConversationResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [testText, setTestText] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Since we don't have actual audio files, we'll simulate the conversation
  const simulateConversation = async (text: string, reset: boolean = false) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await testVoiceConversation(text, sessionId, null, reset);
      setResponses(prev => [...prev, response]);
      
      // Show conversation state
      console.log('💬 Conversation State:', {
        question: response.conversation.question,
        readyToSearch: response.conversation.ready_to_search,
        query: response.conversation.query
      });
      
    } catch (err: any) {
      console.error('❌ Conversation test error:', err);
      setError(err.message || 'Test failed');
    } finally {
      setLoading(false);
    }
  };

  const handleTest = (text: string, reset = false) => {
    setTestText('');
    simulateConversation(text, reset);
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">🗣️ Voice Conversation Test</h1>
      
      <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Test Interface</h2>
        <p className="text-sm text-gray-600 mb-4">Session ID: {sessionId}</p>
        
        <div className="flex gap-4 mb-4">
          <input
            type="text"
            value={testText}
            onChange={(e) => setTestText(e.target.value)}
            placeholder="Type a query (e.g., 'Find me laptops under 1000')"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg"
          />
          <button
            onClick={() => handleTest(testText)}
            disabled={!testText || loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Processing...' : 'Send'}
          </button>
          <button
            onClick={() => handleTest('', true)}
            className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Reset
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <p className="text-red-700">Error: {error}</p>
          </div>
        )}
      </div>

      {/* Quick Test Buttons */}
      <div className="bg-gray-50 rounded-xl p-6 mb-6">
        <h3 className="font-semibold mb-3">Quick Tests:</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <button
            onClick={() => handleTest('Find me laptops under 1000')}
            className="px-4 py-2 bg-gradient-to-r from-purple-500 to-indigo-500 text-white rounded-lg hover:from-purple-600 hover:to-indigo-600"
          >
            🖥️ "Find me laptops under 1000"
          </button>
          <button
            onClick={() => handleTest('Gaming')}
            className="px-4 py-2 bg-gradient-to-r from-green-500 to-teal-500 text-white rounded-lg hover:from-green-600 hover:to-teal-600"
          >
            🎮 "Gaming"
          </button>
        </div>
      </div>

      {/* Conversation History */}
      <div className="space-y-4">
        <h3 className="text-xl font-semibold">Conversation History:</h3>
        {responses.length === 0 ? (
          <p className="text-gray-500">No conversation yet. Start by typing a query!</p>
        ) : (
          responses.map((response, index) => (
            <div key={index} className="bg-white rounded-xl shadow p-6">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                    {index + 1}
                  </div>
                </div>
                <div className="flex-1">
                  <div className="mb-3">
                    <span className="text-xs font-medium text-gray-500">User said:</span>
                    <p className="text-gray-900 font-medium">{response.transcript.text}</p>
                  </div>
                  
                  {response.conversation.question && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                      <span className="text-xs font-medium text-blue-700">💬 System asks:</span>
                      <p className="text-blue-900 font-medium mt-1">{response.conversation.question}</p>
                    </div>
                  )}
                  
                  {response.conversation.ready_to_search && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                      <span className="text-xs font-medium text-green-700">✅ Ready to search!</span>
                      <p className="text-green-900 text-sm mt-1">
                        Query: {response.conversation.query}
                      </p>
                      {response.products && response.products.length > 0 && (
                        <p className="text-green-900 text-sm mt-1">
                          Found {response.products.length} products
                        </p>
                      )}
                    </div>
                  )}
                  
                  <div className="mt-3 text-xs text-gray-500">
                    <span>Ready: {response.conversation.ready_to_search ? 'Yes' : 'No'} | </span>
                    <span>Products: {response.products?.length || 0}</span>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

