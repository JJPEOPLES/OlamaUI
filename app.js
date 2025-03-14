/**
 * Ollama Chat UI - JavaScript Implementation
 * A web interface for interacting with Ollama models
 */

// Import dependencies
const express = require('express');
const bodyParser = require('body-parser');
const path = require('path');
const axios = require('axios');
const morgan = require('morgan');
const { marked } = require('marked');
require('dotenv').config();

// Create Express app
const app = express();
const port = process.env.PORT || 3000;

// Configure Ollama API URL
const OLLAMA_API_URL = process.env.OLLAMA_API_URL || 'http://localhost:11434/api';

// Configure middleware
app.use(morgan('dev')); // Logging
app.use(bodyParser.json()); // Parse JSON request bodies
app.use(bodyParser.urlencoded({ extended: true })); // Parse URL-encoded request bodies
app.use(express.static(path.join(__dirname, 'public'))); // Serve static files

// Set up view engine
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'pug');

// Configure marked for markdown rendering
marked.setOptions({
  breaks: true, // Add <br> on single line breaks
  gfm: true, // GitHub Flavored Markdown
  headerIds: false, // Don't add IDs to headers
  mangle: false // Don't mangle email addresses
});

// Routes
app.get('/', (req, res) => {
  res.render('index', { title: 'Ollama Chat' });
});

// API Routes
// Get available models
app.get('/api/models', async (req, res) => {
  try {
    const response = await axios.get(`${OLLAMA_API_URL}/tags`);
    res.json(response.data);
  } catch (error) {
    console.error('Error fetching models:', error.message);
    res.status(500).json({ 
      error: 'Failed to fetch models',
      details: error.message
    });
  }
});

// Chat with a model
app.post('/api/chat', async (req, res) => {
  try {
    const { model, messages, options } = req.body;
    
    // Validate request
    if (!model) {
      return res.status(400).json({ error: 'Model is required' });
    }
    
    if (!messages || !Array.isArray(messages)) {
      return res.status(400).json({ error: 'Messages array is required' });
    }
    
    // Prepare request to Ollama
    const requestData = {
      model,
      messages,
      stream: false,
      options: options || {}
    };
    
    // Send request to Ollama
    const response = await axios.post(`${OLLAMA_API_URL}/chat`, requestData);
    
    // Process markdown in response
    if (response.data.message && response.data.message.content) {
      response.data.message.content_html = marked(response.data.message.content);
    }
    
    res.json(response.data);
  } catch (error) {
    console.error('Error in chat:', error.message);
    res.status(500).json({ 
      error: 'Failed to communicate with Ollama',
      details: error.message
    });
  }
});

// Get version info
app.get('/api/version', (req, res) => {
  res.json({
    version: '1.0.0',
    node_version: process.version,
    ollama_api_url: OLLAMA_API_URL
  });
});

// Start the server
app.listen(port, () => {
  console.log(`Ollama Chat JS is running at http://localhost:${port}`);
  console.log(`Using Ollama API at ${OLLAMA_API_URL}`);
});