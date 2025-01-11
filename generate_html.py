import os

def generate_html(chat_id, user_links, link_metadata, first_name):
    """Generate a mobile-friendly HTML file with link history and metadata."""
    # Ensure the directory exists
    directory = "/app/storage/links_history"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Start generating the HTML content
    history_html = f"""
    <html>
    <head>
        <title>{first_name}'s Link History</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                background-color: #f4f7f6;
                margin: 0;
                padding: 0;
                color: #333;
                font-family: Arial, sans-serif;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #fff;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }}
            h1 {{
                color: #2c3e50;
                text-align: center;
                font-size: 1.8rem;
                margin-bottom: 15px;
            }}
            .sort-buttons {{
                text-align: center;
                margin-bottom: 15px;
            }}
            .sort-buttons button {{
                margin: 5px;
                padding: 10px 20px;
                font-size: 1rem;
                border: none;
                border-radius: 4px;
                background-color: #3498db;
                color: white;
                cursor: pointer;
            }}
            .sort-buttons button:hover {{
                background-color: #2980b9;
            }}
            .link-card {{
                background-color: #ecf0f1;
                margin: 15px 0;
                padding: 10px;
                border-radius: 4px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            }}
            .link-card h2 {{
                font-size: 1.2rem;
                color: #34495e;
                margin: 0 0 10px;
            }}
            .link-card p {{
                font-size: 0.9rem;
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
                font-size: 0.8rem;
                color: #7f8c8d;
                margin-top: 20px;
            }}
            @media (max-width: 768px) {{
                .container {{
                    padding: 10px;
                }}
                h1 {{
                    font-size: 1.5rem;
                }}
                .link-card {{
                    padding: 8px;
                }}
                .link-card h2 {{
                    font-size: 1rem;
                }}
            }}
        </style>
        <script>
            function sortLinks(criteria) {{
                const linkCards = Array.from(document.querySelectorAll('.link-card'));
                const container = document.querySelector('.link-cards-container');

                linkCards.sort((a, b) => {{
                    if (criteria === 'category') {{
                        return a.dataset.category.localeCompare(b.dataset.category);
                    }} else {{
                        return a.dataset.index - b.dataset.index;
                    }}
                }});

                container.innerHTML = '';
                linkCards.forEach(card => container.appendChild(card));
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <h1>{first_name}'s Link History</h1>
            <div class="sort-buttons">
                <button onclick="sortLinks('timeline')">Sort by Timeline</button>
                <button onclick="sortLinks('category')">Sort by Category</button>
            </div>
            <div class="link-cards-container">
    """

    # Loop through each link and its metadata
    for i, link in enumerate(user_links.get(chat_id, [])):
        metadata = link_metadata.get(chat_id, [])[i] if i < len(link_metadata.get(chat_id, [])) else {}

        history_html += f"""
        <div class="link-card" data-index="{i}" data-category="{metadata.get('category', 'Unknown')}">
            <h2><a href="{metadata.get('url', link)}" target="_blank">{metadata.get('title', 'Untitled')}</a></h2>
            <p><strong>Category:</strong> {metadata.get('category', 'Unknown')}</p>
            <p><strong>Description:</strong> {metadata.get('description', 'No description available.')}</p>
            {"<p><strong>Price:</strong> $" + metadata['price'] + "</p>" if "price" in metadata else ""}
            {"<p><strong>Content:</strong> " + metadata['content'][:200] + "...</p>" if "content" in metadata else ""}
        </div>
        """

    # Add footer and close HTML tags
    history_html += """
            </div>
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
