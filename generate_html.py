import os
from datetime import datetime, timedelta

def generate_html(chat_id, user_links, link_metadata, first_name):
    """Generate a mobile-friendly HTML file with link history and metadata."""
    directory = "/app/storage/links_history"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Extract all unique tags
    all_tags = sorted(set(tag for metadata in link_metadata for tag in metadata.get("tags", [])))

    def generate_styles():
        return """
        <style>
            body {
                margin: 0;
                font-family: Arial, sans-serif;
                background-color: #f9f9f9;
                color: #333;
            }
            .container {
                padding: 16px;
            }
            .profile {
                margin-bottom: 16px;
                text-align: center;
            }
            .profile h2 {
                margin: 0;
                font-size: 24px;
                color: #2c3e50;
            }
            .filters {
                margin-bottom: 16px;
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                justify-content: center;
            }
            .filter {
                background-color: #e0f7fa;
                color: #00796b;
                padding: 6px 12px;
                font-size: 0.9rem;
                border-radius: 12px;
                cursor: pointer;
                user-select: none;
            }
            .filter.active {
                background-color: #00796b;
                color: #ffffff;
            }
            .bookmarks {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 16px;
            }
            .bookmark {
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 16px;
                display: flex;
                align-items: flex-start;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                transition: transform 0.2s;
            }
            .bookmark:hover {
                transform: translateY(-5px);
            }
            .bookmark img {
                width: 70px;
                height: 70px;
                object-fit: cover;
                border-radius: 4px;
                margin-right: 12px;
                border: 1px solid #ddd;
            }
            .bookmark-content {
                flex: 1;
            }
            .bookmark h3 {
                font-size: 1rem;
                color: #3498db;
                margin: 0;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: normal;
                word-wrap: break-word; /* Prevent overflow */
                max-width: 100%; /* Ensure the title doesn't exceed the card width */
            }
            .bookmark h3 a {
                text-decoration: none;
                color: inherit;
            }
            .bookmark h3 a:hover {
                text-decoration: underline;
            }
            .bookmark p {
                font-size: 0.9rem;
                color: #555;
                margin: 8px 0 0;
            }
            .price {
                font-weight: bold;
                color: #27ae60;
                margin-top: 8px;
            }
            .tags {
                margin-top: 8px;
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }
            .tag {
                background-color: #e0f7fa;
                color: #00796b;
                padding: 4px 8px;
                font-size: 0.8rem;
                border-radius: 12px;
                display: inline-block;
            }
        </style>
        """


    def generate_tag_filters():
        filters_html = '<div class="filters">'
        filters_html += '<span class="filter active" onclick="filterByTag(\'all\')">All</span>'
        for tag in all_tags:
            filters_html += f'<span class="filter" onclick="filterByTag(\'{tag}\')">{tag}</span>'
        filters_html += '</div>'
        return filters_html

    def generate_bookmark_cards():
        cards_html = ""
        current_time = datetime.now()
    
        for link, metadata in zip(user_links, link_metadata):
            # Handle images
            images = metadata.get("images", [])
            image_html = f'<img src="{images[0]}" alt="Image">' if images else ""
    
            # Format price if available
            price = metadata.get("price", None)
            price_html = f'<p class="price">Price: ${price}</p>' if price and price != "N/A" else ""
    
            # Handle tags
            tags = metadata.get("tags", [])
            tags_html = (
                '<div class="tags">' +
                "".join([f'<span class="tag">{tag}</span>' for tag in tags]) +
                "</div>"
                if tags else ""
            )
    
            # Format creation time
            created_at = metadata.get("created_at")
            created_at_html = ""
            if created_at:
                days_difference = (current_time - created_at).days
                if days_difference == 0:
                    formatted_time = created_at.strftime("%d/%m/%y %H:%M")
                elif days_difference == 1:
                    formatted_time = created_at.strftime("%d/%m/%y")
                else:
                    formatted_time = f"{days_difference} days ago"
                created_at_html = f'<p style="text-align: right; font-size: 0.8rem; color: #888;">{formatted_time}</p>'
    
            # Generate card
            tags_attr = " ".join(tags)
            cards_html += f"""
            <div class="bookmark" data-tags="{tags_attr}">
                {image_html}
                <div class="bookmark-content">
                    <h3><a href="{metadata.get('url', link.link)}" target="_blank">{metadata.get('title', 'Untitled')[:150]}</a></h3>
                    <p>{metadata.get('description', '')}</p>
                    {price_html}
                    {tags_html}
                    {created_at_html}
                </div>
            </div>
            """
        return cards_html

    def generate_scripts():
        return """
        <script>
            function filterByTag(tag) {
                const bookmarks = document.querySelectorAll('.bookmark');
                const filters = document.querySelectorAll('.filter');

                // Update active filter
                filters.forEach(filter => filter.classList.remove('active'));
                document.querySelector(`.filter[onclick="filterByTag('${tag}')"]`).classList.add('active');

                // Filter bookmarks
                bookmarks.forEach(bookmark => {
                    const tags = bookmark.getAttribute('data-tags').split(' ');
                    if (tag === 'all' || tags.includes(tag)) {
                        bookmark.style.display = 'flex';
                    } else {
                        bookmark.style.display = 'none';
                    }
                });
            }
        </script>
        """

    # Build HTML
    history_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{first_name}'s Bookmarks</title>
        {generate_styles()}
    </head>
    <body>
        <div class="container">
            <div class="profile">
                <h2>{first_name}'s Bookmarks</h2>
            </div>
            {generate_tag_filters()}
            <div class="bookmarks">
                {generate_bookmark_cards()}
            </div>
        </div>
        {generate_scripts()}
    </body>
    </html>
    """

    # Save the HTML file
    file_path = os.path.join(directory, f"{chat_id}_history.html")
    with open(file_path, "w") as file:
        file.write(history_html)

    return f"https://flask-production-4c83.up.railway.app/storage/links_history/{chat_id}_history.html"

