#!/usr/bin/env python3

import json
import os
import shlex, subprocess
import re
import argparse
from pathlib import Path

# Default Val
default_dmenu_cmd = "wofi --show dmenu" # Wofi
default_dmenu_title_arg = ""
default_dmenu_extra_arg = ""
default_name = "FuzzyMarks"
home_dir = Path.home()
default_bookmark = home_dir / ".config/{}/bookmarks.json".format(default_name)
default_config = home_dir / ".config/{}/config.json".format(default_name)
default_cmd_browser_open = "firefox"
default_title_content = "Select Bookmark!"
default_head_for_page = ""
default_head_for_tag = "*"
default_search_engine_path = "https://google.de/search?q=" # Google Search

# Json File Attr Name
## bookmarks.json
attr_url = "url"
attr_next = "next"
## config.json
attr_browser_open_cmd = "browser-open-cmd"
attr_head_for_page = "head-for-page"
attr_head_for_tag = "head-for-folder"
attr_dmenu_cmd = "dmenu-cmd"
attr_dmenu_title_arg = "dmenu-title-arg"
attr_dmenu_extra_arg = "dmenu-extra-arg"
attr_title_content = "title-content"
attr_search_engine_parh = "search-engine-parh"
attr_config:list[str] = [
    attr_browser_open_cmd,
    attr_head_for_page,
    attr_head_for_tag,
    attr_dmenu_cmd,
    attr_dmenu_title_arg,
    attr_dmenu_extra_arg,
    attr_search_engine_parh,
    attr_title_content
]

# Log Message
log_bookmark_not_exist = "[ERROR] Bookmarks file not exist!"
log_config_not_exist = "[WARN] Config file not exist!"

class Config:
    def __init__(self, bookmarks_dir:str=default_bookmark, config_dir:str=default_config) -> None:
        self.bookmarks_dir:str = bookmarks_dir
        self.config_dir:str = config_dir
        self.bookmarks:dict[int, dict[str, Option]] = {}
        self.config_item:dict[str, str] = {
            attr_browser_open_cmd: default_cmd_browser_open,
            attr_head_for_page: default_head_for_page,
            attr_head_for_tag: default_head_for_tag,
            attr_dmenu_cmd: default_dmenu_cmd,
            attr_dmenu_title_arg: default_dmenu_title_arg,
            attr_dmenu_extra_arg: default_dmenu_extra_arg,
            attr_search_engine_parh: default_search_engine_path,
            attr_title_content: default_title_content,
        }

    def build_bookmarks(self, bookmarks_json:dict) -> None:
        for key, _ in bookmarks_json.items():
            self.bookmarks.update({ int(key): {} })
            opt_dict = bookmarks_json.get(key)
            assert opt_dict != None
            for opt_key, _ in opt_dict.items():
                opt_item = opt_dict.get(opt_key)
                assert opt_item != None
                opt = Option(name=opt_key, url=opt_item.get(attr_url), next=int(opt_item.get(attr_next)))
                cur_dict = self.bookmarks.get(int(key)) 
                assert cur_dict != None
                if opt.next == -1:
                    cur_dict.update({
                        '{}{}'.format(self.config_item.get(attr_head_for_page), opt_key): opt
                    })
                else:
                    cur_dict.update({
                        '{}{}'.format(self.config_item.get(attr_head_for_tag), opt_key): opt
                    })

    def build_config(self, config_json) -> None:
        for attr in attr_config:
            if config_json.get(attr) != None:
                self.config_item.update({
                    attr: config_json.get(attr)
                })

    # Disk IO
    def update(self) -> bool:
        try:
            bookmark_fd = open(self.bookmarks_dir, mode="r")
        except IOError:
            print(log_bookmark_not_exist)
            return False
        try:
            config_fd = open(self.config_dir, mode="r")
        except IOError:
            print(log_config_not_exist)
        else:
            # Setup Config
            config_js = json.load(config_fd)
            config_fd.close()
            self.build_config(config_json=config_js)
        # Setup Bookmark
        bookmark_json = json.load(bookmark_fd)
        bookmark_fd.close()
        self.build_bookmarks(bookmark_json)
        # print(self.bookmarks)
        return True

class Option:
    def __init__(self, name:str='', url:str='', next:int=-1) -> None:
        self.name = name
        self.url = url
        self.next = next
    def __lt__(self, other):
        if self.next < 0 and other.next >= 0: # self -> page, other -> tag
            return False
        elif self.next >= 0 and other.next < 0: # self -> tag, other -> page
            return True
        else:
            return (self.name < other.name)

class Utils:
    @staticmethod
    def build_string_input(input_list:list[str]) -> str:
        res = ''
        for i in input_list:
            if i == input_list[0]:
                res += i
            else:
                res += '\n{}'.format(i)
        return res

    @staticmethod
    def subprocess_run_no_input(cmd:str) -> str:
        p = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE)
        return p.stdout.decode('utf-8')

    @staticmethod
    def subprocess_run_input(cmd:str, input:str) -> str:
        p = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, input=input.encode())
        return p.stdout.decode('utf-8')

    @staticmethod
    def build_dmenu_cmd_with_title(title:str, config:Config) -> str:
        dmenu_cmd = config.config_item.get(attr_dmenu_cmd)
        dmenu_title_arg = config.config_item.get(attr_dmenu_title_arg)
        dmenu_extra_arg = config.config_item.get(attr_dmenu_extra_arg)
        if dmenu_title_arg:
            return '{} {} "{}" {}'.format(dmenu_cmd, dmenu_title_arg, title, dmenu_extra_arg)
        else:
            return '{} {}'.format(dmenu_cmd, dmenu_extra_arg)

class Main:
    def __init__(self, config: Config) -> None:
        self.config: Config = config
        self.bookmarks = config.bookmarks

    def run(self) -> None:
        respond:int = 0
        while respond >= 0 :
            respond = self.execute(index=respond)

    def show_options(self, options:(dict[str, Option] | None)) -> tuple[int, Option]:
        if options != None:
            input_list:list[str] = []
            for opt_name, _ in options.items():
                input_list.append(opt_name)
            title = self.config.config_item.get(attr_title_content)
            assert title != None
            select = Utils.subprocess_run_input(cmd=Utils.build_dmenu_cmd_with_title(title=title, config=self.config), input=Utils.build_string_input(input_list)).strip('\n')
            select_opt = options.get(select)
            if select_opt != None:
                next = select_opt.next
                return int(next), select_opt
            elif select:
                return -2, Option(url=select, next=-1)
        return -3, Option()

    def open_web(self, url:str="") -> None:
        cmd_browser_open = self.config.config_item.get(attr_browser_open_cmd)
        os.system(command='{} "{}" &'.format(cmd_browser_open, url))

    def execute(self, index:int) -> int:
        if index >= 0:
            vals = self.config.bookmarks.get(index)
            next, select = self.show_options(vals)
            if next >= 0:
                return next
            elif next == -1:
                self.open_web(url=select.url)
            elif next == -2:
                search_content = re.sub(r'\s+', '+', select.url.strip())
                url = '{}{}'.format(self.config.config_item.get(attr_search_engine_parh), search_content)
                self.open_web(url=url)
        return -1

class Parser:
    def __init__(self):
        self.args = self._parse_arguments()

    def _valid_file(self, path):
        """Checks if the path is a valid file."""
        if os.path.isfile(path):
            return path
        else:
            raise argparse.ArgumentTypeError(f"'{path}' is not a valid file.")

    def _parse_arguments(self):
        parser = argparse.ArgumentParser(
            description="A Bookmarks Selector",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument(
            '-b', '--bookmark_file',
            type=self._valid_file,
            default=default_bookmark,
            help='Path to the bookmark file'
        )
        parser.add_argument(
            '-c', '--config_file',
            default=default_config,
            help='Path to the config file'
        )
        return parser.parse_args()

    def get_bookmark_file(self):
        return self.args.bookmark_file

    def get_config_file(self):
        return self.args.config_file


if __name__== "__main__" :
    parser = Parser()
    config = Config(bookmarks_dir=parser.get_bookmark_file(), config_dir=parser.get_config_file())
    if config.update() == True:
        app = Main(config=config)
        app.run()
