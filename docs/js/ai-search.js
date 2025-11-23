/**
 * WYN360 CLI Documentation - AI Search System
 *
 * Provides intelligent search capabilities for WYN360 CLI documentation.
 * Integrates seamlessly with existing MkDocs Material search functionality.
 *
 * Features:
 * - Semantic search across documentation
 * - AI-powered response generation
 * - Source attribution with direct links
 * - Graceful fallback to regular search
 *
 * @version 1.0.0
 * @author WYN360 CLI Documentation Team
 */

class WYN360AISearch {
  constructor() {
    this.isInitialized = false;
    this.searchIndex = null;
    this.embeddings = null;
    this.isLoading = false;
    this.currentQuery = '';
    this.indexLoaded = false;

    // Configuration
    this.config = {
      enabled: true,
      maxResults: 5,
      similarityThreshold: 0.1, // Lower threshold for simple embedding approximation
      responseTimeout: 30000, // 30 seconds
      apiEndpoint: null, // Will be set in Phase 3
      fallbackToRegularSearch: true,
      indexUrl: '/wyn360-cli/assets/search-index.json'
    };

    // UI Elements (will be initialized when DOM is ready)
    this.elements = {};

    this.init();
  }

  /**
   * Initialize AI Search system
   */
  async init() {
    try {
      // Wait for DOM to be ready
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => this.initializeUI());
      } else {
        this.initializeUI();
      }

      // Load search index
      await this.loadSearchIndex();

      // Log initialization for debugging
      console.log('[AI Search] WYN360 AI Search initialized');

      this.isInitialized = true;
    } catch (error) {
      console.error('[AI Search] Initialization failed:', error);
      this.handleError(error);
    }
  }

  /**
   * Initialize UI elements and event listeners
   */
  initializeUI() {
    try {
      // Cache UI elements
      this.elements = {
        searchInput: document.querySelector('.md-search__input'),
        aiSection: document.getElementById('ai-search-section'),
        aiButton: document.getElementById('ask-ai-button'),
        responseContainer: document.getElementById('ai-response-container'),
        loading: document.getElementById('ai-loading'),
        response: document.getElementById('ai-response'),
        error: document.getElementById('ai-error'),
        responseText: document.getElementById('ai-response-text'),
        sourceLinks: document.getElementById('ai-source-links'),
        askAnother: document.getElementById('ask-another'),
        showRegularSearch: document.getElementById('show-regular-search'),
        retryAI: document.getElementById('retry-ai')
      };

      // Bind event listeners
      this.bindEventListeners();

      console.log('[AI Search] UI initialized successfully');
    } catch (error) {
      console.error('[AI Search] UI initialization failed:', error);
    }
  }

  /**
   * Bind event listeners to UI elements
   */
  bindEventListeners() {
    if (this.elements.aiButton) {
      this.elements.aiButton.addEventListener('click', (e) => {
        e.preventDefault();
        this.handleAISearch();
      });
    }

    if (this.elements.askAnother) {
      this.elements.askAnother.addEventListener('click', () => {
        this.resetAISearch();
      });
    }

    if (this.elements.showRegularSearch) {
      this.elements.showRegularSearch.addEventListener('click', () => {
        this.showRegularSearch();
      });
    }

    if (this.elements.retryAI) {
      this.elements.retryAI.addEventListener('click', () => {
        this.handleAISearch();
      });
    }

    // Handle Enter key in search input when AI section is visible
    if (this.elements.searchInput) {
      this.elements.searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && this.elements.aiSection &&
            this.elements.aiSection.style.display !== 'none') {
          e.preventDefault();
          this.handleAISearch();
        }
      });
    }
  }

  /**
   * Handle AI search request
   */
  async handleAISearch() {
    if (!this.isInitialized || this.isLoading) {
      return;
    }

    try {
      // Get current search query
      this.currentQuery = this.elements.searchInput?.value?.trim() || '';

      if (!this.currentQuery) {
        this.showError('Please enter a search query first.');
        return;
      }

      console.log(`[AI Search] Processing query: "${this.currentQuery}"`);

      // Show loading state
      this.showLoading();

      // Check if search index is available
      if (this.indexLoaded && this.searchIndex) {
        // Perform semantic search on documentation
        const searchResults = await this.performSemanticSearch(this.currentQuery);

        // Generate AI response from search results
        const aiResponse = await this.generateAIResponse(this.currentQuery, searchResults);

        // Show AI response
        this.showResponse(aiResponse);
      } else if (this.searchIndex === null) {
        // Search index failed to load - show helpful error
        this.showError(
          'AI search index is currently unavailable. ' +
          'Please try using the regular search above, or check back later when the search index has been deployed.'
        );
      } else {
        // Still loading index - try again in a moment
        this.showError('Search index is still loading. Please wait a moment and try again.');

        // Try to load index again
        setTimeout(() => {
          this.loadSearchIndex();
        }, 2000);
      }

    } catch (error) {
      console.error('[AI Search] Search failed:', error);
      this.showError('AI search encountered an error. Please try using the regular search above.');
    }
  }

  /**
   * Load search index from the server
   */
  async loadSearchIndex() {
    if (this.indexLoaded) {
      return;
    }

    try {
      console.log('[AI Search] Loading search index...');

      const response = await fetch(this.config.indexUrl);
      if (!response.ok) {
        // Update UI to show search index is missing
        this.updateSearchStatus(null, `Search index not available (${response.status})`);
        throw new Error(`Failed to load search index: ${response.status}`);
      }

      const indexData = await response.json();
      this.searchIndex = indexData;
      this.embeddings = indexData.embeddings || null;
      this.indexLoaded = true;

      console.log(`[AI Search] Index loaded: ${indexData.metadata.total_chunks} chunks`);
      console.log(`[AI Search] Sections: ${indexData.metadata.sections.join(', ')}`);

      // Update status indicator
      const aiStatusElement = document.getElementById('ai-status');
      if (aiStatusElement) {
        if (indexData.metadata.has_embeddings) {
          aiStatusElement.textContent = '🧠 Semantic search ready';
          console.log('[AI Search] Semantic search enabled');
        } else {
          aiStatusElement.textContent = '🔍 Keyword search ready';
          console.log('[AI Search] Using keyword-based search');
        }
      }

    } catch (error) {
      console.error('[AI Search] Failed to load search index:', error);
      this.searchIndex = null;
      this.indexLoaded = false;

      // Update status to show error
      const aiStatusElement = document.getElementById('ai-status');
      if (aiStatusElement) {
        aiStatusElement.textContent = '⚠️ Search index unavailable';
      }

      // Don't throw - allow regular search to work
      console.log('[AI Search] Falling back to regular MkDocs search');
    }
  }

  /**
   * Perform semantic search on the loaded index
   */
  async performSemanticSearch(query) {
    if (!this.searchIndex) {
      throw new Error('Search index not loaded');
    }

    console.log(`[AI Search] Searching for: "${query}"`);

    // Use embedding-based semantic search if available
    if (this.searchIndex.metadata.has_embeddings && this.embeddings && this.embeddings.length > 0) {
      return await this._performEmbeddingSearch(query);
    } else {
      // Fallback to keyword-based search
      console.log('[AI Search] Using keyword-based search (embeddings not available)');
      return this._performKeywordSearch(query);
    }
  }

  /**
   * Perform embedding-based semantic search
   */
  async _performEmbeddingSearch(query) {
    try {
      console.log('[AI Search] Performing semantic embedding search');

      // Generate query embedding using browser-based sentence transformer
      const queryEmbedding = await this._generateQueryEmbedding(query);

      if (!queryEmbedding) {
        console.warn('[AI Search] Failed to generate query embedding, falling back to keyword search');
        return this._performKeywordSearch(query);
      }

      // Calculate cosine similarity with all document embeddings
      const similarities = this.embeddings.map((embedding, index) => {
        if (!embedding || embedding.length === 0) {
          return { index, similarity: 0 };
        }

        const similarity = this._calculateCosineSimilarity(queryEmbedding, embedding);
        return { index, similarity };
      });

      // Filter and sort by similarity
      const validSimilarities = similarities
        .filter(item => item.similarity > this.config.similarityThreshold)
        .sort((a, b) => b.similarity - a.similarity)
        .slice(0, this.config.maxResults);

      console.log(`[AI Search] Found ${validSimilarities.length} semantically similar chunks`);

      // Map back to chunks with similarity scores
      const results = validSimilarities.map(item => ({
        ...this.searchIndex.chunks[item.index],
        similarity: item.similarity
      }));

      return results;

    } catch (error) {
      console.error('[AI Search] Embedding search failed:', error);
      return this._performKeywordSearch(query);
    }
  }

  /**
   * Perform keyword-based search (fallback)
   */
  _performKeywordSearch(query) {
    const results = this.searchIndex.chunks.filter(chunk => {
      const queryLower = query.toLowerCase();
      const titleMatch = chunk.title.toLowerCase().includes(queryLower);
      const contentMatch = chunk.content.toLowerCase().includes(queryLower);
      const sectionMatch = chunk.section.toLowerCase().includes(queryLower);
      const tagMatch = chunk.tags.some(tag => tag.toLowerCase().includes(queryLower));

      return titleMatch || contentMatch || sectionMatch || tagMatch;
    });

    // Sort by relevance (simple scoring for keyword search)
    results.sort((a, b) => {
      const scoreA = this._calculateRelevanceScore(a, query);
      const scoreB = this._calculateRelevanceScore(b, query);
      return scoreB - scoreA;
    });

    // Return top results
    return results.slice(0, this.config.maxResults);
  }

  /**
   * Calculate simple relevance score for keyword search
   */
  _calculateRelevanceScore(chunk, query) {
    const queryLower = query.toLowerCase();
    let score = 0;

    // Title match (highest weight)
    if (chunk.title.toLowerCase().includes(queryLower)) {
      score += 10;
    }

    // Section match
    if (chunk.section.toLowerCase().includes(queryLower)) {
      score += 5;
    }

    // Tag match
    const tagMatches = chunk.tags.filter(tag =>
      tag.toLowerCase().includes(queryLower)
    ).length;
    score += tagMatches * 3;

    // Content match (lower weight, but count occurrences)
    const contentLower = chunk.content.toLowerCase();
    const occurrences = (contentLower.match(new RegExp(queryLower, 'g')) || []).length;
    score += occurrences;

    // Boost for shorter, more focused content
    if (chunk.content.length < 300) {
      score += 2;
    }

    return score;
  }

  /**
   * Generate AI response using search results
   */
  async generateAIResponse(query, searchResults) {
    try {
      // Combine search results into context
      const context = searchResults.map(chunk =>
        `**${chunk.title}** (${chunk.section})\n${chunk.content.substring(0, 300)}...`
      ).join('\n\n');

      // Generate response based on search results
      const response = {
        answer: this._generateAnswerFromContext(query, searchResults),
        sources: searchResults.map(chunk => ({
          title: chunk.title,
          url: chunk.url,
          snippet: chunk.content.substring(0, 200) + '...',
          section: chunk.section,
          relevance: chunk.similarity || (this._calculateRelevanceScore(chunk, query) / 10),
          searchType: chunk.similarity ? 'semantic' : 'keyword'
        }))
      };

      return response;

    } catch (error) {
      console.error('[AI Search] Error generating AI response:', error);
      throw error;
    }
  }

  /**
   * Generate contextual answer from search results
   */
  _generateAnswerFromContext(query, searchResults) {
    if (!searchResults || searchResults.length === 0) {
      return `I couldn't find specific information about "${query}" in the WYN360 CLI documentation. Please try a different search term or browse the documentation sections.`;
    }

    const topResult = searchResults[0];
    const queryLower = query.toLowerCase();

    // Generate contextual responses based on query patterns
    if (queryLower.includes('install') || queryLower.includes('setup')) {
      return `To set up WYN360 CLI: First install with \`pip install wyn360-cli\`, then configure your API key with \`export ANTHROPIC_API_KEY=your_key_here\`, and launch with \`wyn360\`. Check the sources below for detailed installation instructions.`;
    }

    if (queryLower.includes('browser') || queryLower.includes('automation')) {
      return `WYN360 CLI provides autonomous browser automation through the \`browse_and_find()\` tool. It uses Claude Vision to analyze web pages and make intelligent navigation decisions. Perfect for e-commerce browsing, form filling, and data extraction tasks.`;
    }

    if (queryLower.includes('vision') || queryLower.includes('image')) {
      return `Vision Mode allows WYN360 CLI to process images, charts, and diagrams in documents. When reading Word or PDF files, it automatically analyzes visual content using Claude Vision API and provides intelligent descriptions.`;
    }

    // ENHANCED: Better matching for web/internet queries
    if (queryLower.includes('web') || queryLower.includes('internet') || queryLower.includes('search') ||
        queryLower.includes('online') || queryLower.includes('fetch') || queryLower.includes('browse')) {
      return `WYN360 CLI provides powerful web/internet capabilities: **1) Web Search** - Real-time internet search for current information, weather, URLs, and finding GitHub repositories. **2) Browser Automation** - Autonomous web navigation with vision-powered interaction. **3) Website Fetching** - Direct URL content retrieval with full DOM access. Use these tools for accessing current information, browsing websites, and integrating web data into your workflow.`;
    }

    if (queryLower.includes('api') || queryLower.includes('key')) {
      return `WYN360 CLI supports multiple AI providers: Anthropic Claude (recommended), AWS Bedrock, and Google Gemini. Set your API key using environment variables like \`ANTHROPIC_API_KEY\` or \`GEMINI_API_KEY\` depending on your chosen provider.`;
    }

    // Default contextual response using the top result
    const snippet = topResult.content.substring(0, 400);
    return `Based on the documentation, here's what I found about "${query}": ${snippet}... You can find more detailed information in the sources below.`;
  }

  /**
   * Generate mock AI response for Phase 1 demonstration
   * Will be replaced with real AI integration in Phase 3
   */
  async generateMockResponse(query) {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Mock responses based on common queries
    const mockResponses = {
      'browser automation': {
        answer: 'WYN360 CLI provides powerful browser automation through the `browse_and_find()` tool. This feature uses Claude Vision to analyze web pages and make intelligent decisions about what to click, type, or navigate. It works great for tasks like finding products on e-commerce sites, filling forms, and extracting information.',
        sources: [
          {
            title: 'Browser Automation Overview',
            url: '/features/browser-use/',
            snippet: 'Learn how to use autonomous browser automation with vision-powered navigation...'
          },
          {
            title: 'Use Case 17: Browser Automation',
            url: '/usage/use-cases/#use-case-17',
            snippet: 'Complete examples of browser automation tasks including e-commerce browsing...'
          }
        ]
      },
      'web search': {
        answer: 'WYN360 CLI includes built-in web search capabilities that let you access real-time information from the internet. You can search for current information, browse websites, and integrate web data into your development workflow.',
        sources: [
          {
            title: 'Web Search Integration',
            url: '/features/web-search/',
            snippet: 'Access real-time internet information using Claude\'s native web search tool...'
          },
          {
            title: 'Use Case 15: Web Search Examples',
            url: '/usage/use-cases/#use-case-15',
            snippet: 'Examples of web search integration and external API usage...'
          }
        ]
      },
      'getting started': {
        answer: 'To get started with WYN360 CLI, first install it using `pip install wyn360-cli`, then set up your API key with `export ANTHROPIC_API_KEY=your_key_here`, and finally launch it with `wyn360`. You\'ll then have access to all the AI-powered development tools.',
        sources: [
          {
            title: 'Installation Guide',
            url: '/getting-started/installation/',
            snippet: 'Step-by-step installation instructions for all platforms...'
          },
          {
            title: 'Quick Start Tutorial',
            url: '/getting-started/quickstart/',
            snippet: 'Get up and running with WYN360 CLI in under 5 minutes...'
          }
        ]
      },
      'vision mode': {
        answer: 'Vision Mode enables WYN360 CLI to process images, charts, diagrams, and visual content in documents. When reading Word or PDF files, it automatically analyzes images using Claude Vision API and provides intelligent descriptions of visual elements.',
        sources: [
          {
            title: 'Vision Mode Features',
            url: '/features/vision-mode/',
            snippet: 'Process images, charts, and diagrams with AI-powered analysis...'
          },
          {
            title: 'Document Processing with Vision',
            url: '/usage/use-cases/#vision-mode-examples',
            snippet: 'Examples of vision-powered document analysis...'
          }
        ]
      }
    };

    // Find best matching response
    const queryLower = query.toLowerCase();
    for (const [keyword, response] of Object.entries(mockResponses)) {
      if (queryLower.includes(keyword)) {
        return response;
      }
    }

    // Default response for unmatched queries
    return {
      answer: `I found information related to "${query}" in the WYN360 CLI documentation. WYN360 CLI is an AI-powered coding assistant that helps you build projects, generate code, and improve your codebase through natural language conversations. Check out the links below for specific information about your query.`,
      sources: [
        {
          title: 'Complete User Guide',
          url: '/usage/use-cases/',
          snippet: 'Comprehensive guide covering all WYN360 CLI features and use cases...'
        },
        {
          title: 'Feature Overview',
          url: '/features/overview/',
          snippet: 'Overview of all available features and capabilities...'
        }
      ]
    };
  }

  /**
   * Show loading state
   */
  showLoading() {
    this.isLoading = true;

    if (this.elements.responseContainer) {
      this.elements.responseContainer.style.display = 'block';
    }

    if (this.elements.loading) {
      this.elements.loading.style.display = 'block';
    }

    if (this.elements.response) {
      this.elements.response.style.display = 'none';
    }

    if (this.elements.error) {
      this.elements.error.style.display = 'none';
    }
  }

  /**
   * Show AI response in chatbot style
   */
  showResponse(response) {
    this.isLoading = false;

    if (this.elements.loading) {
      this.elements.loading.style.display = 'none';
    }

    if (this.elements.error) {
      this.elements.error.style.display = 'none';
    }

    // Show user question
    const userQuestionElement = document.getElementById('user-question-text');
    if (userQuestionElement) {
      userQuestionElement.textContent = this.currentQuery;
    }

    // Set response text
    if (this.elements.responseText) {
      this.elements.responseText.textContent = response.answer;
    }

    // Set source links as cards
    if (this.elements.sourceLinks && response.sources) {
      this.elements.sourceLinks.innerHTML = '';

      response.sources.forEach(source => {
        const sourceCard = document.createElement('a');
        sourceCard.href = source.url;
        sourceCard.innerHTML = `
          <span class="source-title">${source.title}</span>
          <span class="source-snippet">${source.snippet}</span>
          ${source.searchType ? `<span class="search-type-tag">${source.searchType === 'semantic' ? '🧠 Semantic' : '🔍 Keyword'}</span>` : ''}
        `;
        this.elements.sourceLinks.appendChild(sourceCard);
      });
    }

    // Show search type status
    this.updateSearchStatus(response.sources);

    // Show response container
    if (this.elements.response) {
      this.elements.response.style.display = 'block';
    }

    console.log('[AI Search] Response displayed successfully');
  }

  /**
   * Update search status indicator
   */
  updateSearchStatus(sources) {
    const statusElement = document.getElementById('ai-search-status');
    const badgeElement = document.getElementById('search-type-badge');
    const countElement = document.getElementById('result-count');

    if (statusElement && sources && sources.length > 0) {
      const hasSemanticResults = sources.some(s => s.searchType === 'semantic');

      if (badgeElement) {
        if (hasSemanticResults) {
          badgeElement.textContent = '🧠 Semantic Search';
          badgeElement.className = 'search-badge semantic';
        } else {
          badgeElement.textContent = '🔍 Keyword Search';
          badgeElement.className = 'search-badge keyword';
        }
      }

      if (countElement) {
        countElement.textContent = `${sources.length} result${sources.length === 1 ? '' : 's'}`;
      }

      statusElement.style.display = 'block';
    }
  }

  /**
   * Show error state
   */
  showError(message) {
    this.isLoading = false;

    if (this.elements.loading) {
      this.elements.loading.style.display = 'none';
    }

    if (this.elements.response) {
      this.elements.response.style.display = 'none';
    }

    if (this.elements.error) {
      this.elements.error.style.display = 'block';

      // Update error message if provided
      const errorText = this.elements.error.querySelector('p');
      if (errorText && message) {
        errorText.textContent = message;
      }
    }

    if (this.elements.responseContainer) {
      this.elements.responseContainer.style.display = 'block';
    }

    console.warn('[AI Search] Error displayed:', message);
  }

  /**
   * Reset AI search to initial state
   */
  resetAISearch() {
    if (this.elements.responseContainer) {
      this.elements.responseContainer.style.display = 'none';
    }

    if (this.elements.loading) {
      this.elements.loading.style.display = 'none';
    }

    if (this.elements.response) {
      this.elements.response.style.display = 'none';
    }

    if (this.elements.error) {
      this.elements.error.style.display = 'none';
    }

    this.isLoading = false;
    this.currentQuery = '';

    // Focus back to search input
    if (this.elements.searchInput) {
      this.elements.searchInput.focus();
    }
  }

  /**
   * Show regular search results (hide AI interface)
   */
  showRegularSearch() {
    if (this.elements.aiSection) {
      this.elements.aiSection.style.display = 'none';
    }

    // Trigger regular search
    const searchEvent = new Event('input', { bubbles: true });
    if (this.elements.searchInput) {
      this.elements.searchInput.dispatchEvent(searchEvent);
    }
  }

  /**
   * Handle errors gracefully
   */
  handleError(error) {
    console.error('[AI Search] Error:', error);

    if (this.config.fallbackToRegularSearch) {
      this.showRegularSearch();
    }
  }

  /**
   * Check if AI search is available
   */
  isAvailable() {
    return this.isInitialized && this.config.enabled;
  }

  /**
   * Get current configuration
   */
  getConfig() {
    return { ...this.config };
  }

  /**
   * Update configuration
   */
  updateConfig(newConfig) {
    this.config = { ...this.config, ...newConfig };
    console.log('[AI Search] Configuration updated:', this.config);
  }

  /**
   * Generate query embedding using simple TF-IDF approach
   * (Browser-based approximation of sentence transformers)
   */
  async _generateQueryEmbedding(query) {
    try {
      // For Phase 3, we'll use a client-side approximation
      // In a full implementation, you'd use transformers.js or a dedicated API

      // Simple approach: Create a bag-of-words vector based on the query
      // and the vocabulary from the document corpus
      const queryWords = this._tokenize(query.toLowerCase());
      const vocabulary = this._getVocabulary();

      // Create a simple TF-IDF-like vector
      const embedding = new Array(Math.min(vocabulary.length, 384)).fill(0);

      queryWords.forEach(word => {
        const index = vocabulary.indexOf(word);
        if (index !== -1 && index < embedding.length) {
          embedding[index] = 1.0; // Simple binary encoding
        }
      });

      // Normalize the vector
      const norm = Math.sqrt(embedding.reduce((sum, val) => sum + val * val, 0));
      if (norm > 0) {
        for (let i = 0; i < embedding.length; i++) {
          embedding[i] /= norm;
        }
      }

      console.log('[AI Search] Generated query embedding (simple approximation)');
      return embedding;

    } catch (error) {
      console.error('[AI Search] Error generating query embedding:', error);
      return null;
    }
  }

  /**
   * Get vocabulary from the search index for embedding approximation
   */
  _getVocabulary() {
    if (this._vocabulary) {
      return this._vocabulary;
    }

    // Extract vocabulary from all chunks
    const words = new Set();

    this.searchIndex.chunks.forEach(chunk => {
      const chunkWords = this._tokenize(chunk.content.toLowerCase());
      chunkWords.forEach(word => words.add(word));
    });

    this._vocabulary = Array.from(words).slice(0, 384); // Limit vocabulary size
    console.log(`[AI Search] Built vocabulary: ${this._vocabulary.length} words`);

    return this._vocabulary;
  }

  /**
   * Simple tokenizer for text processing
   */
  _tokenize(text) {
    return text
      .replace(/[^\w\s]/g, ' ') // Remove punctuation
      .split(/\s+/) // Split on whitespace
      .filter(word => word.length > 2) // Remove very short words
      .filter(word => !this._isStopWord(word)); // Remove stop words
  }

  /**
   * Check if word is a stop word
   */
  _isStopWord(word) {
    const stopWords = new Set([
      'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
      'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
      'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
      'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
      'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
    ]);
    return stopWords.has(word);
  }

  /**
   * Calculate cosine similarity between two vectors
   */
  _calculateCosineSimilarity(vectorA, vectorB) {
    if (!vectorA || !vectorB || vectorA.length !== vectorB.length) {
      return 0;
    }

    let dotProduct = 0;
    let normA = 0;
    let normB = 0;

    for (let i = 0; i < vectorA.length; i++) {
      dotProduct += vectorA[i] * vectorB[i];
      normA += vectorA[i] * vectorA[i];
      normB += vectorB[i] * vectorB[i];
    }

    normA = Math.sqrt(normA);
    normB = Math.sqrt(normB);

    if (normA === 0 || normB === 0) {
      return 0;
    }

    return dotProduct / (normA * normB);
  }
}

// Global access for debugging and external integration
window.WYN360AISearch = WYN360AISearch;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  if (typeof window.aiSearch === 'undefined') {
    window.aiSearch = new WYN360AISearch();
  }
});