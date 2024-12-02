#!/usr/bin/env python3

import os
import json
import argparse

# Parse command-line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="Parse Chrome/Firefox bookmarks and convert them to FuzzyMarks JSON format.")
    parser.add_argument("-f", "--file", required=True, help="Path to the bookmarks JSON file.")
    parser.add_argument("-t", "--type", required=True, choices=["chrome", "firefox"], help="Browser type (chrome or firefox).")
    return parser.parse_args()

# Parse Firefox bookmarks (JSON file)
def parse_firefox_bookmarks(bookmark_file):
    with open(bookmark_file, 'r', encoding='utf-8') as file:
        bookmarks_data = json.load(file)

    custom_bookmarks = {}
    folder_id_map = {"0": {}}
    next_folder_id = 1

    def process_bookmark_node(node, parent_id):
        nonlocal next_folder_id

        if node['type'] == "text/x-moz-place-container":  # Folder
            folder_name = node['title']
            current_folder_id = str(next_folder_id)
            next_folder_id += 1

            folder_id_map[current_folder_id] = {}
            folder_id_map[parent_id][folder_name] = {"url": "", "next": current_folder_id}

            # Recursively process child nodes
            for child in node.get('children', []):
                process_bookmark_node(child, current_folder_id)

        elif node['type'] == "text/x-moz-place":  # Bookmark
            bookmark_name = node['title']
            bookmark_url = node['uri']
            folder_id_map[parent_id][bookmark_name] = {"url": bookmark_url, "next": "-1"}

    # Start processing from the root nodes
    for root_node in bookmarks_data.get('children', []):
        process_bookmark_node(root_node, "0")

    return folder_id_map

# Parse Chrome bookmarks (for comparison)
def parse_chrome_bookmarks(bookmark_file):
    with open(bookmark_file, 'r', encoding='utf-8') as file:
        bookmarks_data = json.load(file)
    roots = bookmarks_data.get('roots', {})
    bookmark_bar = roots.get('bookmark_bar', {})
    return convert_bookmarks_to_custom_format(bookmark_bar)

def convert_bookmarks_to_custom_format(bookmark_item, folder_id=0):
    custom_bookmarks = {}
    child_folder_id = folder_id + 1
    current_folder = {}

    for child in bookmark_item.get('children', []):
        if child['type'] == 'url':
            current_folder[child['name']] = {"url": child['url'], "next": "-1"}
        elif child['type'] == 'folder':
            current_folder[child['name']] = {"url": "", "next": str(child_folder_id)}
            custom_bookmarks.update(convert_bookmarks_to_custom_format(child, child_folder_id))
            child_folder_id += 1

    custom_bookmarks[str(folder_id)] = current_folder
    return custom_bookmarks

# Main function
def main():
    args = parse_arguments()
    bookmark_file = args.file
    browser_type = args.type

    if not os.path.isfile(bookmark_file):
        print(f"Error: Bookmarks file '{bookmark_file}' not found.")
        return

    if browser_type == "chrome":
        custom_format = parse_chrome_bookmarks(bookmark_file)
    elif browser_type == "firefox":
        custom_format = parse_firefox_bookmarks(bookmark_file)

    # Output custom JSON format
    print(json.dumps(custom_format, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    main()

