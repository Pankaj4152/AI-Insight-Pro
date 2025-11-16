import React, { useState, useRef, useEffect } from 'react';
import { API_BASE_URL_CLIENT_CHATBOT } from '../apiConfig';
import { getCurrentClientId } from '../utils/clientUtils';
import '../Css/DatabaseChatbot.css';

const DatabaseChatbot = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [apiHealth, setApiHealth] = useState(null);
  const messagesEndRef = useRef(null);

  // Get client ID - handles both regular clients and compliance officers
  const getClientId = () => {
    return getCurrentClientId();
  };

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

  // Check API health on component mount
  useEffect(() => {
    checkApiHealth();
  }, []);

  const checkApiHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL_CLIENT_CHATBOT}/health`);
      const health = await response.json();
      setApiHealth(health);
    } catch (error) {
      console.error('API Health Check Error:', error);
      setApiHealth({ status: 'unhealthy', error: error.message });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    const clientId = getClientId();
    if (!clientId) {
      setMessages(prev => [...prev, { 
        text: 'Error: Please log in to use the chatbot.', 
        sender: 'bot' 
      }]);
      return;
    }

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setMessages(prev => [...prev, { text: userMessage, sender: 'user' }]);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL_CLIENT_CHATBOT}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: userMessage,
          client_id: clientId
        })
      });

      if (response.ok) {
        const data = await response.json();
        const responseText = data.answer || 'Sorry, I couldn\'t process your request.';
        setMessages(prev => [...prev, { text: responseText, sender: 'bot' }]);
        
        // Log any errors from the API
        if (data.error) {
          console.log('API Error:', data.error);
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

  const handleQuickSuggestion = (suggestion) => {
    setInputMessage(suggestion);
  };

  return (
    <div className="database-chatbot-page">
      <header className="database-header">
        <h1 className="page-title">ASK ABOUT YOUR DATA</h1>
        <p>Get insights about your database, data sources, and analytics</p>
        
        {/* API Health Status */}
        {/* {apiHealth && (
          <div style={{ 
            marginTop: '10px', 
            padding: '5px 10px', 
            borderRadius: '5px',
            backgroundColor: apiHealth.status === 'healthy' ? '#d4edda' : '#f8d7da',
            color: apiHealth.status === 'healthy' ? '#155724' : '#721c24',
            fontSize: '0.8rem'
          }}>
            API Status: {apiHealth.status === 'healthy' ? 'Connected' : 'Disconnected'}
          </div>
        )} */}
      </header>
      
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 20px' }}>
        {messages.length === 0 && (
          <article className="welcome-card">
            <div className="quick-suggestion-bar">
              <div className="quick-suggestion" onClick={() => handleQuickSuggestion("How many risk findings does my data have?")}>
                How many risk findings does my data have?
              </div>
              {/* <div className="quick-suggestion" onClick={() => handleQuickSuggestion("Show me all data stores for my data")}>
                Show me all data stores for my data
              </div> */}
              <div className="quick-suggestion" onClick={() => handleQuickSuggestion("how much risk does my data contains?")}>
              how much risk does my data contains?
              </div>
              <div className="quick-suggestion" onClick={() => handleQuickSuggestion("provide me the sdes that my data contatin?")}>
                provide me the sdes that my data contatin?
              </div>
              <div className="quick-suggestion" onClick={() => handleQuickSuggestion("how many types of data i have?")}>
                how many types of data i have?
              </div>
            </div>
          </article>
        )}
        
        {messages.map((message, index) => (
          <article 
            key={index} 
            className={`message-bubble ${message.sender === 'user' ? 'user-message' : 'bot-message'}`}
          >
            {message.sender === 'bot' ? formatMessageText(message.text) : message.text}
          </article>
        ))}
        
        {isLoading && (
          <article className="message-bubble bot-message">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </article>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <footer className="database-input-section">
        <form onSubmit={handleSubmit} className="input-form">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask about your data, database, or analytics..."
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading || !inputMessage.trim()}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </form>
      </footer>
    </div>
  );
};

export default DatabaseChatbot; 