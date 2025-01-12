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
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 16px;
            }}

            .bookmark {{
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 12px;
                display: flex;
                align-items: center;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }}

            .bookmark img {{
                width: 70px;
                height: 70px;
                object-fit: cover;
                border-radius: 4px;
                margin-right: 12px;
                border: 1px solid #ddd;
            }}

            .bookmark-content {{
                flex: 1;
            }}

            .bookmark h3 {{
                font-size: 1rem;
                color: #3498db;
                margin: 0;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: normal;
            }}

            .bookmark h3 a {{
                text-decoration: none;
                color: inherit;
            }}

            .bookmark h3 a:hover {{
                text-decoration: underline;
            }}

            .bookmark p {{
                font-size: 0.9rem;
                color: #555;
                margin: 8px 0 0;
            }}

            .price {{
                font-weight: bold;
                color: #27ae60;
                margin-top: 8px;
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
        # Handle images
        images = metadata.get("images", [])
        image_html = f'<img src="{images[0]}" alt="Image">' if images else ""

        # Format price if available
        price = metadata.get("price", None)
        price_html = f'<p class="price">Price: ${price}</p>' if price and price != "N/A" else ""

        # Create bookmark section
        history_html += f"""
        <div class="bookmark">
            {image_html}
            <div class="bookmark-content">
                <h3><a href="{metadata.get('url', link)}" target="_blank">{metadata.get('title', 'Untitled')}</a></h3>
                <p>{metadata.get('description', '')}</p>
                {price_html}
            </div>
        </div>
        """

    history_html += """
            </div>
        </div>
    </body>
    </html>
    """

    # Save the HTML file
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
