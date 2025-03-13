document.addEventListener('DOMContentLoaded', () => {
  // DOM elements
  const modelSelector = document.getElementById('model-selector');
  const temperatureSlider = document.getElementById('temperature');
  const temperatureValue = document.getElementById('temperature-value');
  const maxTokensInput = document.getElementById('max-tokens');
  const systemPromptInput = document.getElementById('system-prompt');
  const chatForm = document.getElementById('chat-form');
  const userInput = document.getElementById('user-input');
  const chatMessages = document.getElementById('chat-messages');
  const sendButton = document.getElementById('send-button');
  
  // Chat state
  let chatHistory = [];
  let selectedModel = '';
  
  // Fetch available models
  async function fetchModels() {
    try {
      const response = await fetch('/api/models');
      const data = await response.json();
      
      // Clear loading option
      modelSelector.innerHTML = '';
      
      // Add default option
      const defaultOption = document.createElement('option');
      defaultOption.value = '';
      defaultOption.textContent = 'Select a model';
      defaultOption.disabled = true;
      defaultOption.selected = true;
      modelSelector.appendChild(defaultOption);
      
      // Add models from API
      if (data.models && data.models.length > 0) {
        data.models.forEach(model => {
          const option = document.createElement('option');
          option.value = model.name;
          option.textContent = model.name;
          modelSelector.appendChild(option);
        });
      } else {
        // If no models are available
        const noModelsOption = document.createElement('option');
        noModelsOption.value = '';
        noModelsOption.textContent = 'No models available';
        noModelsOption.disabled = true;
        modelSelector.appendChild(noModelsOption);
      }
    } catch (error) {
      console.error('Error fetching models:', error);
      modelSelector.innerHTML = '<option value="" disabled selected>Error loading models</option>';
      
      // Add system message about the error
      addMessageToUI('system', 'Error connecting to Ollama API. Make sure Ollama is running on your machine.');
    }
  }
  
  // Update temperature value display
  temperatureSlider.addEventListener('input', () => {
    temperatureValue.textContent = temperatureSlider.value;
  });
  
  // Handle model selection
  modelSelector.addEventListener('change', () => {
    selectedModel = modelSelector.value;
    
    // Add system message when model is selected
    if (selectedModel) {
      chatMessages.innerHTML = '';
      chatHistory = [];
      
      addMessageToUI('system', `Model <strong>${selectedModel}</strong> selected. Start chatting!`);
    }
  });
  
  // Handle form submission
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const userMessage = userInput.value.trim();
    
    // Validate input
    if (!userMessage) return;
    if (!selectedModel) {
      alert('Please select a model first');
      return;
    }
    
    // Add user message to UI
    addMessageToUI('user', userMessage);
    
    // Prepare messages array
    let messages = [];
    
    // Add system message if provided
    const systemPrompt = systemPromptInput.value.trim();
    if (systemPrompt) {
      messages.push({
        role: 'system',
        content: systemPrompt
      });
    }
    
    // Add chat history
    messages = messages.concat(chatHistory);
    
    // Add current user message
    messages.push({
      role: 'user',
      content: userMessage
    });
    
    // Update chat history (excluding system message)
    if (!chatHistory.some(msg => msg.role === 'user' && msg.content === userMessage)) {
      chatHistory.push({
        role: 'user',
        content: userMessage
      });
    }
    
    // Clear input
    userInput.value = '';
    
    // Disable send button and show loading
    sendButton.disabled = true;
    const originalButtonText = sendButton.innerHTML;
    sendButton.innerHTML = `
      <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      Thinking...
    `;
    
    try {
      // Send to API
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: selectedModel,
          messages: messages,
          options: {
            temperature: parseFloat(temperatureSlider.value),
            num_predict: parseInt(maxTokensInput.value)
          }
        })
      });
      
      const data = await response.json();
      
      // Add assistant response to UI
      if (data.message && data.message.content) {
        addMessageToUI('assistant', data.message.content);
        
        // Add to chat history
        chatHistory.push({
          role: 'assistant',
          content: data.message.content
        });
      } else if (data.error) {
        addMessageToUI('system', `Error: ${data.error}`);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      addMessageToUI('system', 'Error: Could not connect to the server');
    } finally {
      // Re-enable send button
      sendButton.disabled = false;
      sendButton.innerHTML = originalButtonText;
    }
  });
  
  // Add message to UI
  function addMessageToUI(role, content) {
    const messageDiv = document.createElement('div');
    
    // Set appropriate classes based on role
    let messageClasses = '';
    if (role === 'user') {
      messageClasses = 'ml-auto bg-primary-100 text-gray-800';
    } else if (role === 'assistant') {
      messageClasses = 'mr-auto bg-gray-100 text-gray-800';
    } else { // system
      messageClasses = 'mx-auto bg-gray-100 border border-gray-200 text-center';
    }
    
    messageDiv.className = `max-w-[80%] p-3 mb-4 rounded-lg ${messageClasses}`;
    
    // Process markdown-like formatting
    let formattedContent = content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/```([\s\S]*?)```/g, '<pre class="bg-gray-800 text-white p-3 rounded my-2 overflow-x-auto"><code>$1</code></pre>')
      .replace(/`(.*?)`/g, '<code class="bg-gray-200 px-1 rounded">$1</code>')
      .replace(/\n/g, '<br>');
    
    messageDiv.innerHTML = formattedContent;
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
  
  // Add keyboard shortcut (Ctrl+Enter to submit)
  userInput.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
      e.preventDefault();
      chatForm.dispatchEvent(new Event('submit'));
    }
  });
  
  // Initialize
  fetchModels();
});