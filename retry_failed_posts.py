#!/usr/bin/env python3
"""
Script to retry migrating failed Hugo blog posts to Notion database.
"""

import os
import time
from migrate_to_notion import (
    process_markdown_file,
    create_notion_page,
    OLD_CONTENT_DIR
)

# List of posts that failed in the previous run
FAILED_POSTS = [
    "2020-02-19-menu-cost-in-digital-age",
    "2020-03-04-python-r-online",
    "2020-01-30-vscode-markdown-writing",
    "2018-11-14-posting-from-rstudio",
    "2020-02-03-hcode-bcode",
    "2020-07-06-python-dash",
    "2020-10-05-the-1hour-workday",
    "2020-02-18-aws-lambda-bot",
    "2020-07-08-3dollar-hosting"
]

def main():
    """Retry migrating failed posts with a delay between attempts."""
    successful_retries = 0
    
    print(f"Retrying migration for {len(FAILED_POSTS)} failed posts...")
    
    for post_dir in FAILED_POSTS:
        folder_path = os.path.join(OLD_CONTENT_DIR, post_dir)
        md_path = os.path.join(folder_path, "index.md")
        
        if os.path.exists(md_path):
            print(f"Processing {post_dir}...")
            
            # Extract content and metadata
            frontmatter, content = process_markdown_file(md_path)
            
            # Create Notion page with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    page_id = create_notion_page(frontmatter, content, folder_path)
                    
                    if page_id:
                        successful_retries += 1
                        print(f"Successfully created Notion page for {post_dir} (ID: {page_id})")
                        break
                    else:
                        print(f"Failed to create Notion page for {post_dir} (attempt {attempt+1}/{max_retries})")
                except Exception as e:
                    print(f"Error on attempt {attempt+1}/{max_retries}: {e}")
                
                # Wait before retrying to avoid rate limits
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)  # Exponential backoff
                    print(f"Waiting {wait_time} seconds before retrying...")
                    time.sleep(wait_time)
            
            # Add a delay between posts to avoid rate limits
            time.sleep(3)
        else:
            print(f"Skipping {post_dir} (no index.md found)")
    
    # Print statistics
    print("\nRetry complete!")
    print(f"Total failed posts: {len(FAILED_POSTS)}")
    print(f"Successfully migrated on retry: {successful_retries}")
    print(f"Still failed: {len(FAILED_POSTS) - successful_retries}")

if __name__ == "__main__":
    main()
