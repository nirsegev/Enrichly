import os
import requests
from collections import defaultdict
from flask import Flask, request, jsonify, send_from_directory, Response
from generate_html import generate_html
from bs4 import BeautifulSoup

app = Flask(__name__)

# Store user data (link history)
user_links = defaultdict(list)
link_metadata = defaultdict(list)

# Set your Telegram Bot token here
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your-telegram-bot-token")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/"

# Endpoint to handle Telegram Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" in data:
        chat_id = data["message"]["chat"].get("id")
        first_name = data["message"]["chat"].get("first_name")  # Extract first name
        text = data["message"].get("text")

        if text and text.startswith("http"):
            user_links[chat_id].append(text)

            # Fetch and analyze link
            metadata = analyze_link(text)
            if metadata:
                link_metadata[chat_id].append(metadata)

            # Generate updated HTML
            html_link = generate_html(chat_id, user_links, link_metadata, first_name)  
            send_message(chat_id, f"Thanks for sharing! Your link history: {html_link}")
        else:
            send_message(chat_id, "Please send a valid link.")
    return jsonify({"status": "ok"}), 200

def analyze_link(link):
    """Analyze a link and retrieve structured data using SOAX API scraper."""
    headers = {
        'X-SOAX-API-Secret': 'e1c3b3ee-7874-46f7-9af1-c41d44a0b3f0',
    }

    # Construct the SOAX API request URL
    api_url = f"https://scraping.soax.com/v1/request?param={link}&function=getProduct&sync=true"

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise an error for bad HTTP status codes

        # Parse the response JSON
        result = response.json()

        if result.get("data", {}).get("status") == "done":
            product_data = result.get("data", {}).get("value", {})
            images_small = product_data.get("imagesSmall", {})
            images_large = product_data.get("images", {})

            # Get the first non-empty small image or fallback to a large image, or placeholder
            product_image = next(
                (url for url in images_small.values() if url),
                next((url for url in images_large.values() if url), "https://via.placeholder.com/150")
            )

            return {
                "title": product_data.get("title", "Untitled"),
                "image": product_image,
                "price": product_data.get("price", "N/A"),
                "url": product_data.get("url", link)
            }
        else:
            print("No valid data received from SOAX API.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while analyzing the link: {e}")
        return None




# Endpoint to set Telegram webhook
@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    webhook_url = request.args.get("url")
    if not webhook_url:
        return jsonify({"error": "Please provide a webhook URL."}), 400

    url = TELEGRAM_API_URL + "setWebhook"
    response = requests.post(url, json={"url": webhook_url})
    return jsonify(response.json())

# Function to send a message back to the user
def send_message(chat_id, text):
    url = TELEGRAM_API_URL + "sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    response = requests.post(url, json=payload)
    return response.json()

# Serve static HTML files
@app.route('/storage/links_history/<filename>')
def serve_file(filename):
    # Serve the HTML content with cache-control headers
    try:
        # Read the HTML file content
        with open(f'/app/storage/links_history/{filename}', 'r') as file:
            html_content = file.read()
        
        # Return the HTML content with cache-control headers
        return Response(html_content, headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',  # Prevent caching
            'Pragma': 'no-cache',  # HTTP 1.0 compatibility
            'Expires': '0'  # Ensure it expires immediately
        })
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
