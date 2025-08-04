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
                
                // Handle both old and new ToolResult structure
                const toolName = tool.tool_name || tool.name || 'Unknown Tool';
                const executionTime = tool.execution_time_ms;
                
                return `
                    <div class="tool-call">
                        <div class="tool-call-header">
                            <span class="tool-name">${toolName}</span>
                            <span class="tool-status ${statusClass}">${statusText}</span>
                        </div>
                        <div class="tool-result">${tool.result}</div>
                        ${executionTime ? `<div class="tool-execution-time">Execution time: ${Math.round(executionTime)}ms</div>` : ''}
                        ${tool.error_message ? `<div class="tool-error">Error: ${tool.error_message}</div>` : ''}
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
 * Add a progress indicator for tool execution
 * @param {string} message - The progress message to display
 * @param {string} tool - The tool name being executed
 * @returns {HTMLElement} The progress element
 */
function addProgressIndicator(message, tool = '') {
    const progressDiv = document.createElement('div');
    progressDiv.className = 'progress-indicator';
    progressDiv.innerHTML = `
        <div class="progress-content">
            <div class="spinner"></div>
            <span class="progress-message">${message}</span>
            ${tool ? `<span class="progress-tool">(${tool})</span>` : ''}
        </div>
    `;
    
    messagesContainer.appendChild(progressDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return progressDiv;
}

/**
 * Update a progress indicator with completion status
 * @param {HTMLElement} progressElement - The progress element to update
 * @param {string} message - The completion message
 * @param {boolean} success - Whether the operation was successful
 */
function updateProgressIndicator(progressElement, message, success = true) {
    const statusClass = success ? 'success' : 'error';
    const statusIcon = success ? '✅' : '❌';
    
    progressElement.className = `progress-indicator completed ${statusClass}`;
    progressElement.innerHTML = `
        <div class="progress-content">
            <span class="status-icon">${statusIcon}</span>
            <span class="progress-message">${message}</span>
        </div>
    `;
}

/**
 * Send a message to the agent API using streaming
 */
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addMessage(message, true);
    messageInput.value = '';
    setLoading(true);

    let currentProgressElement = null;
    let toolCalls = [];
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream',
            },
            body: JSON.stringify({ message }),
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        // Check if the response is a stream (SSE) or regular JSON
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('text/event-stream')) {
            // Handle streaming response
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            try {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                
                                switch (data.type) {
                                    case 'start':
                                        currentProgressElement = addProgressIndicator(data.message);
                                        break;
                                        
                                    case 'tool_start':
                                        if (currentProgressElement) {
                                            updateProgressIndicator(currentProgressElement, 'Research started', true);
                                        }
                                        currentProgressElement = addProgressIndicator(data.message, data.tool);
                                        break;
                                        
                                    case 'tool_complete':
                                        if (currentProgressElement) {
                                            updateProgressIndicator(currentProgressElement, data.message, data.success);
                                        }
                                        // Use structured ToolResult data if available, otherwise fall back to manual construction
                                        if (data.tool_result) {
                                            toolCalls.push(data.tool_result);
                                        } else {
                                            // Fallback for backward compatibility
                                            toolCalls.push({
                                                tool_name: data.tool,
                                                success: data.success,
                                                result: data.message,
                                                execution_time_ms: null
                                            });
                                        }
                                        currentProgressElement = null;
                                        break;
                                        
                                    case 'response':
                                        if (currentProgressElement) {
                                            updateProgressIndicator(currentProgressElement, 'Research completed', true);
                                        }
                                        // Add final agent response
                                        addMessage(
                                            data.message,
                                            false,
                                            new Date().toISOString(),
                                            toolCalls,
                                            [] // References can be added later if needed
                                        );
                                        break;
                                        
                                    case 'error':
                                        if (currentProgressElement) {
                                            updateProgressIndicator(currentProgressElement, 'Error occurred', false);
                                        }
                                        addError(data.message);
                                        break;
                                }
                            } catch (parseError) {
                                console.warn('Failed to parse SSE data:', line);
                            }
                        }
                    }
                }
            } finally {
                reader.releaseLock();
            }
        } else {
            // Fallback to regular JSON response
            const data = await response.json();
            
            if (data.error && data.message) {
                addError(data.message);
            } else if (data.error) {
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
        }
    } catch (error) {
        if (currentProgressElement) {
            updateProgressIndicator(currentProgressElement, 'Connection failed', false);
        }
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
