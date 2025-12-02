import React, { useState, useEffect, useCallback } from 'react';

interface SearchResult {
  title: string;
  content: string;
  url: string;
  score?: number;
}

interface ChatMessage {
  type: 'user' | 'ai';
  content: string;
  results?: SearchResult[];
}

export default function AISearch(): JSX.Element {
  const [isVisible, setIsVisible] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [searchIndex, setSearchIndex] = useState<any>(null);
  const [embeddings, setEmbeddings] = useState<any>(null);

  // Load search index on component mount
  useEffect(() => {
    loadSearchIndex();
  }, []);

  // Add keyboard shortcut for Cmd+K / Ctrl+K to open search
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
        event.preventDefault();
        setIsVisible(true);
        // Focus the search input after opening
        setTimeout(() => {
          const searchInput = document.querySelector('.ai-search-input') as HTMLInputElement;
          if (searchInput) {
            searchInput.focus();
          }
        }, 100);
      }
      // ESC to close
      if (event.key === 'Escape' && isVisible) {
        setIsVisible(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isVisible]);

  const loadSearchIndex = async () => {
    try {
      const response = await fetch('/wyn360-cli/assets/search-index.json');
      if (response.ok) {
        const data = await response.json();
        setSearchIndex(data.chunks || []);
        setEmbeddings(data.embeddings || []);
        console.log('Search index loaded:', data.chunks?.length || 0, 'chunks');
      } else {
        console.warn('Search index not found, AI search disabled');
      }
    } catch (error) {
      console.warn('Failed to load search index:', error);
    }
  };

  const performSemanticSearch = useCallback(async (searchQuery: string): Promise<SearchResult[]> => {
    if (!searchIndex || !embeddings) {
      return performKeywordSearch(searchQuery);
    }

    try {
      // For now, fallback to keyword search
      // In a full implementation, you would use transformers.js here
      console.log('Performing semantic search for:', searchQuery);
      return performKeywordSearch(searchQuery);
    } catch (error) {
      console.warn('Semantic search failed, falling back to keyword search:', error);
      return performKeywordSearch(searchQuery);
    }
  }, [searchIndex, embeddings]);

  const performKeywordSearch = (searchQuery: string): SearchResult[] => {
    if (!searchIndex) return [];

    const queryWords = searchQuery.toLowerCase().split(' ');
    const results: SearchResult[] = [];

    searchIndex.forEach((chunk: any) => {
      const content = chunk.content?.toLowerCase() || '';
      const title = chunk.metadata?.title || chunk.title || 'Untitled';
      let score = 0;

      // Calculate relevance score
      queryWords.forEach(word => {
        if (content.includes(word)) {
          score += 1;
          if (title.toLowerCase().includes(word)) {
            score += 2; // Title matches are more important
          }
        }
      });

      if (score > 0) {
        results.push({
          title,
          content: chunk.content?.substring(0, 200) + '...' || '',
          url: chunk.url || '#',
          score
        });
      }
    });

    // Sort by score and return top results
    return results
      .sort((a, b) => (b.score || 0) - (a.score || 0))
      .slice(0, 6);
  };

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsLoading(true);
    const userMessage: ChatMessage = { type: 'user', content: query };
    setMessages(prev => [...prev, userMessage]);

    try {
      const results = await performSemanticSearch(query);

      const aiMessage: ChatMessage = {
        type: 'ai',
        content: results.length > 0
          ? `I found ${results.length} relevant documentation sections for "${query}":`
          : `No specific results found for "${query}". Try different keywords or browse the documentation sections.`,
        results
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage: ChatMessage = {
        type: 'ai',
        content: 'Sorry, I encountered an error while searching. Please try again or use the regular search.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setQuery('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const toggleVisibility = () => {
    setIsVisible(!isVisible);
    if (!isVisible) {
      setMessages([]);
    }
  };

  return (
    <div className="ai-search-section">
      <div className="ai-search-trigger">
        <button
          className="ai-search-button"
          onClick={toggleVisibility}
          aria-label="Toggle AI Search"
        >
          🤖 Ask AI about WYN360 CLI
          <kbd style={{
            fontSize: '0.7rem',
            marginLeft: '0.5rem',
            padding: '0.1rem 0.3rem',
            background: 'rgba(255,255,255,0.2)',
            borderRadius: '3px'
          }}>
            ⌘K
          </kbd>
        </button>
      </div>

      {isVisible && (
        <div className="ai-search-chat">
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', padding: '1rem', color: 'var(--ifm-color-emphasis-600)' }}>
              <p>Ask me anything about WYN360 CLI! I'll search the documentation for you.</p>
            </div>
          )}

          {messages.map((message, index) => (
            <div key={index} className={`chat-message ${message.type}`}>
              <div>{message.content}</div>
              {message.results && message.results.length > 0 && (
                <div style={{ marginTop: '1rem' }}>
                  {message.results.map((result, resultIndex) => (
                    <div key={resultIndex} className="source-card">
                      <h4>
                        <a href={result.url} style={{ textDecoration: 'none' }}>
                          {result.title}
                        </a>
                      </h4>
                      <p>{result.content}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="ai-loading">
              <div className="spinner"></div>
              <span>Searching documentation...</span>
            </div>
          )}

          <div style={{
            display: 'flex',
            gap: '0.5rem',
            marginTop: '1rem',
            borderTop: '1px solid var(--ifm-color-emphasis-300)',
            paddingTop: '1rem'
          }}>
            <input
              type="text"
              className="ai-search-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about installation, features, usage... (⌘K to open)"
              style={{
                flex: 1,
                padding: '0.5rem',
                border: '1px solid var(--ifm-color-emphasis-300)',
                borderRadius: '4px',
                background: 'var(--ifm-background-color)',
                color: 'var(--ifm-color-content)'
              }}
              disabled={isLoading}
            />
            <button
              onClick={handleSearch}
              disabled={isLoading || !query.trim()}
              style={{
                padding: '0.5rem 1rem',
                background: 'var(--ifm-color-primary)',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                opacity: isLoading || !query.trim() ? 0.6 : 1
              }}
            >
              Search
            </button>
          </div>
        </div>
      )}
    </div>
  );
}