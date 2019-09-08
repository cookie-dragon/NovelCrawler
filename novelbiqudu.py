#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time:    2019/9/8 12:19
# @Author:  Cooky Long
# @File:    novelbiqudu.py
from novel import Novel


class NovelBiqudu(Novel):

    def __init__(self, bookid):
        Novel.__init__(self, bookid)
        self.urlheader = 'https://www.biqudu.net'
        self.blackliststrline = ['readx();', 'chaptererror();']
        self.blackliststr = []

    def _igetintro(self):
        intro = {}
        url = self.urlheader + '/' + self.bookid + '/'
        soup = self._getsoup(url)
        box_con0 = soup.html.body(
            'div', {'id': 'wrapper'})[0](
            'div', {'class': 'box_con'})[0]
        intro['coverurl'] = self.urlheader + box_con0(
            'div', {'id': 'sidebar'})[0](
            'div', {'id': 'fmimg'})[0].img['src'].strip()
        info = box_con0(
            'div', {'id': 'maininfo'})[0](
            'div', {'id': 'info'})[0]
        intro['title'] = info.h1.text.strip()
        intro['author'] = info.p.text.strip()
        intro['author'] = intro['author'][intro['author'].find(u'：') + 1:]
        intro['desc'] = box_con0(
            'div', {'id': 'maininfo'})[0](
            'div', {'id': 'intro'})[0].text.strip()
        return intro

    def _igetchapters(self):
        url = self.urlheader + '/' + self.bookid + '/'
        soup = self._getsoup(url)
        dtdds = soup({'dt': True, 'dd': True})
        passednewest = 2
        for dtdd in dtdds:
            if passednewest > 0:
                if dtdd.name == 'dt':
                    passednewest -= 1
            else:
                if dtdd.name == 'dd':
                    chapterurl = self.urlheader + dtdd.a['href']
                    chaptertitle = dtdd.a.text.strip()
                    chapter = self.Chapter(title=chaptertitle, url=chapterurl)
                    self.chapterlist.append(chapter)

    def _igetchapter(self, chapter):
        soup = self._getsoup(chapter.url)
        box_con = soup.html.body(
            'div', {'id': 'wrapper'})[0](
            'div', {'class': 'content_read'})[0](
            'div', {'class': 'box_con'})[0]
        chapter.titlein = box_con('div', {'class': 'bookname'})[0].h1.text.strip()
        textlines = box_con('div', {'id': 'content'})[0](text=True)
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
    NovelBiqudu(bookid='133_133265').build()
