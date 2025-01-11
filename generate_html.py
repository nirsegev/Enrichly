import os

def generate_html(chat_id, user_links, link_metadata, first_name):
    """Generate a mobile-friendly HTML file with link history and metadata."""
    directory = "/app/storage/links_history"
    if not os.path.exists(directory):
        os.makedirs(directory)

    history_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{first_name}'s Bookmarks</title>
        <style>
            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background-color: #f9f9f9;
                color: #333;
            }}

            .container {{
                padding: 16px;
            }}

            .profile {{
                margin-bottom: 16px;
                text-align: center;
            }}

            .profile h2 {{
                margin: 0;
                font-size: 24px;
                color: #2c3e50;
            }}

            .bookmarks {{
                margin-top: 16px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px;
            }}

            .bookmark {{
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 12px;
                text-align: center;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }}

            .bookmark img {{
                max-width: 100%;
                height: auto;
                border-radius: 4px;
            }}

            .bookmark h3 {{
                font-size: 1rem;
                color: #333;
                margin: 12px 0 8px;
            }}

            .bookmark p {{
                font-size: 0.9rem;
                color: #555;
                margin: 0;
            }}

            .bookmark a {{
                display: inline-block;
                margin-top: 8px;
                padding: 8px 12px;
                background-color: #3498db;
                color: #fff;
                text-decoration: none;
                border-radius: 4px;
            }}

            .bookmark a:hover {{
                background-color: #2980b9;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="profile">
                <h2>{first_name}'s Bookmarks</h2>
            </div>

            <div class="bookmarks">
    """

    for link, metadata in zip(user_links.get(chat_id, []), link_metadata.get(chat_id, [])):
        history_html += f"""
        <div class="bookmark">
            <img src="{metadata.get('image', 'https://via.placeholder.com/150')}" alt="{metadata.get('title', 'No Image')}">
            <h3>{metadata.get('title', 'Untitled')}</h3>
            <p>Price: {metadata.get('price', 'N/A')}</p>
            <a href="{metadata.get('url', link)}" target="_blank">View Product</a>
        </div>
        """

    history_html += """
            </div>
        </div>
    </body>
    </html>
    """

    file_path = os.path.join(directory, f"{chat_id}_history.html")
    with open(file_path, "w") as file:
        file.write(history_html)

    return f"https://flask-production-4c83.up.railway.app/storage/links_history/{chat_id}_history.html"

def generate_bookmarks(chat_id, user_links, link_metadata):
    bookmarks_html = ""
    for i, link in enumerate(user_links.get(chat_id, [])):
        metadata = link_metadata.get(chat_id, [])[i] if i < len(link_metadata.get(chat_id, [])) else {}

        # Truncate the title to 150 characters and add ellipsis if longer
        title = metadata.get('title', 'Untitled')[:150] + ("..." if len(metadata.get('title', '')) > 150 else "")

        bookmarks_html += f"""
        <div class="bookmark">
            <img src="https://via.placeholder.com/40" alt="Thumbnail">
            <div>
                <p>{title}</p>
                <small>{metadata.get('category', 'Unknown')} - {metadata.get('url', link)}</small>
            </div>
        </div>
        """
    return bookmarks_html
