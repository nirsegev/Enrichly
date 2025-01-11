import os
import requests
from collections import defaultdict
from flask import Flask, request, jsonify, send_from_directory

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

def analyze_link(link):
    """Fetch and analyze the content of the link."""
    try:
        response = requests.get(link, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Categorize and extract attributes
        metadata = {}
        if soup.title:
            metadata["title"] = soup.title.string.strip()
        metadata["url"] = link

        # Example heuristic: Check for product or article keywords
        if soup.find("meta", {"name": "description"}):
            description = soup.find("meta", {"name": "description"}).get("content", "").strip()
            metadata["description"] = description

        # Try to find price if it’s a product
        price_tags = soup.find_all(["span", "div"], string=lambda s: s and "$" in s)
        if price_tags:
            metadata["price"] = price_tags[0].text.strip()

        # Extract article content if it's an article
        article_content = soup.find_all("p")
        if article_content:
            metadata["content"] = " ".join([p.text for p in article_content[:3]])  # Shortened content for display

        # Assign category (simple example: based on presence of attributes)
        if "price" in metadata:
            metadata["category"] = "Product"
        elif "content" in metadata:
            metadata["category"] = "Article"
        else:
            metadata["category"] = "Unknown"

        return metadata
    except Exception as e:
        print(f"Error analyzing link: {e}")
        return None


# Function to generate the HTML page with the link history
def generate_html(chat_id):
    # Ensure the directory exists
    directory = "/app/storage/links_history"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Start generating the HTML content
    history_html = f"""
    <html>
    <head>
        <title>Link History</title>
        <style>
            body {{
                background-color: #f4f7f6;
                margin: 0;
                padding: 0;
                color: #333;
                font-family: Arial, sans-serif;
            }}
            .container {{
                width: 80%;
                margin: 50px auto;
                background-color: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }}
            h1 {{
                color: #2c3e50;
                text-align: center;
                font-size: 36px;
                margin-bottom: 20px;
            }}
            .link-card {{
                background-color: #ecf0f1;
                margin: 20px 0;
                padding: 15px;
                border-radius: 4px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            }}
            .link-card h2 {{
                font-size: 20px;
                color: #34495e;
                margin: 0 0 10px;
            }}
            .link-card p {{
                font-size: 14px;
                color: #7f8c8d;
                margin: 5px 0;
            }}
            .link-card a {{
                text-decoration: none;
                color: #2980b9;
                font-weight: bold;
            }}
            .link-card a:hover {{
                text-decoration: underline;
            }}
            footer {{
                text-align: center;
                font-size: 14px;
                color: #7f8c8d;
                margin-top: 30px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Link History for User {chat_id}</h1>
    """

    # Loop through each link and its metadata
    for i, link in enumerate(user_links.get(chat_id, [])):
        metadata = link_metadata.get(chat_id, [])[i] if i < len(link_metadata.get(chat_id, [])) else {}

        history_html += f"""
        <div class="link-card">
            <h2><a href="{metadata.get('url', link)}" target="_blank">{metadata.get('title', 'Untitled')}</a></h2>
            <p><strong>Category:</strong> {metadata.get('category', 'Unknown')}</p>
            <p><strong>Description:</strong> {metadata.get('description', 'No description available.')}</p>
            {"<p><strong>Price:</strong> $" + metadata['price'] + "</p>" if "price" in metadata else ""}
            {"<p><strong>Content:</strong> " + metadata['content'][:200] + "...</p>" if "content" in metadata else ""}
        </div>
        """

    # Add footer and close HTML tags
    history_html += """
            <footer>
                <p>Generated by Enrichly</p>
            </footer>
        </div>
    </body>
    </html>
    """

    # Save the HTML file
    file_path = os.path.join(directory, f"{chat_id}_history.html")
    with open(file_path, "w") as file:
        file.write(history_html)

    # Return the link to the generated HTML page
    return f"https://flask-production-4c83.up.railway.app/storage/links_history/{chat_id}_history.html"



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
@app.route('/storage/links_history/<filename>')
def serve_file(filename):
    return send_from_directory('/app/storage/links_history', filename)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
