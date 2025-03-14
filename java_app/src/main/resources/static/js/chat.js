$(document).ready(function() {
    // Initialize variables
    let chatHistory = [];
    let attachedFiles = [];
    let isGenerating = false;
    
    // Configure marked.js
    marked.setOptions({
        highlight: function(code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                return hljs.highlight(code, { language: lang }).value;
            }
            return hljs.highlightAuto(code).value;
        },
        breaks: true
    });
    
    // Event handlers
    $('#temperatureRange').on('input', function() {
        $('#temperatureValue').text($(this).val());
    });
    
    $('#newChatBtn').click(function() {
        if (isGenerating) {
            if (!confirm('A response is being generated. Are you sure you want to start a new chat?')) {
                return;
            }
        }
        
        clearChat();
    });
    
    $('#clearChatBtn').click(function() {
        if (chatHistory.length > 0) {
            if (confirm('Are you sure you want to clear the chat history?')) {
                clearChat();
            }
        }
    });
    
    $('#saveChatBtn').click(function() {
        if (chatHistory.length === 0) {
            alert('There is no chat to save.');
            return;
        }
        
        const chatData = {
            messages: chatHistory,
            model: $('#modelSelect').val(),
            timestamp: new Date().toISOString(),
            settings: {
                temperature: parseFloat($('#temperatureRange').val()),
                maxTokens: parseInt($('#maxTokensInput').val()),
                systemPrompt: $('#systemPromptInput').val()
            }
        };
        
        // Create a Blob and download it
        const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ollama-chat-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });
    
    $('#sendBtn').click(sendMessage);
    
    $('#userInput').keydown(function(e) {
        if (e.ctrlKey && e.keyCode === 13) {
            sendMessage();
        }
    });
    
    $('#testConnectionBtn').click(function() {
        const apiUrl = $('#apiUrlInput').val();
        
        $(this).prop('disabled', true);
        $(this).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Testing...');
        
        $.ajax({
            url: '/api/models',
            type: 'GET',
            success: function(data) {
                alert('Connection successful! Found ' + data.length + ' models.');
                
                // Update model select
                $('#modelSelect').empty();
                $('#modelSelect').append('<option value="">Select a model</option>');
                
                data.forEach(function(model) {
                    $('#modelSelect').append(`<option value="${model.name}">${model.name}</option>`);
                });
            },
            error: function(xhr, status, error) {
                alert('Connection failed: ' + error);
            },
            complete: function() {
                $('#testConnectionBtn').prop('disabled', false);
                $('#testConnectionBtn').html('Test Connection');
            }
        });
    });
    
    $('#codeSnippetBtn').click(function() {
        const snippet = '```python\n# Your code here\n```';
        const userInput = $('#userInput');
        const cursorPos = userInput.prop('selectionStart');
        const textBefore = userInput.val().substring(0, cursorPos);
        const textAfter = userInput.val().substring(cursorPos);
        
        userInput.val(textBefore + snippet + textAfter);
        userInput.focus();
    });
    
    $('#attachFileBtn').click(function() {
        // Create a file input element
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.txt,.js,.py,.java,.html,.css,.json,.md';
        
        fileInput.onchange = function(e) {
            const file = e.target.files[0];
            if (!file) return;
            
            // Check file size (limit to 100KB)
            if (file.size > 100 * 1024) {
                alert('File is too large. Maximum size is 100KB.');
                return;
            }
            
            const reader = new FileReader();
            reader.onload = function(e) {
                const fileContent = e.target.result;
                
                // Add to attachments
                attachedFiles.push({
                    name: file.name,
                    content: fileContent
                });
                
                // Update UI
                updateAttachments();
            };
            
            reader.readAsText(file);
        };
        
        fileInput.click();
    });
    
    $('#clearAttachmentsBtn').click(function() {
        attachedFiles = [];
        updateAttachments();
    });
    
    // Functions
    function clearChat() {
        chatHistory = [];
        $('#chatContainer').empty();
        addSystemMessage('Welcome to Ollama Chat! Select a model to start chatting.');
    }
    
    function updateAttachments() {
        const container = $('#attachmentsContainer');
        const list = $('#attachmentsList');
        
        if (attachedFiles.length === 0) {
            container.addClass('d-none');
            return;
        }
        
        list.empty();
        attachedFiles.forEach(function(file, index) {
            const item = $(`
                <li class="list-group-item attachment-item">
                    <div>
                        <i class="fas fa-file-alt me-2"></i>
                        <span>${file.name}</span>
                        <small class="text-muted">(${Math.round(file.content.length / 1024 * 10) / 10} KB)</small>
                    </div>
                    <button class="btn btn-sm btn-outline-danger remove-attachment" data-index="${index}">
                        <i class="fas fa-times"></i>
                    </button>
                </li>
            `);
            
            list.append(item);
        });
        
        container.removeClass('d-none');
        
        // Add event handlers for remove buttons
        $('.remove-attachment').click(function() {
            const index = $(this).data('index');
            attachedFiles.splice(index, 1);
            updateAttachments();
        });
    }
    
    function sendMessage() {
        if (isGenerating) return;
        
        const userInput = $('#userInput');
        const message = userInput.val().trim();
        
        if (!message && attachedFiles.length === 0) return;
        
        const model = $('#modelSelect').val();
        if (!model) {
            alert('Please select a model first.');
            return;
        }
        
        // Add user message to chat
        if (message) {
            addUserMessage(message);
            chatHistory.push({ role: 'user', content: message });
        }
        
        // Clear input
        userInput.val('');
        
        // Prepare messages array
        const messages = [];
        
        // Add system message
        const systemPrompt = $('#systemPromptInput').val().trim();
        if (systemPrompt) {
            messages.push({ role: 'system', content: systemPrompt });
        }
        
        // Add reasoning instruction if checked
        if ($('#reasoningCheck').is(':checked')) {
            messages.push({ 
                role: 'system', 
                content: 'Please think step by step and show your reasoning before providing the final answer.' 
            });
        }
        
        // Add file content if any files are attached
        if (attachedFiles.length > 0) {
            let fileContent = 'I\'m attaching the following files for reference:\n\n';
            
            attachedFiles.forEach(function(file) {
                fileContent += `File: ${file.name}\n\n${file.content}\n\n`;
            });
            
            messages.push({ role: 'user', content: fileContent });
            chatHistory.push({ role: 'user', content: fileContent });
            
            // Add a system message to indicate files were attached
            addSystemMessage(`Attached ${attachedFiles.length} file(s) to the conversation.`);
        }
        
        // Add chat history
        chatHistory.forEach(function(msg) {
            messages.push(msg);
        });
        
        // Show loading indicator
        isGenerating = true;
        $('#sendBtn').prop('disabled', true);
        $('#sendBtn').html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...');
        
        const loadingIndicator = $(`
            <div class="loading-indicator">
                <div class="spinner-border text-primary" role="status"></div>
                <span>Generating response...</span>
            </div>
        `);
        
        $('#chatContainer').append(loadingIndicator);
        scrollToBottom();
        
        // Send to API
        $.ajax({
            url: '/api/chat',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                model: model,
                messages: messages,
                options: {
                    temperature: parseFloat($('#temperatureRange').val()),
                    num_predict: parseInt($('#maxTokensInput').val())
                }
            }),
            success: function(data) {
                // Remove loading indicator
                loadingIndicator.remove();
                
                if (data.error) {
                    addSystemMessage(`Error: ${data.error}`);
                } else if (data.message && data.message.content) {
                    addAssistantMessage(data.message.content);
                    chatHistory.push({ role: 'assistant', content: data.message.content });
                } else {
                    addSystemMessage('Error: Received empty response from model.');
                }
            },
            error: function(xhr, status, error) {
                // Remove loading indicator
                loadingIndicator.remove();
                
                let errorMessage = 'Failed to communicate with the server.';
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.error) {
                        errorMessage = response.error;
                    }
                } catch (e) {
                    console.error('Error parsing error response:', e);
                }
                
                addSystemMessage(`Error: ${errorMessage}`);
            },
            complete: function() {
                isGenerating = false;
                $('#sendBtn').prop('disabled', false);
                $('#sendBtn').html('<i class="fas fa-paper-plane me-1"></i>Send');
            }
        });
    }
    
    function addSystemMessage(text) {
        const message = $(`
            <div class="system-message">
                <div class="message-content">
                    <p>${text}</p>
                </div>
            </div>
        `);
        
        $('#chatContainer').append(message);
        scrollToBottom();
    }
    
    function addUserMessage(text) {
        const message = $(`
            <div class="message user-message">
                <div class="message-header">
                    <span>You</span>
                    <span>${new Date().toLocaleTimeString()}</span>
                </div>
                <div class="message-content">
                    <p>${text}</p>
                </div>
            </div>
        `);
        
        $('#chatContainer').append(message);
        scrollToBottom();
    }
    
    function addAssistantMessage(text) {
        // Process markdown and code blocks
        const htmlContent = marked.parse(text);
        
        const message = $(`
            <div class="message assistant-message">
                <div class="message-header">
                    <span>Assistant</span>
                    <span>${new Date().toLocaleTimeString()}</span>
                </div>
                <div class="message-content markdown-body">
                    ${htmlContent}
                </div>
            </div>
        `);
        
        $('#chatContainer').append(message);
        
        // Add copy buttons to code blocks
        message.find('pre code').each(function(i, block) {
            const codeBlock = $(block);
            const codeContent = codeBlock.text();
            
            const copyBtn = $(`
                <button class="btn btn-sm btn-outline-light position-absolute top-0 end-0 m-2 copy-code-btn">
                    <i class="fas fa-copy"></i>
                </button>
            `);
            
            // Wrap code block in a relative positioned div
            codeBlock.parent().wrap('<div class="position-relative"></div>');
            codeBlock.parent().parent().append(copyBtn);
            
            copyBtn.click(function() {
                navigator.clipboard.writeText(codeContent);
                $(this).html('<i class="fas fa-check"></i>');
                setTimeout(() => {
                    $(this).html('<i class="fas fa-copy"></i>');
                }, 2000);
            });
        });
        
        scrollToBottom();
    }
    
    function scrollToBottom() {
        const container = $('#chatContainer');
        container.scrollTop(container.prop('scrollHeight'));
    }
    
    // Initialize
    clearChat();
});