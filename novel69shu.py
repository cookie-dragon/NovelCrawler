#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time:    2019/9/8 14:06
# @Author:  Cooky Long
# @File:    novel69shu.py
from novel import Novel


class Novel69Shu(Novel):

    def __init__(self, bookid):
        Novel.__init__(self, bookid)
        self.urlheader = 'https://www.69shu.io'
        self.blackliststrline = ['一秒记住【69书吧www.69shu.io】，更新快，无弹窗，免费读！']
        self.blackliststr = []

    def _igetintro(self):
        intro = {}
        url = self.urlheader + '/book/' + self.bookid + '/'
        soup = self._getsoup(url, encoding='gbk')
        book_info = soup.html.body(
            'div', {'class': 'box nopad border', 'id': 'box-info'})[0](
            'div', {'class': 'book_info'})[0]
        intro['coverurl'] = book_info(
            'div', {'class': 'pic'})[0].img['src'].strip()
        info = book_info(
            'div', {'id': 'info'})[0]
        intro['title'] = info.h1.text.strip()
        intro['author'] = info(
            'div', {'class': 'options'})[0](
            'span', {'class': 'item'})[0].a.text.strip()
        intro['desc'] = info(
            'div', {'class': 'bookinfo_intro'})[0].text.strip()
        return intro

    def _igetchapters(self):
        url = self.urlheader + '/book/' + self.bookid + '/'
        soup = self._getsoup(url, encoding='gbk')
        lis = soup.html.body(
            'div', {'class': 'box nopad border'})[1](
            'div', {'class': 'book_list'})[0](
            'ul', {'class': 'chapterlist'})[0]('li', {'class': False})

        for li in lis:
            if li.a:
                chapterurl = self.urlheader + '/book/' + self.bookid + '/' + li.a['href']
                chaptertitle = li.a.text.strip()
                chapter = self.Chapter(title=chaptertitle, url=chapterurl)
                self.chapterlist.append(chapter)

    def _igetchapter(self, chapter):
        soup = self._getsoup(chapter.url, encoding='gbk')
        contentbox = soup.html.body(
            'div', {'class': 'box nopad border'})[0](
            'div', {'class': 'ncon', 'id': 'content'})[0](
            'div', {'class': 'nc_l', 'id': 'jsnc_l'})[0](
            'div', {'class': 'wrapper_main'})[0](
            'div', {'class': 'contentbox clear', 'id': 'htmlContent'})[0]
        textlines = contentbox(text=True)
        for line in textlines:
            if line not in self.blackliststrline:
                line = line.replace('\r', '').replace('\n', '').replace('\t', '').replace(' ', '').strip()
                if line not in self.blackliststrline:
                    if line != '':
                        for blackstr in self.blackliststr:
                            if blackstr in line:
                                line.replace(blackstr, '')
                        chapter.text.append(line)


if __name__ == '__main__':
    Novel69Shu(bookid='110530').build()
