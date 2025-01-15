import os
import requests
from collections import defaultdict
from flask import Flask, request, jsonify, send_from_directory, Response
from generate_html import generate_html
from bs4 import BeautifulSoup
from flask_sqlalchemy import SQLAlchemy
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


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

    # Check if it's a callback query
    if "callback_query" in data:
        return callback()

    if "message" not in data:
        return jsonify({"status": "ignored"}), 200

    # Handle standard messages
    chat_id, first_name, text = _parse_message(data)
    if not text or not text.startswith("http"):
        send_message(chat_id, "Please send a valid link.")
        return jsonify({"status": "ok"}), 200

    # Extract tags and analyze link
    link, tags = _extract_tags_from_text(text)
    metadata = analyze_link(link)
    if not metadata:
        print("metadata couldn't be generated. stoping process")
 
    print("metadata exists, saving link to db")
    link_id = _save_link_to_db(chat_id, link, tags, metadata)
    print("link_id is: ", link_id)

    # Send tagging options
    existing_tags = [tag.name for tag in Tag.query.order_by(Tag.name).all()]
    inline_keyboard = generate_inline_keyboard(link_id, existing_tags)
    send_message_with_buttons(chat_id, "Tag this link:", inline_keyboard)
    return jsonify({"status": "ok"}), 200


def generate_inline_keyboard(link_id, existing_tags):
    """Generate inline keyboard with existing tags and an option to add a new tag."""
    if not link_id:
        raise ValueError("link_id cannot be None")
    
    buttons = [
        [InlineKeyboardButton(tag, callback_data=f"tag:{link_id}:{tag}") for tag in existing_tags],
        [InlineKeyboardButton("Add New Tag", callback_data=f"add_tag:{link_id}")]
    ]
    return InlineKeyboardMarkup(buttons)



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
    print("Saving link to database")
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
    print(f"Link saved with ID: {user_link.id}")  # Debugging line

    return user_link.id


def _generate_and_send_html(chat_id, first_name):
    """Generate HTML and send link history."""
    print("_generate_and_send_html")
    user_links = UserLink.query.filter_by(chat_id=chat_id).order_by(UserLink.created_at.desc()).all()
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

@app.route("/add_tag/<int:link_id>", methods=["POST"])
def add_tag(link_id):
    data = request.get_json()
    tag_name = data.get("tag")

    if not tag_name:
        return jsonify({"error": "Tag name is required"}), 400

    # Fetch the link
    link = UserLink.query.get(link_id)
    if not link:
        return jsonify({"error": "Link not found"}), 404

    # Fetch or create the tag
    tag = Tag.query.filter_by(name=tag_name).first()
    if not tag:
        tag = Tag(name=tag_name)
        db.session.add(tag)

    # Add the tag to the link
    if tag not in link.tags:
        link.tags.append(tag)

    db.session.commit()

    # Regenerate the HTML for the user
    chat_id = link.chat_id
    user_links = UserLink.query.filter_by(chat_id=chat_id).order_by(UserLink.created_at.desc()).all()
    link_metadata = [
        {
            "title": l.title,
            "description": l.description,
            "url": l.url,
            "price": l.price,
            "images": l.images if isinstance(l.images, list) else l.images.split(","),
            "site_name": l.site_name,
            "tags": [t.name for t in l.tags],
            "created_at": l.created_at,
        }
        for l in user_links
    ]
    generate_html(chat_id, user_links, link_metadata, first_name="User")  # Regenerate the HTML file

    return jsonify({"message": "Tag added successfully!"}), 200

@app.route("/delete_link/<int:link_id>", methods=["DELETE"])
def delete_link(link_id):
    link = UserLink.query.get(link_id)
    if not link:
        return jsonify({"error": "Link not found"}), 404

    # Get chat_id and first_name from the link data
    chat_id = link.chat_id
    first_name = "User"  # Replace with logic to fetch the first name if available

    # Delete the link
    db.session.delete(link)
    db.session.commit()

    # Fetch updated user links and metadata
    user_links = UserLink.query.filter_by(chat_id=chat_id).order_by(UserLink.created_at.desc()).all()
    link_metadata = [
        {
            "title": l.title,
            "description": l.description,
            "url": l.url,
            "price": l.price,
            "images": l.images if isinstance(l.images, list) else l.images.split(","),
            "site_name": l.site_name,
            "tags": [tag.name for tag in l.tags],
            "created_at": l.created_at,
        }
        for l in user_links
    ]

    # Regenerate the HTML file
    generate_html(chat_id, user_links, link_metadata, first_name)

    return jsonify({"message": "Link deleted successfully!"}), 200

@app.route("/delete_all/<string:chat_id>", methods=["DELETE"])
def delete_all_links_and_tags(chat_id):
    # Fetch all links for the chat ID
    links = UserLink.query.filter_by(chat_id=chat_id).all()
    if not links:
        return jsonify({"error": "No links found for this chat ID"}), 404

    # Delete all links and associated tags
    for link in links:
        db.session.delete(link)

    # Commit the deletions
    db.session.commit()

    # Optionally clear unused tags
    unused_tags = Tag.query.filter(~Tag.links.any()).all()
    for tag in unused_tags:
        db.session.delete(tag)

    db.session.commit()

    # Regenerate the HTML file for the user with no links
    first_name = "User"  # Replace with logic to fetch the user's name, if available
    generate_html(chat_id, [], [], first_name)

    return jsonify({"message": "All links and tags deleted successfully!"}), 200

@app.route("/callback", methods=["POST"])
def callback():
    """Handle callback queries from Telegram inline buttons."""
    data = request.get_json()
    print("Callback data received:", data)  # Debugging line

    callback_query = data.get("callback_query")
    if not callback_query:
        print("No callback_query found")  # Debugging line
        return jsonify({"status": "ignored"}), 200

    callback_data = callback_query["data"]
    print("Callback data content:", callback_data)  # Debugging line

    if callback_data.startswith("tag:"):
        _, link_id, tag_name = callback_data.split(":")
        print(f"Parsed link_id: {link_id}, tag_name: {tag_name}")  # Debugging line
        _add_tag_to_link(link_id, tag_name)
        send_message(callback_query["message"]["chat"]["id"], f"Tag '{tag_name}' added to the link!")
    elif callback_data.startswith("add_tag:"):
        _, link_id = callback_data.split(":")
        print(f"Parsed link_id for adding a new tag: {link_id}")  # Debugging line
        send_message(callback_query["message"]["chat"]["id"], f"Send the new tag for the link ID {link_id}")

    return jsonify({"status": "ok"}), 200


def _add_tag_to_link(link_id, tag_name):
    """Add a tag to a specific link."""
    link = UserLink.query.get(link_id)
    if not link:
        raise ValueError("Link not found")

    tag = Tag.query.filter_by(name=tag_name).first()
    if not tag:
        tag = Tag(name=tag_name)
        db.session.add(tag)

    if tag not in link.tags:
        link.tags.append(tag)
        db.session.commit()

def send_message_with_buttons(chat_id, text, buttons):
    """Send a message with inline keyboard buttons."""
    url = TELEGRAM_API_URL + "sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": buttons.to_json()
    }
    requests.post(url, json=payload)

# Database Management
@app.route("/create_db", methods=["GET"])
def create_db():
    db.create_all()
    return "Database tables created successfully!", 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
