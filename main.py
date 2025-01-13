import os
import requests
from collections import defaultdict
from flask import Flask, request, jsonify, send_from_directory, Response
from generate_html import generate_html
from bs4 import BeautifulSoup
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configure database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Store user data (link history)
user_links = defaultdict(list)
link_metadata = defaultdict(list)

# Set your Telegram Bot token here
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your-telegram-bot-token")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/"

X_SOAX_API_Secret = os.getenv("X-SOAX-API-Secret", "your-soax-token")

# Endpoint to handle Telegram Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" in data:
        chat_id = str(data["message"]["chat"].get("id"))
        first_name = data["message"]["chat"].get("first_name")  # Extract first name
        text = data["message"].get("text")

        if text and text.startswith("http"):
            # Extract tags from the message
            parts = text.split()
            link = parts[0]
            tags = [part.lstrip("#") for part in parts[1:] if part.startswith("#")]

            # Fetch and analyze link
            metadata = analyze_link(link)
            if metadata:
                # Save the link to the database
                user_link = UserLink(
                    chat_id=chat_id,
                    link=link,
                    title=metadata.get("title"),
                    description=metadata.get("description"),
                    url=metadata.get("url"),
                    price=metadata.get("price"),
                    images=metadata.get("images"),
                    site_name=metadata.get("site_name"),
                )

                # Add tags to the link
                for tag_name in tags:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    user_link.tags.append(tag)

                db.session.add(user_link)
                db.session.commit()

            # Query the database for user links and metadata
            user_links = UserLink.query.filter_by(chat_id=chat_id).all()
            link_metadata = [
                {
                    "title": link.title,
                    "description": link.description,
                    "url": link.url,
                    "price": link.price,
                    "images": link.images if isinstance(link.images, list) else link.images.split(","),
                    "site_name": link.site_name,
                    "tags": [tag.name for tag in link.tags],
                    "created_at": link.created_at,  # Pass raw datetime object
                }
                for link in user_links
            ]

            # Generate the HTML
            html_link = generate_html(chat_id, user_links, link_metadata, first_name)

            send_message(chat_id, f"Thanks for sharing! Your link history: {html_link}")
        else:
            send_message(chat_id, "Please send a valid link.")
    return jsonify({"status": "ok"}), 200



def analyze_link(link):
    """Analyze a link and retrieve structured product data using SOAX for Amazon links or OpenGraph as fallback."""
    headers_soax = {
        'X-SOAX-API-Secret': X_SOAX_API_Secret,
    }

    headers_general = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "DNT": "1",  # Do Not Track
        "Upgrade-Insecure-Requests": "1",
    }

    if "amazon" in link:
        # Use the SOAX scraping API for Amazon links
        print("Using SOAX scraping API for Amazon link.")
        api_url = f"https://scraping.soax.com/v1/request?param={link}&function=getProduct&sync=true"

        try:
            response = requests.get(api_url, headers=headers_soax, timeout=60)
            response.raise_for_status()

            # Parse the SOAX response JSON
            result = response.json()
            if result.get("data", {}).get("status") == "done":
                product_data = result.get("data", {}).get("value", {})
                extras = product_data.get("extras", {})
                images_small = extras.get("imagesSmall", [])

                # Ensure `images_small` is treated as a list
                if isinstance(images_small, dict):
                    images_small = list(images_small.values())

                # Extract all valid image URLs from imagesSmall
                product_images = [url for url in images_small if isinstance(url, str) and url.endswith(".jpg")]

                processed_data = {
                    "title": product_data.get("title", "Untitled"),
                    "images": product_images,
                    "price": product_data.get("price", "N/A"),
                    "url": product_data.get("url", link),
                }

                print("Processed Data from SOAX (Amazon):", processed_data)
                return processed_data

        except requests.exceptions.RequestException as e:
            print(f"SOAX API error: {e}")

    # Fallback for non-Amazon links using SOAX unblocker
    try:
        print("Using SOAX unblocker API for non-Amazon link.")
        soax_unblocker_link = f"https://scraping.soax.com/v1/unblocker/html?xhr=false&url={link}"
        response = requests.get(soax_unblocker_link, headers=headers_soax, timeout=60)
        response.raise_for_status()

        # Log response size
        #response_size = len(response.content)
        #print(f"Response content size: {response_size} bytes")

        #first_bytes = response.raw.read(4096, decode_content=True).decode("utf-8", errors="ignore")
        
        # Parse the response content with BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract OpenGraph tags
        title_tag = soup.find("meta", property="og:title")
        url_tag = soup.find("meta", property="og:url")
        description_tag = soup.find("meta", property="og:description")
        image_tag = soup.find("meta", property="og:image")
        site_name_tag = soup.find("meta", property="og:site_name")

        # Extract content or provide defaults
        data = {
            "title": title_tag["content"] if title_tag and title_tag.get("content") else "No title found",
            "description": description_tag["content"] if description_tag and description_tag.get("content") else "No description found",
            "url": url_tag["content"] if url_tag and url_tag.get("content") else link,
            "images": [image_tag["content"]] if image_tag and image_tag.get("content") else [],
            "site_name": site_name_tag["content"] if site_name_tag and site_name_tag.get("content") else "Unknown site name",
        }

        # Debugging extracted data
        print("Extracted OpenGraph Data:", data)
        return data

    except requests.exceptions.RequestException as e:
        print(f"OpenGraph extraction error: {e}")
    except Exception as e:
        print(f"Error parsing OpenGraph metadata: {e}")

    # Return minimal data if both SOAX and OpenGraph fail
    return {
        "title": link,
        "images": [],
        "price": "N/A",
        "url": link,
        "description": "",
    }



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

@app.route('/create_db', methods=['GET'])
def create_db():
    db.create_all()
    return "Database tables created successfully!", 200

@app.route("/links/<chat_id>/tags", methods=["GET"])
def get_links_by_tags(chat_id):
    # Get tags from request arguments
    tags = request.args.getlist("tag")  # Example: ?tag=tag1&tag=tag2

    # Build the query
    query = UserLink.query.filter_by(chat_id=chat_id)
    if tags:
        query = query.filter(UserLink.tags.any(Tag.name.in_(tags)))

    # Fetch and return links
    links = query.order_by(UserLink.created_at.desc()).all()
    return jsonify([
        {
            "id": link.id,
            "title": link.title,
            "description": link.description,
            "url": link.url,
            "tags": [tag.name for tag in link.tags],
        }
        for link in links
    ])

# Association table for many-to-many relationship
link_tags = db.Table(
    'link_tags',
    db.Column('link_id', db.Integer, db.ForeignKey('user_links.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)

class UserLink(db.Model):
    __tablename__ = 'user_links'

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String, nullable=False)  # Telegram chat ID
    link = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=True)
    description = db.Column(db.Text, nullable=True)
    url = db.Column(db.String, nullable=True)
    price = db.Column(db.String, nullable=True)
    images = db.Column(db.JSON, nullable=True)  # Store as JSON
    site_name = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())

    # Many-to-many relationship with tags
    tags = db.relationship('Tag', secondary=link_tags, back_populates='links')

    def __repr__(self):
        return f"<UserLink {self.title}>"


class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)

    # Many-to-many relationship with links
    links = db.relationship('UserLink', secondary=link_tags, back_populates='tags')

    def __repr__(self):
        return f"<Tag {self.name}>"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
