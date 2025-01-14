import os
from datetime import datetime

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
                padding: 16px;
                display: flex;
                align-items: flex-start;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                transition: transform 0.2s;
                position: relative;
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
                word-wrap: break-word;
                max-width: 100%;
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
            .add-tag {
                background-color: #d4edda;
                color: #155724;
                padding: 4px 8px;
                font-size: 0.8rem;
                border-radius: 12px;
                cursor: pointer;
                border: 1px solid #c3e6cb;
            }
            .delete-link {
                position: absolute;
                bottom: 8px;
                left: 8px;
                color: #b00;
                padding: 4px 8px;
                font-size: 0.8rem;
                cursor: pointer;
            }
            .delete-all {
                background-color: #f8d7da;
                color: #721c24;
                padding: 10px 20px;
                border: 1px solid #f5c6cb;
                border-radius: 8px;
                cursor: pointer;
                margin-top: 16px;
                display: block;
                text-align: center;
            }
            .delete-all:hover {
                background-color: #f5c6cb;
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
                f'<span class="add-tag" onclick="openTagDialog({link.id})">+</span>' +
                "</div>"
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
            <div class="bookmark" data-tags="{tags_attr}" data-id="{link.id}">
                {image_html}
                <div class="bookmark-content">
                    <h3><a href="{metadata.get('url', link.link)}" target="_blank">{metadata.get('title', 'Untitled')[:100]}</a></h3>
                    <p>{(metadata.get('description') or '')[:200] + ("..." if metadata.get('description') and len(metadata.get('description')) > 200 else "")}</p>
                    {price_html}
                    {tags_html}
                    {created_at_html}
                </div>
                <span class="delete-link" onclick="deleteLink({link.id})">🗑️</span>
            </div>
            """
        return cards_html

    def generate_scripts(chat_id):
        return f"""
        <script>
            const chatId = "{chat_id}";
    
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
    
            function deleteAllLinks() {
                if (confirm("Are you sure you want to delete all links and tags? This action cannot be undone.")) {
                    fetch(`/delete_all/${chatId}`, { method: "DELETE" })
                        .then(response => response.json())
                        .then(data => {
                            if (data.message === "All links and tags deleted successfully!") {
                                alert(data.message);
                                location.reload(); // Reload the page to reflect the changes
                            } else {
                                alert(data.error || "Failed to delete all links.");
                            }
                        })
                        .catch(error => {
                            console.error("Error deleting all links:", error);
                            alert("An error occurred while deleting all links and tags.");
                        });
                }
            }
    
            function openTagDialog(linkId) {
                const existingTags = Array.from(document.querySelectorAll('.filter:not(.active)')).map(tag => tag.innerText);
                let tag = prompt(`Choose Existing tag:\n${existingTags.join(', ')}\n Or enter manually`, "");
    
                if (tag) {
                    fetch(`/add_tag/${linkId}`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({ tag: tag })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.message === "Tag added successfully!") {
                            const bookmark = document.querySelector(`.bookmark[data-id="${linkId}"]`);
                            if (bookmark) {
                                const tagsContainer = bookmark.querySelector('.tags');
                                const newTagHtml = `<span class="tag">${tag}</span>`;
                                tagsContainer.insertAdjacentHTML('beforeend', newTagHtml);
                            }
                        } else {
                            alert("Failed to add tag.");
                        }
                    })
                    .catch(error => {
                        console.error("Error adding tag:", error);
                        alert("An error occurred while adding the tag.");
                    });
                }
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
            {generate_tag_filters()}
            <div class="bookmarks">
                {generate_bookmark_cards()}
            </div>
            <div class="actions">
                <button class="delete-all" onclick="deleteAllLinks()">Delete All Links</button>
            </div>
        </div>
        {generate_scripts(chat_id)}
    </body>
    </html>
    """

    # Save the HTML file
    file_path = os.path.join(directory, f"{chat_id}_history.html")
    with open(file_path, "w") as file:
        file.write(history_html)

    return f"https://flask-production-4c83.up.railway.app/storage/links_history/{chat_id}_history.html"


