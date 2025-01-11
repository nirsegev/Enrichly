import os

def generate_html(chat_id, user_links, link_metadata, first_name):
    """Generate a mobile-friendly HTML file with link history and metadata."""
    # Ensure the directory exists
    directory = "/app/storage/links_history"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Start generating the HTML content
    history_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{first_name}'s Link History</title>
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
                display: flex;
                align-items: center;
                margin-bottom: 16px;
            }}

            .profile img {{
                width: 50px;
                height: 50px;
                border-radius: 50%;
                margin-right: 12px;
            }}

            .profile h2 {{
                margin: 0;
                font-size: 18px;
            }}

            .search-bar {{
                margin: 16px 0;
            }}

            .search-bar input {{
                width: 100%;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}

            .categories {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 16px;
            }}

            .categories .category {{
                text-align: center;
                flex: 1;
                padding: 8px;
                margin: 0 4px;
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 8px;
            }}

            .collections {{
                margin-bottom: 16px;
            }}

            .collections .collection {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px;
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-bottom: 8px;
            }}

            .bookmarks {{
                margin-top: 16px;
            }}

            .bookmarks .bookmark {{
                display: flex;
                align-items: center;
                padding: 8px;
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-bottom: 8px;
            }}

            .bookmarks .bookmark img {{
                width: 40px;
                height: 40px;
                border-radius: 4px;
                margin-right: 12px;
            }}

            .bottom-nav {{
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                display: flex;
                justify-content: space-around;
                background-color: #fff;
                border-top: 1px solid #ddd;
                padding: 8px 0;
            }}

            .bottom-nav .nav-item {{
                text-align: center;
            }}

            .bottom-nav .nav-item i {{
                font-size: 24px;
                display: block;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Profile -->
            <div class="profile">
                <img src="https://via.placeholder.com/50" alt="User">
                <div>
                    <h2>{first_name}</h2>
                    <p>{first_name.lower()}@example.com</p>
                </div>
            </div>

            <!-- Search Bar -->
            <div class="search-bar">
                <input type="text" placeholder="Search...">
            </div>

            <!-- Categories -->
            <div class="categories">
                <div class="category">
                    <i>🔗</i>
                    <p>Link</p>
                </div>
                <div class="category">
                    <i>🖼️</i>
                    <p>Image</p>
                </div>
                <div class="category">
                    <i>📄</i>
                    <p>Document</p>
                </div>
                <div class="category">
                    <i>🎥</i>
                    <p>Video</p>
                </div>
            </div>

            <!-- Collections -->
            <div class="collections">
                <h3>My Collection</h3>
                <div class="collection">
                    <span>Project 1</span>
                    <span>174 MB</span>
                </div>
                <div class="collection">
                    <span>Download</span>
                    <span>201 MB</span>
                </div>
                <div class="collection">
                    <span>Explore</span>
                    <span>133 MB</span>
                </div>
            </div>

            <!-- Recent Bookmarks -->
            <div class="bookmarks">
                <h3>Recent Bookmarks</h3>
                {generate_bookmarks(chat_id, user_links, link_metadata)}
            </div>
        </div>

        <!-- Bottom Navigation -->
        <div class="bottom-nav">
            <div class="nav-item">
                <i>🏠</i>
                <p>Home</p>
            </div>
            <div class="nav-item">
                <i>➕</i>
                <p>Add</p>
            </div>
            <div class="nav-item">
                <i>⚙️</i>
                <p>Settings</p>
            </div>
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

def generate_bookmarks(chat_id, user_links, link_metadata):
    bookmarks_html = ""
    for i, link in enumerate(user_links.get(chat_id, [])):
        metadata = link_metadata.get(chat_id, [])[i] if i < len(link_metadata.get(chat_id, [])) else {}

        # Truncate the title to 100 characters and add ellipsis if longer
        title = metadata.get('title', 'Untitled')[:100] + ("..." if len(metadata.get('title', '')) > 100 else "")

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
