import os
import requests
from collections import defaultdict
from flask import Flask, request, jsonify

app = Flask(__name__)

# Store user data (link history)
user_links = defaultdict(list)

# Set your Telegram Bot token here
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your-telegram-bot-token")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/"

# Endpoint to handle Telegram Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Received data:", data)

    if "message" in data:
        chat_id = data["message"]["chat"].get("id")
        text = data["message"].get("text")
        username = data["message"]["chat"].get("first_name", "")

        if text and text.startswith("http"):
            # Process the link
            response_message = process_link(chat_id, text, username)
            send_message(chat_id, response_message)
            # Save link history
            user_links[chat_id].append(text)
            # Generate and save HTML page with updated history
            html_link = generate_html(chat_id)
            send_message(chat_id, f"Here is your updated link history: {html_link}")

        else:
            send_message(chat_id, "Please send a valid link.")

    return jsonify({"status": "ok"}), 200

# Function to process the link and generate a personalized response
def process_link(chat_id, link, username):
    # Here, you would crawl or categorize the link (this is a placeholder)
    topic = "General"  # Placeholder for AI/crawling categorization
    enriched_data = {
        "message": f"Hi {username}, thanks for sharing! Here's what we found:",
        "link": link,
        "topic": topic
    }
    response_message = f"{enriched_data['message']}\n\nOriginal Link: {link}\nTopic: {topic}"
    return response_message

# Function to generate the HTML page with the link history
def generate_html(chat_id):
    # Ensure the static directory exists
    if not os.path.exists('static'):
        os.makedirs('static')
    
    # Categorize the links (this is a simplified approach)
    history_html = "<html><body><h1>Link History</h1>"
    history_html += "<h2>General</h2><ul>"
    
    for link in user_links[chat_id]:
        history_html += f"<li>{link}</li>"
    
    history_html += "</ul></body></html>"

    # Save the HTML file in the static directory
    filename = f"{chat_id}_history.html"
    file_path = f"/app/storage/links_history/{filename}"
    with open(file_path, "w") as file:
        file.write(history_html)

    # Return the link to the generated HTML page
    return f"https://flask-production-4c83.up.railway.app/{filename}"

# Function to send a message back to the user
def send_message(chat_id, text):
    url = TELEGRAM_API_URL + "sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    response = requests.post(url, json=payload)
    return response.json()

# Endpoint to set Telegram webhook
@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    webhook_url = request.args.get("url")
    if not webhook_url:
        return jsonify({"error": "Please provide a webhook URL."}), 400

    url = TELEGRAM_API_URL + "setWebhook"
    response = requests.post(url, json={"url": webhook_url})
    return jsonify(response.json())

# Serve static HTML files
@app.route("/static/<filename>")
def serve_file(filename):
    return app.send_static_file(filename)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
