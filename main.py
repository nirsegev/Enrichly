import os
import requests
from collections import defaultdict
from flask import Flask, request, jsonify, send_from_directory
from generate_html import generate_html


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
        text = data["message"].get("text")

        if text and text.startswith("http"):
            user_links[chat_id].append(text)

            # Fetch and analyze link
            metadata = analyze_link(text)
            if metadata:
                link_metadata[chat_id].append(metadata)

            # Generate updated HTML
            html_link = generate_html(chat_id)
            send_message(chat_id, f"Thanks for sharing! Your link history: {html_link}")
        else:
            send_message(chat_id, "Please send a valid link.")
    return jsonify({"status": "ok"}), 200

from bs4 import BeautifulSoup

def analyze_link(link):
    """Fetch and analyze the content of the link, tailored for Amazon product pages."""
    try:
        response = requests.get(link, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        metadata = {"url": link}

        # Extract the canonical URL
        canonical_link = soup.find("link", {"rel": "canonical"})
        if canonical_link and canonical_link.get("href"):
            metadata["canonical_url"] = canonical_link["href"]

        # Extract product title from meta tag or title tag
        meta_title = soup.find("meta", {"name": "title"})
        if meta_title and meta_title.get("content"):
            metadata["title"] = meta_title["content"]
        else:
            metadata["title"] = soup.title.string.strip() if soup.title else "No title found"

        # Extract product description
        meta_description = soup.find("meta", {"name": "description"})
        if meta_description and meta_description.get("content"):
            metadata["description"] = meta_description["content"]

        # Example for price (Amazon might dynamically load this in JavaScript, so might require Selenium or similar tools)
        price_tags = soup.find_all("span", string=lambda s: s and "$" in s)
        if price_tags:
            metadata["price"] = price_tags[0].text.strip()

        # Set category if title or description has a product-like structure
        if metadata.get("price"):
            metadata["category"] = "Product"
        else:
            metadata["category"] = "Unknown"

        return metadata

    except Exception as e:
        print(f"Error analyzing link: {e}")
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

# Serve static HTML files
@app.route('/storage/links_history/<filename>')
def serve_file(filename):
    return send_from_directory('/app/storage/links_history', filename)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
