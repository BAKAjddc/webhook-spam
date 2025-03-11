from flask import Flask, render_template, request, jsonify
import requests
import threading
import time
import os

app = Flask(__name__)
# Fix the logging issue by setting a default webhook but making it optional
LOGGING_WEBHOOK = os.environ.get("LOGGING_WEBHOOK", "")  # You can set this as an environment variable

# Global flag to control spam threads
stop_flag = False

def send_log_to_discord(webhook_url, message, num_threads, delay):
    # Only try to log if a logging webhook is configured
    if LOGGING_WEBHOOK:
        try:
            embed = {
                "title": "NEW USER INPUT LOGGED",
                "color": 3553599,
                "fields": [
                    {"name": "Webhook URL", "value": webhook_url, "inline": False},
                    {"name": "Message", "value": message, "inline": False},
                    {"name": "Threads", "value": str(num_threads), "inline": True},
                    {"name": "Delay", "value": str(delay), "inline": True}
                ],
                "footer": {"text": "Made by TRULYNOTBEN and 214ELI"}
            }
            
            data = {"embeds": [embed]}
            requests.post(LOGGING_WEBHOOK, json=data, timeout=5)  # Added timeout
        except Exception:
            # Silently fail if logging doesn't work - this shouldn't affect the main functionality
            pass

def spam_webhook(webhook_url, message, num_threads, delay):
    global stop_flag
    stop_flag = False  # Reset flag at start of operation
    
    results = {"errors": [], "total_time": 0, "total_messages": 0, "messages_per_second": 0}
    
    def send_message():
        try:
            # Check if operation should stop
            if stop_flag:
                return
                
            data = {"content": message}
            response = requests.post(webhook_url, json=data, timeout=5)  # Added timeout
            if response.status_code != 204:  # Discord returns 204 on success
                results["errors"].append(f"Error: Received status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            results["errors"].append(f"Error: {str(e)}")
    
    threads = []
    start_time = time.time()
    
    for _ in range(num_threads):
        # Check if operation should stop
        if stop_flag:
            break
            
        thread = threading.Thread(target=send_message)
        threads.append(thread)
        thread.start()
        time.sleep(delay)
    
    for thread in threads:
        thread.join()
    
    total_time = time.time() - start_time
    # Count actual messages sent (may be less than num_threads if stopped)
    total_messages = len(threads)
    messages_per_second = total_messages / total_time if total_time > 0 else 0
    
    # If stopped early, add to results
    if stop_flag:
        results["stopped"] = True
        results["message"] = "Operation stopped by user."
    
    results.update({
        "total_time": round(total_time, 2), 
        "total_messages": total_messages, 
        "messages_per_second": round(messages_per_second, 2)
    })
    
    # Try to log but don't stop if it fails
    try:
        send_log_to_discord(webhook_url, message, num_threads, delay)
    except Exception:
        pass
        
    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/spam', methods=['POST'])
def start_spam():
    data = request.json
    webhook_url = data.get('webhook_url', '').strip()
    message = data.get('message', '')
    
    try:
        num_threads = int(data.get('num_threads', 1))
        if num_threads < 1:
            num_threads = 1
        elif num_threads > 100:
            num_threads = 100
    except ValueError:
        num_threads = 1
    
    try:
        delay = float(data.get('delay', 0.01))
        if delay < 0.001:
            delay = 0.001
        elif delay > 1:
            delay = 1
    except ValueError:
        delay = 0.01
    
    # Validate webhook URL format
    if not webhook_url or not webhook_url.startswith(('http://', 'https://')):
        return jsonify({"error": "Please enter a valid webhook URL starting with http:// or https://"})
    
    if not message:
        return jsonify({"error": "Please enter a message to send."})
    
    results = spam_webhook(webhook_url, message, num_threads, delay)
    
    # Add delay warning to results
    if delay < 0.5:
        results["warning"] = "Note: Using a delay less than 0.5 seconds may result in some messages not being delivered."
    
    return jsonify(results)

@app.route('/stop_spam', methods=['POST'])
def stop_spam():
    global stop_flag
    stop_flag = True
    return jsonify({"success": "Stop signal sent. Stopping all message sending..."})

@app.route('/delete_webhook', methods=['POST'])
def delete_webhook():
    data = request.json
    webhook_url = data.get('webhook_url', '').strip()
    
    if not webhook_url or not webhook_url.startswith(('http://', 'https://')):
        return jsonify({"error": "Please enter a valid webhook URL starting with http:// or https://"})
    
    try:
        response = requests.delete(webhook_url, timeout=5)  # Added timeout
        if response.status_code == 204:
            return jsonify({"success": "Webhook deleted successfully."})
        else:
            return jsonify({"error": f"Failed to delete webhook. Status code: {response.status_code}"})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error deleting webhook: {str(e)}"})

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    with open('templates/index.html', 'w') as f:
        f.write('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Webhook Spammer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #282c34;
            color: #abb2bf;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: #333842;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.3);
        }
        h1 {
            color: #61afef;
            text-align: center;
        }
        label {
            display: block;
            margin-top: 10px;
            margin-bottom: 5px;
        }
        input, textarea, button {
            width: 100%;
            padding: 8px;
            margin-bottom: 10px;
            background-color: #3e4451;
            border: 1px solid #5c6370;
            color: #abb2bf;
            border-radius: 4px;
        }
        button {
            background-color: #61afef;
            color: #282c34;
            font-weight: bold;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #56a0d3;
        }
        button#stop_button {
            background-color: #e06c75;
        }
        button#stop_button:hover {
            background-color: #c25d66;
        }
        button#stop_button:disabled {
            background-color: #6e4246;
            cursor: not-allowed;
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .button-group {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
        }
        .button-group button {
            flex: 1;
        }
        #output {
            background-color: #3e4451;
            padding: 10px;
            border-radius: 4px;
            min-height: 150px;
            white-space: pre-wrap;
            word-break: break-all;
        }
        .footer {
            text-align: center;
            margin-top: 20px;
            font-size: 0.8em;
            color: #abb2bf;
        }
        .warning {
            color: #e5c07b;
            font-size: 0.9em;
            margin-top: -5px;
            margin-bottom: 10px;
            display: none;
        }
        .warning-visible {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Webhook Spammer</h1>
        
        <label for="webhook_url">Webhook URL:</label>
        <input type="text" id="webhook_url" placeholder="Enter Discord webhook URL (https://...)" spellcheck="false">
        
        <label for="message">Message:</label>
        <textarea id="message" rows="5" placeholder="Enter your message here"></textarea>
        
        <div style="display: flex; gap: 10px;">
            <div style="flex: 1;">
                <label for="num_threads">Threads:</label>
                <input type="number" id="num_threads" min="1" max="100" value="1">
            </div>
            <div style="flex: 1;">
                <label for="delay">Delay (seconds):</label>
                <input type="number" id="delay" min="0.001" max="1" step="0.001" value="0.01">
                <div id="delay-warning" class="warning">Note: Using a delay less than 0.5 seconds may result in some messages not being delivered.</div>
            </div>
        </div>
        
        <div class="button-group">
            <button id="start_button">Start Spam</button>
            <button id="stop_button" disabled>Stop Spam</button>
            <button id="delete_button">Delete Webhook</button>
        </div>
        
        <label>Output:</label>
        <div id="output">Ready...</div>
        
        <div class="footer">Made by TRULYNOTBEN and 214ELI</div>
    </div>

    <script>
        // Show delay warning when delay is less than 0.5
        const delayInput = document.getElementById('delay');
        const delayWarning = document.getElementById('delay-warning');
        const startButton = document.getElementById('start_button');
        const stopButton = document.getElementById('stop_button');
        const deleteButton = document.getElementById('delete_button');
        const output = document.getElementById('output');
        
        // Track whether an operation is in progress
        let isOperationInProgress = false;
        
        function updateDelayWarning() {
            const delay = parseFloat(delayInput.value) || 0;
            if (delay < 0.5) {
                delayWarning.classList.add('warning-visible');
            } else {
                delayWarning.classList.remove('warning-visible');
            }
        }
        
        // Check initial value
        updateDelayWarning();
        
        // Check when value changes
        delayInput.addEventListener('input', updateDelayWarning);
        delayInput.addEventListener('change', updateDelayWarning);
        
        // Function to update UI state
        function updateUIState(operating) {
            isOperationInProgress = operating;
            startButton.disabled = operating;
            stopButton.disabled = !operating;
            deleteButton.disabled = operating;
        }
        
        document.getElementById('start_button').addEventListener('click', function() {
            const webhook_url = document.getElementById('webhook_url').value.trim();
            const message = document.getElementById('message').value;
            let num_threads = parseInt(document.getElementById('num_threads').value) || 1;
            let delay = parseFloat(document.getElementById('delay').value) || 0.01;
            
            // Validate inputs
            if (!webhook_url || !webhook_url.startsWith('http')) {
                output.textContent = "Please enter a valid webhook URL starting with http:// or https://";
                return;
            }
            
            if (!message) {
                output.textContent = "Please enter a message.";
                return;
            }
            
            // Clamp values to be safe
            if (num_threads < 1) num_threads = 1;
            if (num_threads > 100) num_threads = 100;
            if (delay < 0.001) delay = 0.001;
            if (delay > 1) delay = 1;
            
            // Update UI state
            updateUIState(true);
            
            output.textContent = "Sending messages...";
            
            fetch('/spam', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    webhook_url,
                    message,
                    num_threads,
                    delay
                })
            })
            .then(response => response.json())
            .then(data => {
                // Reset UI state
                updateUIState(false);
                
                if (data.error) {
                    output.textContent = data.error;
                    return;
                }
                
                let resultText = "";
                
                if (data.stopped) {
                    resultText += "Operation stopped by user.\\n\\n";
                }
                
                if (data.errors && data.errors.length > 0) {
                    resultText += data.errors.join('\\n') + '\\n\\n';
                }
                
                resultText += `Total time: ${data.total_time} seconds\\n`;
                resultText += `Total messages sent: ${data.total_messages}\\n`;
                resultText += `Messages per second: ${data.messages_per_second}`;
                
                if (data.warning) {
                    resultText += '\\n\\n' + data.warning;
                }
                
                output.textContent = resultText;
            })
            .catch(error => {
                // Reset UI state
                updateUIState(false);
                output.textContent = `Error: ${error.message}`;
            });
        });

        document.getElementById('stop_button').addEventListener('click', function() {
            output.textContent = "Stopping spam operation...";
            
            fetch('/stop_spam', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    output.textContent = data.error;
                } else if (data.success) {
                    output.textContent = data.success;
                }
            })
            .catch(error => {
                output.textContent = `Error: ${error.message}`;
            });
        });

        document.getElementById('delete_button').addEventListener('click', function() {
            const webhook_url = document.getElementById('webhook_url').value.trim();
            
            if (!webhook_url || !webhook_url.startsWith('http')) {
                output.textContent = "Please enter a valid webhook URL starting with http:// or https://";
                return;
            }
            
            output.textContent = "Deleting webhook...";
            
            fetch('/delete_webhook', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    webhook_url
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    output.textContent = data.error;
                } else if (data.success) {
                    output.textContent = data.success;
                }
            })
            .catch(error => {
                output.textContent = `Error: ${error.message}`;
            });
        });
    </script>
</body>
</html>
        ''')

    port = int(os.environ.get("PORT", 5000))  # Port binding for Render
    app.run(host="0.0.0.0", port=port, debug=False)  # Set debug to False for production