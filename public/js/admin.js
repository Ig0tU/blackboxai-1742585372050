// Admin interface functionality
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const serverStatus = document.getElementById('serverStatus');
    const requestStats = document.getElementById('requestStats');
    const activeBots = document.getElementById('activeBots');
    const botList = document.getElementById('botList');
    const botSelect = document.getElementById('botSelect');
    const modelSelection = document.getElementById('modelSelection');
    const modelSelect = document.getElementById('modelSelect');
    const testMessage = document.getElementById('testMessage');
    const sendTest = document.getElementById('sendTest');
    const testResult = document.getElementById('testResult');
    const testResponse = document.getElementById('testResponse');
    const connectionStatus = document.getElementById('connectionStatus');

    // Bot types that support model selection
    const MODEL_SELECTION_BOTS = ['enterprise', 'app-creator'];

    // Update server info and stats
    async function updateServerInfo() {
        try {
            const response = await fetch('/health');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log('Health check response:', data);

            // Update server status
            serverStatus.textContent = data.status;
            
            // Update request stats
            requestStats.textContent = `${data.total_requests} requests processed`;
            
            // Update active bots count
            activeBots.textContent = `${data.available_bots.length} bots available`;

            // Update bot list with descriptions
            const botListHtml = data.available_bots.map(bot => {
                const description = data.bot_descriptions[bot] || 'No description available';
                const isModelBot = MODEL_SELECTION_BOTS.includes(bot);
                return `
                    <div class="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
                        <div class="flex-grow">
                            <h3 class="font-semibold text-gray-700">${capitalizeFirstLetter(bot)}</h3>
                            <p class="text-sm text-gray-500">${description}</p>
                            ${isModelBot ? '<p class="text-xs text-indigo-600 mt-1">Supports model selection</p>' : ''}
                        </div>
                        <div class="flex items-center space-x-2">
                            <span class="px-3 py-1 text-sm text-green-700 bg-green-100 rounded-full">Active</span>
                        </div>
                    </div>
                `;
            }).join('');
            
            botList.innerHTML = botListHtml || 'No bots available';

            // Update bot select options
            botSelect.innerHTML = `
                <option value="">Choose a bot...</option>
                ${data.available_bots.map(bot => 
                    `<option value="${bot}">${capitalizeFirstLetter(bot)}</option>`
                ).join('')}
            `;

            // Update connection status
            connectionStatus.innerHTML = `
                <i class="fas fa-circle text-xs mr-2 text-green-400"></i>
                Connected
            `;

        } catch (error) {
            console.error('Error fetching server info:', error);
            connectionStatus.innerHTML = `
                <i class="fas fa-circle text-xs mr-2 text-red-500"></i>
                Disconnected
            `;
            botList.innerHTML = '<div class="text-red-500 p-4">Error loading bots. Please check server connection.</div>';
        }
    }

    // Helper function to capitalize first letter
    function capitalizeFirstLetter(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }

    // Handle bot selection change
    botSelect.addEventListener('change', function() {
        // Show/hide model selection for supported bots
        modelSelection.style.display = MODEL_SELECTION_BOTS.includes(this.value) ? 'block' : 'none';
    });

    // Send test message
    async function sendTestMessage() {
        const bot = botSelect.value;
        const message = testMessage.value;

        if (!bot || !message) {
            alert('Please select a bot and enter a message');
            return;
        }

        try {
            // Disable send button and show loading state
            sendTest.disabled = true;
            sendTest.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Sending...';

            // Prepare the message
            let payload = {
                query: [{
                    role: "user",
                    content: message,
                    content_type: "text/markdown",
                    timestamp: Date.now() * 1000
                }]
            };

            // Add model selection for supported bots
            if (MODEL_SELECTION_BOTS.includes(bot)) {
                const modelSettings = {
                    model: modelSelect.value
                };
                payload.query[0].content = JSON.stringify(modelSettings) + '\n' + message;
            }

            const response = await fetch(`/bot/${bot}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Bot response:', data);
            
            // Show response
            testResult.classList.remove('hidden');
            testResponse.innerHTML = `
                <div class="space-y-2">
                    <div class="text-gray-500 text-sm">Bot: ${capitalizeFirstLetter(bot)}</div>
                    ${MODEL_SELECTION_BOTS.includes(bot) ? 
                        `<div class="text-gray-500 text-sm">Model: ${modelSelect.value}</div>` : 
                        ''}
                    <div class="whitespace-pre-wrap">${data[0]?.text || 'No response received'}</div>
                </div>
            `;

            // Update server info after successful test
            updateServerInfo();

        } catch (error) {
            console.error('Error sending test message:', error);
            testResult.classList.remove('hidden');
            testResponse.innerHTML = `
                <div class="text-red-500">
                    Error: ${error.message}
                </div>
            `;
        } finally {
            // Reset send button
            sendTest.disabled = false;
            sendTest.innerHTML = 'Send Message';
        }
    }

    // Event listeners
    sendTest.addEventListener('click', sendTestMessage);

    // Handle Enter key in message input
    testMessage.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendTestMessage();
        }
    });

    // Initial update
    updateServerInfo();

    // Update every 30 seconds
    setInterval(updateServerInfo, 30000);
});