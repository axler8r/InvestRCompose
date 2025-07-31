/**
 * Investment Research Agent - Main Application JavaScript
 * Handles chat functionality, message rendering, and UI interactions
 */

// DOM element references
const messagesContainer = document.getElementById('messages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const typingIndicator = document.getElementById('typingIndicator');

/**
 * Add a message to the chat interface
 * @param {string} content - The message content
 * @param {boolean} isUser - Whether the message is from the user
 * @param {string|null} timestamp - Optional timestamp
 * @param {Array} toolCalls - Array of tool call information
 * @param {Array} references - Array of reference URLs
 */
function addMessage(content, isUser = false, timestamp = null, toolCalls = [], references = []) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'agent'}`;
    
    const timeStr = timestamp ? new Date(timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
    
    // Render markdown for agent messages, plain text for user messages
    const messageContent = isUser ? content : marked.parse(content);
    
    let disclosureWidgets = '';
    
    // Add disclosure widgets for agent messages only
    if (!isUser && (references.length > 0 || toolCalls.length > 0)) {
        // References disclosure
        if (references.length > 0) {
            const referencesHtml = references.map(ref => 
                `<li><a href="${ref}" target="_blank" rel="noopener noreferrer">${ref}</a></li>`
            ).join('');
            
            disclosureWidgets += `
                <div class="disclosure-section">
                    <div class="disclosure-header" onclick="toggleDisclosure(this)">
                        <span class="icon">▶</span>
                        <span>📚 References (${references.length})</span>
                    </div>
                    <div class="disclosure-content">
                        <ul class="references-list">${referencesHtml}</ul>
                    </div>
                </div>
            `;
        }
        
        // Tool calls disclosure
        if (toolCalls.length > 0) {
            const toolCallsHtml = toolCalls.map(tool => {
                const statusClass = tool.success ? 'success' : 'error';
                const statusText = tool.success ? 'Success' : 'Failed';
                
                return `
                    <div class="tool-call">
                        <div class="tool-call-header">
                            <span class="tool-name">${tool.name}</span>
                            <span class="tool-status ${statusClass}">${statusText}</span>
                        </div>
                        <div class="tool-result">${tool.result}</div>
                        ${tool.execution_time_ms ? `<div class="tool-execution-time">Execution time: ${tool.execution_time_ms}ms</div>` : ''}
                    </div>
                `;
            }).join('');
            
            disclosureWidgets += `
                <div class="disclosure-section">
                    <div class="disclosure-header" onclick="toggleDisclosure(this)">
                        <span class="icon">▶</span>
                        <span>🔧 Tool Calls (${toolCalls.length})</span>
                    </div>
                    <div class="disclosure-content">
                        ${toolCallsHtml}
                    </div>
                </div>
            `;
        }
    }
    
    messageDiv.innerHTML = `
        <div>${messageContent}</div>
        ${disclosureWidgets}
        <div class="timestamp">${timeStr}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * Add an error message to the chat interface
 * @param {string} message - The error message to display
 */
function addError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.textContent = `Error: ${message}`;
    messagesContainer.appendChild(errorDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * Toggle disclosure widget visibility
 * @param {HTMLElement} header - The disclosure header element
 */
function toggleDisclosure(header) {
    const content = header.nextElementSibling;
    const icon = header.querySelector('.icon');
    
    if (content.style.display === 'none' || content.style.display === '') {
        content.style.display = 'block';
        header.classList.add('expanded');
    } else {
        content.style.display = 'none';
        header.classList.remove('expanded');
    }
}

/**
 * Set the loading state of the chat interface
 * @param {boolean} loading - Whether the interface should show loading state
 */
function setLoading(loading) {
    sendButton.disabled = loading;
    messageInput.disabled = loading;
    typingIndicator.style.display = loading ? 'block' : 'none';
    
    if (loading) {
        sendButton.textContent = 'Sending...';
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } else {
        sendButton.textContent = 'Send';
    }
}

/**
 * Send a message to the agent API
 */
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addMessage(message, true);
    messageInput.value = '';
    setLoading(true);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        });

        if (!response.ok) {
            // Handle ErrorResponse format for non-200 responses
            try {
                const errorData = await response.json();
                if (errorData.error && errorData.message) {
                    throw new Error(errorData.message);
                }
            } catch (parseError) {
                // If we can't parse the error response, fall back to status
                throw new Error(`HTTP ${response.status}`);
            }
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        
        // Check for ErrorResponse format in successful responses
        if (data.error && data.message) {
            addError(data.message);
        } else if (data.error) {
            // Legacy error format support
            addError(data.error);
        } else {
            addMessage(
                data.response, 
                false, 
                data.timestamp,
                data.tool_calls || [],
                data.references || []
            );
        }
    } catch (error) {
        addError(`Failed to send message: ${error.message}`);
    } finally {
        setLoading(false);
        messageInput.focus();
    }
}

// Event listeners
sendButton.addEventListener('click', sendMessage);

messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Focus input on load
messageInput.focus();
