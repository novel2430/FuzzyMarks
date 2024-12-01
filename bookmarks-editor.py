#!/usr/bin/env python3

import argparse
import json
import os

DEFAULT_PATH = "~/.config/FuzzyMarks/bookmarks.json"

# ANSI escape codes for colors
GREEN = "\033[32m"
RESET = "\033[0m"

def load_bookmarks(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, 'r') as file:
        return json.load(file)

def save_bookmarks(file_path, bookmarks):
    with open(file_path, 'w') as file:
        json.dump(bookmarks, file, indent=2)

def print_bookmarks(bookmarks, folder_id="0", prefix=""):
    if folder_id not in bookmarks:
        return
    folder = bookmarks[folder_id]
    for name, data in folder.items():
        url = data.get("url", "")
        if data.get("next", "") != "-1":
            next_folder = data.get("next", "")
            print(f"{prefix}|- {GREEN}[{next_folder}] {name}{RESET}")
            if next_folder != "-1" and next_folder in bookmarks:
                print_bookmarks(bookmarks, next_folder, prefix + "  ")
        else:
            print(f"{prefix}|- {name} ({url})")

def add_bookmark(bookmarks, parent_folder_id, name, url):
    bookmarks[parent_folder_id][name] = {"url": url, "next": "-1"}

def add_folder(bookmarks, parent_folder_id, name):
    new_id = str(max([int(folder_id) for folder_id in bookmarks.keys()] + [0]) + 1)
    bookmarks[parent_folder_id][name] = {"url": "", "next": new_id}
    bookmarks[new_id] = {}
    return new_id

def delete_bookmark(bookmarks, folder_id, name):
    if folder_id in bookmarks and name in bookmarks[folder_id]:
        del bookmarks[folder_id][name]
    else:
        print(f"Bookmark '{name}' not found in folder '{folder_id}'.")

def delete_folder(bookmarks, folder_id):
    def recursive_delete(f_id):
        if f_id in bookmarks:
            folder = bookmarks[f_id]
            for name, data in folder.items():
                next_folder = data.get("next", "")
                if next_folder != "-1":
                    recursive_delete(next_folder)  # delete sub folder
            del bookmarks[f_id]
    # Delete Parent Folder
    for parent_id, folder in bookmarks.items():
        for name, data in folder.items():
            if data.get("next", "") == folder_id:
                del folder[name]
                break
    recursive_delete(folder_id)


def valid_file(path):
    if os.path.isfile(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"'{path}' is not a valid file.")


def main():
    parser = argparse.ArgumentParser(description="Manage bookmarks in bookmarks.json.")
    parser.add_argument("-p", "--path", help="Path to the bookmarks.json file",type=valid_file, default=DEFAULT_PATH)
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    # Add bookmark command
    add_parser = subparsers.add_parser("add_bookmark", help="Add a bookmark")
    add_parser.add_argument("parent_folder", help="Parent folder ID")
    add_parser.add_argument("name", help="Bookmark name")
    add_parser.add_argument("url", help="Bookmark URL")
    # Add folder command
    add_folder_parser = subparsers.add_parser("add_folder", help="Add a folder")
    add_folder_parser.add_argument("parent_folder", help="Parent folder ID")
    add_folder_parser.add_argument("name", help="Folder name")
    # Print bookmarks command
    subparsers.add_parser("print", help="Print bookmarks in tree format")
    # Delete bookmark command
    delete_parser = subparsers.add_parser("del_bookmark", help="Delete a bookmark")
    delete_parser.add_argument("folder", help="Parent Folder ID")
    delete_parser.add_argument("name", help="Bookmark name")
    # Delete folder command
    delete_folder_parser = subparsers.add_parser("del_folder", help="Delete a folder")
    delete_folder_parser.add_argument("folder", help="Folder ID")
    args = parser.parse_args()
    # Load bookmarks
    bookmarks = load_bookmarks(args.path)
    if args.command == "add_bookmark":
        add_bookmark(bookmarks, args.parent_folder, args.name, args.url)
        save_bookmarks(args.path, bookmarks)
        print(f"Bookmark '{args.name}' added to folder '{args.parent_folder}'.")
    elif args.command == "add_folder":
        new_id = add_folder(bookmarks, args.parent_folder, args.name)
        save_bookmarks(args.path, bookmarks)
        print(f"Folder '{args.name}' added to folder '{args.parent_folder}' with ID {new_id}.")
    elif args.command == "print":
        print(f"{GREEN}[0] Root{RESET}")
        print_bookmarks(bookmarks)
    elif args.command == "del_bookmark":
        delete_bookmark(bookmarks, args.folder, args.name)
        save_bookmarks(args.path, bookmarks)
        print(f"Bookmark '{args.name}' deleted from folder '{args.folder}'.")
    elif args.command == "del_folder":
        delete_folder(bookmarks, args.folder)
        save_bookmarks(args.path, bookmarks)
        print(f"Folder '{args.folder}' delete.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

