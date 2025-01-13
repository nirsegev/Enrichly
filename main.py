import os
import requests
from collections import defaultdict
from flask import Flask, request, jsonify, send_from_directory, Response
from generate_html import generate_html
from bs4 import BeautifulSoup
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask App
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

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your-telegram-bot-token")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/"
X_SOAX_API_Secret = os.getenv("X-SOAX-API-Secret", "your-soax-token")

# Database Models
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

    tags = db.relationship('Tag', secondary=link_tags, back_populates='links')

    def __repr__(self):
        return f"<UserLink {self.title}>"


class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)

    links = db.relationship('UserLink', secondary=link_tags, back_populates='tags')

    def __repr__(self):
        return f"<Tag {self.name}>"

# Utility Functions
def analyze_link(link):
    """Analyze a link to retrieve structured data."""
    if "amazon" in link:
        return _fetch_from_soax_api(link)
    return _fetch_opengraph_metadata(link)

def _fetch_from_soax_api(link):
    """Fetch data using SOAX API for Amazon links."""
    print("Using SOAX scraping API for Amazon link.")
    api_url = f"https://scraping.soax.com/v1/request?param={link}&function=getProduct&sync=true"
    headers = {'X-SOAX-API-Secret': X_SOAX_API_Secret}

    try:
        response = requests.get(api_url, headers=headers, timeout=60)
        response.raise_for_status()
        result = response.json()
        return _process_soax_response(result, link)
    except requests.exceptions.RequestException as e:
        print(f"SOAX API error: {e}")
        return {}

def _process_soax_response(result, link):
    """Process the SOAX API response."""
    if result.get("data", {}).get("status") != "done":
        return {}

    product_data = result.get("data", {}).get("value", {})
    extras = product_data.get("extras", {})
    images_small = extras.get("imagesSmall", [])

    # Ensure `images_small` is a list
    if isinstance(images_small, dict):
        images_small = list(images_small.values())

    product_images = [url for url in images_small if isinstance(url, str) and url.endswith(".jpg")]
    return {
        "title": product_data.get("title", "Untitled"),
        "images": product_images,
        "price": product_data.get("price", "N/A"),
        "url": product_data.get("url", link),
    }

def _fetch_opengraph_metadata(link):
    """Fallback: Fetch OpenGraph metadata."""
    print("Using OpenGraph metadata extraction.")
    headers = {'X-SOAX-API-Secret': X_SOAX_API_Secret}
    soax_unblocker_link = f"https://scraping.soax.com/v1/unblocker/html?xhr=false&url={link}"
    try:
        response = requests.get(soax_unblocker_link, headers=headers, timeout=60)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return _extract_opengraph_tags(soup, link)
    except requests.exceptions.RequestException as e:
        print(f"OpenGraph extraction error: {e}")
        return {}

def _extract_opengraph_tags(soup, link):
    """Extract OpenGraph metadata from the page."""
    print("_extract_opengraph_tags")
    def get_meta(property_name):
        tag = soup.find("meta", property=property_name)
        return tag["content"] if tag and tag.get("content") else None

    return {
        "title": get_meta("og:title") or "No title found",
        "description": get_meta("og:description") or "No description found",
        "url": get_meta("og:url") or link,
        "images": [get_meta("og:image")] if get_meta("og:image") else [],
        "site_name": get_meta("og:site_name") or "Unknown site name",
    }

# Telegram Bot Endpoints
@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle Telegram webhook messages."""
    data = request.get_json()
    if "message" not in data:
        return jsonify({"status": "ignored"}), 200

    chat_id, first_name, text = _parse_message(data)
    if not text or not text.startswith("http"):
        send_message(chat_id, "Please send a valid link.")
        return jsonify({"status": "ok"}), 200

    # Extract tags and analyze link
    link, tags = _extract_tags_from_text(text)
    metadata = analyze_link(link)
    if metadata:
        print("metadata exists, saving link to db")
        _save_link_to_db(chat_id, link, tags, metadata)

    # Generate and send HTML
    html_link = _generate_and_send_html(chat_id, first_name)
    send_message(chat_id, f"Thanks for sharing! Your link history: {html_link}")
    return jsonify({"status": "ok"}), 200

def _parse_message(data):
    """Extract relevant message data."""
    chat_id = str(data["message"]["chat"]["id"])
    first_name = data["message"]["chat"].get("first_name", "User")
    text = data["message"].get("text")
    return chat_id, first_name, text

def _extract_tags_from_text(text):
    """Extract tags and link from the text."""
    parts = text.split()
    link = parts[0]
    tags = [part.lstrip("#") for part in parts[1:] if part.startswith("#")]
    return link, tags

def _save_link_to_db(chat_id, link, tags, metadata):
    """Save link and metadata to the database."""
    print("saving link to db")
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

    for tag_name in tags:
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.session.add(tag)
        user_link.tags.append(tag)

    db.session.add(user_link)
    db.session.commit()

def _generate_and_send_html(chat_id, first_name):
    """Generate HTML and send link history."""
    print("_generate_and_send_html")
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
            "created_at": link.created_at,
        }
        for link in user_links
    ]
    return generate_html(chat_id, user_links, link_metadata, first_name)

# Utility: Send message to Telegram
def send_message(chat_id, text):
    url = TELEGRAM_API_URL + "sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

# Database Management
@app.route("/create_db", methods=["GET"])
def create_db():
    db.create_all()
    return "Database tables created successfully!", 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
