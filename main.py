from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Set your Telegram Bot token here
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your-telegram-bot-token")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/"

# Endpoint to handle Telegram Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Received data:", data)  # Print the full incoming data for debugging

    if "message" in data:
        chat_id = data["message"]["chat"].get("id")
        text = data["message"].get("text")
        username = data["message"]["chat"].get("first_name", "")  # Get the username if available

        print("Message text:", text)  # Log the text to check what is being received

        if text and text.startswith("http"):
            # Process the link
            response_message = process_link(chat_id, text, username)
            send_message(chat_id, response_message)
        else:
            send_message(chat_id, "Please send a valid link.")

    return jsonify({"status": "ok"}), 200
    
# Function to process the link and generate a personalized response
def process_link(chat_id, link, username):
    # Placeholder for enrichment logic
    enriched_data = {
        "message": f"Hi {username}, thanks for sharing! Here's what we found:",
        "link": link,
        "suggestions": ["Similar Product A", "Related Article B", "Live Event C"]
    }
    # Format the enriched data
    response_message = f"{enriched_data['message']}\n\nOriginal Link: {link}\n\nSuggestions:\n- " + "\n- ".join(enriched_data["suggestions"])
    return response_message

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

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
