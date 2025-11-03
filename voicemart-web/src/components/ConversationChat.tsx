import { useState, useRef, useEffect } from 'react';
import { X, Send, MessageCircle, Sparkles, Edit2, Trash2 } from 'lucide-react';

interface Message {
  id: string;
  type: 'user' | 'system';
  text: string;
  timestamp: Date;
  isEditable?: boolean;
}

interface ConversationChatProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  userId?: string | null;
}

export default function ConversationChat({ isOpen, onClose, sessionId, userId }: ConversationChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const sendMessage = async (text: string, messageId?: string) => {
    if (!text.trim() || loading) return;

    let userMessage: Message;
    
    if (messageId && editingMessageId) {
      // Update existing message
      userMessage = {
        id: messageId,
        type: 'user',
        text: text.trim(),
        timestamp: new Date(),
        isEditable: true
      };
      setMessages(prev => prev.map(msg => msg.id === messageId ? userMessage : msg));
      setEditingMessageId(null);
    } else {
      // Add new message
      userMessage = {
        id: `${Date.now()}-${Math.random()}`,
        type: 'user',
        text: text.trim(),
        timestamp: new Date(),
        isEditable: true
      };
      setMessages(prev => [...prev, userMessage]);
    }
    
    setInput('');
    setLoading(true);

    try {
      // Import and call the API
      const { testVoiceConversation } = await import('../lib/api');
      const response = await testVoiceConversation(text, sessionId, userId, false);

      // Add system response or question
      if (response.conversation.question) {
        const systemMessage: Message = {
          id: `${Date.now()}-system`,
          type: 'system',
          text: response.conversation.question,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, systemMessage]);
      } else if (response.products && response.products.length > 0) {
        const systemMessage: Message = {
          id: `${Date.now()}-system`,
          type: 'system',
          text: `Found ${response.products.length} products for: "${response.conversation.query}"`,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, systemMessage]);
      }
    } catch (err: any) {
      console.error('Conversation error:', err);
      const errorMessage: Message = {
        id: `${Date.now()}-system`,
        type: 'system',
        text: `Error: ${err.message}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input, editingMessageId || undefined);
  };

  const handleEdit = (message: Message) => {
    setEditingMessageId(message.id);
    setInput(message.text);
  };

  const handleDelete = (messageId: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== messageId));
  };

  const handleCancelEdit = () => {
    setEditingMessageId(null);
    setInput('');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed bottom-8 right-8 w-96 bg-white rounded-2xl shadow-2xl z-50 flex flex-col border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-t-2xl">
        <div className="flex items-center space-x-2">
          <Sparkles className="h-5 w-5" />
          <span className="font-semibold">Conversation Mode</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 max-h-96 bg-gray-50">
        {messages.length === 0 ? (
          <div className="text-center py-8">
            <MessageCircle className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600 text-sm">Start a conversation!</p>
            <p className="text-gray-500 text-xs mt-2">Try: "Find me laptops under 1000"</p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={msg.id}
              className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'} group`}
            >
              <div className="relative max-w-[80%]">
                <div
                  className={`rounded-2xl px-4 py-2 ${
                    msg.type === 'user'
                      ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white'
                      : 'bg-white border border-gray-200 text-gray-900'
                  }`}
                >
                  <p className="text-sm">{msg.text}</p>
                  <p className={`text-xs mt-1 ${
                    msg.type === 'user' ? 'text-purple-100' : 'text-gray-500'
                  }`}>
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
                
                {/* Edit/Delete buttons for user messages */}
                {msg.type === 'user' && msg.isEditable && (
                  <div className="absolute right-0 top-0 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => handleEdit(msg)}
                      className="p-1 bg-white rounded-full shadow-lg hover:bg-gray-100 transition-colors"
                      title="Edit message"
                    >
                      <Edit2 className="h-3 w-3 text-purple-600" />
                    </button>
                    <button
                      onClick={() => handleDelete(msg.id)}
                      className="p-1 bg-white rounded-full shadow-lg hover:bg-red-100 transition-colors"
                      title="Delete message"
                    >
                      <Trash2 className="h-3 w-3 text-red-600" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200 bg-white rounded-b-2xl">
        <div className="flex gap-2">
          {editingMessageId && (
            <button
              type="button"
              onClick={handleCancelEdit}
              className="px-3 py-2 text-gray-600 hover:text-gray-800 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          )}
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={editingMessageId ? "Editing..." : "Type your message..."}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-xl hover:from-purple-700 hover:to-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            ) : (
              <Send className="h-5 w-5" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

