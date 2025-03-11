#!/usr/bin/env python3
"""
Script to migrate old Hugo blog posts to Notion database.
"""

import os
import re
import sys
import yaml
import base64
from pathlib import Path
from datetime import datetime
from notion_client import Client

# Configuration
NOTION_DATABASE_ID = "eb897916879243289a3612c1b793c43f"
OLD_CONTENT_DIR = "old_content/post"

# Initialize Notion client
notion = Client(auth=os.environ["NOTION_TOKEN"])

def extract_frontmatter(content):
    """Extract YAML frontmatter from markdown content."""
    pattern = r"^---\s*\n(.*?)\n---\s*\n"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        frontmatter_text = match.group(1)
        try:
            frontmatter = yaml.safe_load(frontmatter_text)
            # Extract content after frontmatter
            content_text = content[match.end():]
            return frontmatter, content_text
        except yaml.YAMLError as e:
            print(f"Error parsing YAML frontmatter: {e}")
            return {}, content
    return {}, content

def process_markdown_file(file_path):
    """Process a markdown file and extract its content and metadata."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        frontmatter, content_text = extract_frontmatter(content)
        return frontmatter, content_text
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return {}, ""

def find_images_in_content(content, folder_path):
    """Find image references in content and return their paths."""
    # Match markdown image syntax: ![alt text](/path/to/image.jpg)
    image_pattern = r"!\[(.*?)\]\((.*?)\)"
    images = []
    
    for match in re.finditer(image_pattern, content):
        image_path = match.group(2)
        
        # Handle relative paths
        if image_path.startswith('/'):
            # Remove leading slash for relative path
            image_path = image_path[1:]
        
        # Check if the image exists in the post folder
        local_image_path = os.path.join(folder_path, os.path.basename(image_path))
        if os.path.exists(local_image_path):
            images.append(local_image_path)
        elif os.path.exists(os.path.join(folder_path, image_path)):
            images.append(os.path.join(folder_path, image_path))
        
    return images

def upload_image_to_notion(image_path):
    """Upload an image to Notion and return the URL."""
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Get file extension and determine MIME type
        file_ext = os.path.splitext(image_path)[1].lower()
        mime_type = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }.get(file_ext, 'application/octet-stream')
        
        # Encode image data as base64
        encoded_image = base64.b64encode(image_data).decode('utf-8')
        
        # Create a file block in Notion
        response = notion.blocks.children.append(
            block_id=NOTION_DATABASE_ID,
            children=[
                {
                    "object": "block",
                    "type": "image",
                    "image": {
                        "type": "external",
                        "external": {
                            "url": f"data:{mime_type};base64,{encoded_image}"
                        }
                    }
                }
            ]
        )
        
        # Return the URL of the uploaded image
        return response["results"][0]["image"]["external"]["url"]
    except Exception as e:
        print(f"Error uploading image {image_path}: {e}")
        return None

def split_content_into_chunks(content, max_length=1900):
    """Split content into chunks of max_length characters."""
    # Split by paragraphs first
    paragraphs = content.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If paragraph is too long, split it further
        if len(paragraph) > max_length:
            # Add current chunk if not empty
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
            # Split long paragraph into smaller chunks
            words = paragraph.split(' ')
            temp_chunk = ""
            
            for word in words:
                if len(temp_chunk) + len(word) + 1 <= max_length:
                    temp_chunk += (" " + word if temp_chunk else word)
                else:
                    chunks.append(temp_chunk)
                    temp_chunk = word
            
            if temp_chunk:
                chunks.append(temp_chunk)
        else:
            # If adding this paragraph would exceed max_length, start a new chunk
            if len(current_chunk) + len(paragraph) + 2 > max_length:
                chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                # Add paragraph to current chunk
                current_chunk += ("\n\n" + paragraph if current_chunk else paragraph)
    
    # Add the last chunk if not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def create_notion_page(frontmatter, content, folder_path):
    """Create a new page in the Notion database with the extracted content."""
    try:
        # Extract metadata from frontmatter
        title = frontmatter.get('title', os.path.basename(folder_path))
        date_str = frontmatter.get('date', '')
        tags = frontmatter.get('tags', [])
        categories = frontmatter.get('categories', [])
        draft = frontmatter.get('draft', False)
        subtitle = frontmatter.get('subtitle', '')
        summary = frontmatter.get('summary', '')
        author = frontmatter.get('author', '')
        
        # Convert date string to datetime object if it exists
        created_time = None
        if date_str:
            try:
                if isinstance(date_str, str):
                    # Try different date formats
                    for fmt in ['%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S %z', '%Y-%m-%d']:
                        try:
                            created_time = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                elif isinstance(date_str, datetime):
                    created_time = date_str
            except Exception as e:
                print(f"Error parsing date {date_str}: {e}")
        
        # Find images in content
        images = find_images_in_content(content, folder_path)
        
        # Prepare properties for Notion page
        properties = {
            "Name": {"title": [{"text": {"content": title}}]},
            "Status": {"status": {"name": "Done"}},
            "isPublished": {"checkbox": True},
            "draft": {"checkbox": draft}
        }
        
        # Add optional properties if they exist
        if subtitle:
            properties["Subtitle"] = {"rich_text": [{"text": {"content": subtitle}}]}
        
        if summary:
            properties["Description"] = {"rich_text": [{"text": {"content": summary}}]}
        
        if author:
            properties["Author"] = {"rich_text": [{"text": {"content": author}}]}
        
        if created_time:
            properties["Created time"] = {"date": {"start": created_time.isoformat()}}
        
        # Add tags if they exist
        if tags:
            # Convert tags to list if it's not already
            if not isinstance(tags, list):
                tags = [tags]
            
            # Limit to existing tags in the database
            tag_options = []
            for tag in tags:
                tag_options.append({"name": str(tag)})
            
            if tag_options:
                properties["Tags"] = {"multi_select": tag_options}
        
        # Add category if it exists
        if categories:
            # Use the first category if multiple are provided
            category = categories[0] if isinstance(categories, list) else categories
            properties["Category"] = {"select": {"name": str(category)}}
        
        # Create the page in Notion
        page = notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties=properties
        )
        
        # Split content into chunks to avoid the 2000 character limit
        content_chunks = split_content_into_chunks(content)
        
        # Create blocks for each content chunk
        blocks = []
        for chunk in content_chunks:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                }
            })
        
        # Add blocks to the page in batches to avoid API limits
        if blocks:
            for i in range(0, len(blocks), 50):  # Notion API has a limit of 100 blocks per request
                batch = blocks[i:i+50]
                notion.blocks.children.append(
                    block_id=page["id"],
                    children=batch
                )
        
        # For images, we'll add a note about them since direct upload is problematic
        if images:
            image_note = f"Note: This post contains {len(images)} images that couldn't be automatically uploaded due to Notion API limitations."
            notion.blocks.children.append(
                block_id=page["id"],
                children=[{
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [{"type": "text", "text": {"content": image_note}}],
                        "icon": {"emoji": "🖼️"}
                    }
                }]
            )
        
        return page["id"]
    except Exception as e:
        print(f"Error creating Notion page: {e}")
        return None

def main():
    """Main function to process all markdown files and migrate to Notion."""
    # Get all directories in the old_content/post directory
    post_dirs = [f for f in os.listdir(OLD_CONTENT_DIR) if os.path.isdir(os.path.join(OLD_CONTENT_DIR, f))]
    
    # Count for statistics
    total_posts = len(post_dirs)
    processed_posts = 0
    successful_posts = 0
    failed_posts = []
    
    print(f"Found {total_posts} post directories to process")
    
    # Process each directory
    for post_dir in post_dirs:
        folder_path = os.path.join(OLD_CONTENT_DIR, post_dir)
        
        # Check if the directory contains index.md
        md_path = os.path.join(folder_path, "index.md")
        html_path = os.path.join(folder_path, "index.html")
        
        # Skip directories with index.html as requested by the user
        if os.path.exists(html_path):
            print(f"Skipping {post_dir} (contains index.html)")
            continue
        
        # Process directories with index.md
        if os.path.exists(md_path):
            print(f"Processing {post_dir}...")
            processed_posts += 1
            
            # Extract content and metadata
            frontmatter, content = process_markdown_file(md_path)
            
            # Create Notion page
            page_id = create_notion_page(frontmatter, content, folder_path)
            
            if page_id:
                successful_posts += 1
                print(f"Successfully created Notion page for {post_dir} (ID: {page_id})")
            else:
                failed_posts.append(post_dir)
                print(f"Failed to create Notion page for {post_dir}")
        else:
            print(f"Skipping {post_dir} (no index.md or index.html found)")
    
    # Print statistics
    print("\nMigration complete!")
    print(f"Total posts: {total_posts}")
    print(f"Processed posts: {processed_posts}")
    print(f"Successfully migrated: {successful_posts}")
    print(f"Failed: {len(failed_posts)}")
    
    if failed_posts:
        print("\nFailed posts:")
        for post in failed_posts:
            print(f"- {post}")

if __name__ == "__main__":
    main()
