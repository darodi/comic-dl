#!/usr/bin/env python
# -*- coding: utf-8 -*-

import globalFunctions
import re
import os
import logging
import time

import js2py
import jsbeautifier
import requests


class MangaFox(object):
    def __init__(self, manga_url, download_directory, chapter_range, **kwargs):

        current_directory = kwargs.get("current_directory")
        conversion = kwargs.get("conversion")
        keep_files = kwargs.get("keep_files")
        self.logging = kwargs.get("log_flag")
        self.sorting = kwargs.get("sorting_order")
        self.comic_name = self.name_cleaner(manga_url)
        url_split = str(manga_url).split("/")
        self.print_index = kwargs.get("print_index")

        if len(url_split) is 5:
            self.full_series(comic_url=manga_url, comic_name=self.comic_name, sorting=self.sorting,
                             download_directory=download_directory, chapter_range=chapter_range, conversion=conversion,
                             keep_files=keep_files)
        else:
            self.single_chapter(manga_url, self.comic_name, download_directory, conversion=conversion,
                                keep_files=keep_files)

    def name_cleaner(self, url):
        initial_name = str(url).split("/")[4].strip()
        safe_name = re.sub(r"[0-9][a-z][A-Z]\ ", "", str(initial_name))
        manga_name = str(safe_name.title()).replace("_", " ")

        return manga_name

    def single_chapter(self, comic_url, comic_name, download_directory, conversion, keep_files):
        raise NotImplementedError('not implemented mangafox download')
        # source, cookies_main = globalFunctions.GlobalFunctions().page_downloader(manga_url=comic_url)
        #
        # s = str(source)
        # chapter_id = re.search(r"var chapterid =(\d*);", s).group(1)
        #
        # key_js = re.search(r'(eval\(function\(p,a,c,k,e,d\){.*)', s).group(1)
        # key = self.getkey(key_js)
        #
        # imagecount = re.search(r"var imagecount=(\d*);", s).group(1)
        #
        # # 'http://fanfox.net/manga/dungeon_meshi/vTBD/c049/1.html'
        # chapter_number = comic_url.split('/')[len(comic_url.split('/'))-2]
        #
        # file_directory = globalFunctions.GlobalFunctions().create_file_directory(chapter_number, comic_name)
        # # directory_path = os.path.realpath(file_directory)
        # directory_path = os.path.realpath(str(download_directory) + "/" + str(file_directory))
        #
        # if not os.path.exists(directory_path):
        #     os.makedirs(directory_path)
        #
        # links = []
        # file_names = []
        # for file_name in range(1, int(imagecount) + 1):
        #     ajax_url = "/chapterfun.ashx?cid=" + chapter_id + "&page=" + str(file_name) + "&key=" + key
        #     decode_url = re.sub("/[^/]*$", ajax_url, comic_url)
        #     image_link, cookies_main = self.get_image_link(decode_url, cookies_main)
        #     file_name_custom = str(
        #         globalFunctions.GlobalFunctions().prepend_zeroes(file_name, int(imagecount) + 1)) + ".jpg"
        #     file_names.append(file_name_custom)
        #     links.append(image_link)
        #
        # globalFunctions.GlobalFunctions().multithread_download(chapter_number, comic_name, comic_url, directory_path,
        #                                                        file_names, links, self.logging)
        #
        # globalFunctions.GlobalFunctions().conversion(directory_path, conversion, keep_files, comic_name,
        #                                              chapter_number)
        #
        # return 0

    def getkey(self, s):
        js = jsbeautifier.beautify(s)
        sub = re.sub(";\$.*", "", js)
        sub = re.sub("\\\\'", "", sub)
        sub = re.sub("\+", "", sub)
        sub = re.sub(".*?= ", "", sub)
        key = sub
        return key

    def full_series(self, comic_url, comic_name, sorting, download_directory, chapter_range, conversion, keep_files):
        # http://mangafox.la/rss/gentleman_devil.xml
        # Parsing RSS would be faster than parsing the whole page.
        rss_url = str(comic_url).replace("/manga/", "/rss/") + ".xml"
        source, cookies = globalFunctions.GlobalFunctions().page_downloader(manga_url=rss_url)

        # all_links = re.findall(r"href=\"(.*?)\" title=\"Thanks for", str(source))
        all_links_temp = re.findall(r"<link/>([^<]*?).html", str(source))
        all_links = [str(link) + ".html" for link in all_links_temp]

        logging.debug("All Links : %s" % all_links)

        # Uh, so the logic is that remove all the unnecessary chapters beforehand
        #  and then pass the list for further operations.
        if chapter_range != "All":
            # -1 to shift the episode number accordingly to the INDEX of it. List starts from 0 xD!
            starting = int(str(chapter_range).split("-")[0]) - 1

            if str(chapter_range).split("-")[1].isdigit():
                ending = int(str(chapter_range).split("-")[1])
            else:
                ending = len(all_links)

            indexes = [x for x in range(starting, ending)]

            all_links = [all_links[len(all_links) - 1 - x] for x in indexes][::-1]
        else:
            all_links = all_links

        if self.print_index:
            idx = len(all_links)
            for chap_link in all_links:
                print(str(idx) + ": " + str(chap_link))
                idx = idx - 1
            return

        if str(sorting).lower() in ['new', 'desc', 'descending', 'latest']:
            for chap_link in all_links:
                try:
                    self.single_chapter(comic_url=str(chap_link), comic_name=comic_name,
                                    download_directory=download_directory, conversion=conversion,
                                    keep_files=keep_files)
                except Exception as ex:
                    logging.error("Error downloading : %s" % chap_link)
                    logging.error(ex)
                    break  # break to continue processing other mangas when chapter doesn't contain images.
                # if chapter range contains "__EnD__" write new value to config.json
                if chapter_range != "All" and chapter_range.split("-")[1] == "__EnD__":
                    globalFunctions.GlobalFunctions().addOne(comic_url)

        elif str(sorting).lower() in ['old', 'asc', 'ascending', 'oldest', 'a']:
            for chap_link in all_links[::-1]:
                try:
                    self.single_chapter(comic_url=str(chap_link), comic_name=comic_name,
                                        download_directory=download_directory, conversion=conversion,
                                        keep_files=keep_files)
                except Exception as ex:
                    logging.error("Error downloading : %s" % chap_link)
                    logging.error(ex)
                    break  # break to continue processing other mangas when chapter doesn't contain images.
                # if chapter range contains "__EnD__" write new value to config.json
                if chapter_range != "All" and chapter_range.split("-")[1] == "__EnD__":
                    globalFunctions.GlobalFunctions().addOne(comic_url)
                # print("Waiting For 5 Seconds...")
                # time.sleep(5)  # Test wait for the issue #23

        return 0

    def get_image_link(self, decode_url, cookies_main):
        sess = requests.session()
        get = sess.get(decode_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0'},
                       cookies=cookies_main)
        source = get.text
        scrambled_js = str(source)
        js = jsbeautifier.beautify(scrambled_js)
        result = js2py.eval_js(js)
        return result[0], sess.cookies
