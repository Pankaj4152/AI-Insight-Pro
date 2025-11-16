import React, { useState, useRef, useEffect } from 'react';
import { API_BASE_URL_CHATBOT } from '../apiConfig';
import '../Css/Chatbot.css';

const Chatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Function to format message text with proper line breaks and bullet points
  const formatMessageText = (text) => {
    if (!text) return '';
    
    // Split by newlines and process each line
    const lines = text.split('\n');
    return lines.map((line, index) => {
      const trimmedLine = line.trim();
      
      // Handle bullet points
      if (trimmedLine.startsWith('•')) {
        const content = trimmedLine.substring(1).trim();
        return <div key={index} style={{ marginLeft: '20px', marginBottom: '8px' }}>
          <span style={{ color: '#007bff', marginRight: '8px' }}>•</span>
          <span dangerouslySetInnerHTML={{ __html: content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
        </div>;
      }
      
      // Handle numbered points
      if (/^\d+\./.test(trimmedLine)) {
        const number = trimmedLine.match(/^\d+\./)[0];
        const content = trimmedLine.replace(/^\d+\.\s*/, '');
        return <div key={index} style={{ marginLeft: '20px', marginBottom: '8px' }}>
          <span style={{ color: '#007bff', marginRight: '8px' }}>{number}</span>
          <span dangerouslySetInnerHTML={{ __html: content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
        </div>;
      }
      
      // Handle bold text in regular lines
      if (trimmedLine.includes('**')) {
        return <div key={index} style={{ marginBottom: '8px' }}>
          <span dangerouslySetInnerHTML={{ __html: trimmedLine.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
        </div>;
      }
      
      // Regular text
      if (trimmedLine) {
        return <div key={index} style={{ marginBottom: '8px' }}>{trimmedLine}</div>;
      }
      
      // Empty line for spacing
      return <div key={index} style={{ height: '8px' }}></div>;
    });
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setMessages(prev => [...prev, { text: userMessage, sender: 'user' }]);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL_CHATBOT}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: userMessage
        })
      });

      if (response.ok) {
        const data = await response.json();
        const responseText = data.response || 'Sorry, I couldn\'t process your request.';
        setMessages(prev => [...prev, { text: responseText, sender: 'bot' }]);
        
        // Log which LLM was used (for debugging)
        if (data.llm_used) {
          console.log(`LLM used: ${data.llm_used}`);
        }
      } else {
        setMessages(prev => [...prev, { text: 'Sorry, there was an error processing your request.', sender: 'bot' }]);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { text: 'Sorry, there was an error connecting to the server.', sender: 'bot' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Floating Chat Button */}
      <button 
        className="chatbot-button"
        onClick={() => setIsOpen(!isOpen)}
        title="Chat with AI Assistant"
      >
        <svg width="32" height="32" viewBox="0 0 32 32" fill="currentColor">
          {/* <!-- Head (square) --> */}
          <rect x="6" y="8" width="20" height="16" rx="3" fill="currentColor" stroke="#222" strokeWidth="1"/>
          {/* <!-- Eyes --> */}
          <circle cx="12" cy="16" r="2" fill="#111"/>
          <circle cx="20" cy="16" r="2" fill="#111"/>
          {/* <!-- Mouth --> */}
          <rect x="13" y="21" width="6" height="2" rx="1" fill="#222"/>
          {/* <!-- Antenna --> */}
          <rect x="15" y="3" width="2" height="6" rx="1" fill="#222"/>
          <circle cx="16" cy="3" r="1.2" fill="#222"/>
          {/* <!-- Left Arm --> */}
          <rect x="2" y="14" width="4" height="4" rx="2" fill="currentColor" stroke="#222" strokeWidth="1"/>
          <rect x="0" y="15.5" width="4" height="1" rx="0.5" fill="#222"/>
          {/* <!-- Right Arm --> */}
          <rect x="26" y="14" width="4" height="4" rx="2" fill="currentColor" stroke="#222" strokeWidth="1"/>
          <rect x="28" y="15.5" width="4" height="1" rx="0.5" fill="#222"/>
        </svg>
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="chatbot-window">
          <div className="chatbot-header">
            <h3>AI Assistant</h3>
            <button 
              className="chatbot-close"
              onClick={() => setIsOpen(false)}
            >
              ×
            </button>
          </div>
          
          <div className="chatbot-messages">
            {messages.length === 0 && (
              <div className="welcome-message">
                <p>👋 Hello! I'm your AI assistant. How can I help you today?</p>
              </div>
            )}
            
            {messages.map((message, index) => (
              <div 
                key={index} 
                className={`message ${message.sender === 'user' ? 'user-message' : 'bot-message'}`}
              >
                <div className="message-content">
                  {message.sender === 'bot' ? formatMessageText(message.text) : message.text}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="message bot-message">
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
          
          <form onSubmit={handleSubmit} className="chatbot-input">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Type your message..."
              disabled={isLoading}
            />
            <button type="submit" disabled={isLoading || !inputMessage.trim()}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
            </button>
          </form>
        </div>
      )}
    </>
  );
};

export default Chatbot; 