#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time:    2019/9/7 20:05
# @Author:  Cooky Long
# @File:    novel.py
import logging
import os
import shutil
import sys
import time
from subprocess import call
from xml.etree import ElementTree as etree
from xml.etree.ElementTree import QName

import requests
from bs4 import BeautifulSoup

from pyh import *

OUTPUTDIR = 'output'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)


class Novel(object):

    @staticmethod
    def titlefix(title):
        symbol = ['\\', '/', ':', '*', '?', '"', '<', '>', '|', '+']
        fixedsymbol = [' ', ' ', u'：', 'x', u'？', ' ', ' ', ' ', ' ', ',']
        title = title.strip()
        for i in range(len(symbol)):
            title = title.replace(symbol[i], fixedsymbol[i])
        return title

    class Intro:
        def __init__(self, title, coverurl, author, desc):
            self.title = Novel.titlefix(title)
            self.coverurl = coverurl.strip()
            self.author = author.strip()
            self.desc = desc.replace('\r', '').replace('\n', '').replace('\t', '').replace(' ', '').strip()

            if not os.path.exists(OUTPUTDIR):
                os.mkdir(OUTPUTDIR)
            if not os.path.exists(OUTPUTDIR + os.sep + title):
                os.mkdir(OUTPUTDIR + os.sep + title)

        def getoutputpath(self):
            return OUTPUTDIR + os.sep + self.title + os.sep

    class Chapter(object):
        def __init__(self, title, url):
            self.title = Novel.titlefix(title)
            self.url = url
            self.index = 0
            self.text = []

        def getfilename(self):
            return ("%04d" % self.index) + '_' + self.title

    def __init__(self, bookid):
        requests.packages.urllib3.disable_warnings()
        self.session = requests.Session()

        self.bookid = bookid
        self.intro = None
        self.chapterlist = []

    def _getsoup(self, url, encoding='utf-8'):
        tsstart = time.time()
        response = self.session.get(url, verify=False)
        tsend = time.time()
        logger.debug('[SOUP]Used time： ' + str(tsend - tsstart))
        response.encoding = encoding
        page = response.text
        soup = BeautifulSoup(page, 'html.parser')
        return soup

    def _igetintro(self):
        pass

    def __buildintro(self):
        intro = self._igetintro()
        self.intro = self.Intro(intro['title'], intro['coverurl'], intro['author'], intro['desc'])
        logger.info('[NOVEL]' + intro['title'] + ' - ' + intro['author'])

    def _igetchapters(self):
        pass

    def __buildchapters(self):
        self._igetchapters()
        logger.debug('[CHAPTERS]Builded!')

    def _igetchapter(self, chapter):
        pass

    def __buildchapter(self):
        hasnewchapter = False

        self.toc = Publish.Toc(self.intro)
        self.ncx = Publish.Ncx(self.intro)
        self.opf = Publish.Opf(self.intro)

        cnt = len(self.chapterlist)
        for i in range(cnt):
            chapter = self.chapterlist[i]
            chapter.index = i

            if os.path.exists(self.intro.getoutputpath() + chapter.getfilename() + '.html'):
                logger.warning(
                    '[CHAPTER ' + str(i + 1) + '/' + str(cnt)
                    + ']Exist & SKIP! \t' + '《' + chapter.title + '》')
            else:
                hasnewchapter = True
                self._igetchapter(chapter)
                Publish.Ch(self.intro, chapter).output()
                logger.info(
                    '[CHAPTER ' + str(i + 1) + '/' + str(cnt)
                    + ']Builded & Files Output! \t' + '《' + chapter.title + '》')

            self.toc.addchapter(chapter)
            self.ncx.addchapter(chapter)
            self.opf.addchapter(chapter)

        logger.debug('[Table Of Contents]Builded!')
        return hasnewchapter

    def __buildothers(self):
        self.toc.output()
        self.ncx.output()
        self.opf.output()
        logger.debug('[Table Of Contents]Files Output!')

        response = requests.get(self.intro.coverurl, verify=False)
        cover = response.content
        with open(self.intro.getoutputpath() + 'cover.jpg', 'wb') as f:
            f.write(cover)
        logger.debug('[Cover]Files Output!')

        shutil.copyfile('style.css', self.intro.getoutputpath() + 'style.css')
        logger.debug('[Style]Files Copied!')

    def __buildmobi(self):
        plat = sys.platform
        tsstart = time.time()
        if plat.startswith('win'):
            call(['kindlegen/windows/kindlegen.exe', '-verbose',
                  self.intro.getoutputpath() + self.intro.author + ' - ' + self.intro.title + '.opf'])
        elif plat == 'linux':
            call(['kindlegen/linux/kindlegen', '-verbose',
                  self.intro.getoutputpath() + self.intro.author + ' - ' + self.intro.title + '.opf'])
        elif plat == 'darwin':
            call(['kindlegen/macos/kindlegen', '-verbose',
                  self.intro.getoutputpath() + self.intro.author + ' - ' + self.intro.title + '.opf'])
        tsend = time.time()
        logger.info('[MOBI]Used time： ' + str(tsend - tsstart))

    def build(self):
        self.__buildintro()
        self.__buildchapters()
        if self.__buildchapter():
            self.__buildothers()
            self.__buildmobi()
        else:
            logger.warning('[ALL CHAPTERS]No New Chapter & BREAK! ')


class Publish(object):
    class Ch:
        def __init__(self, intro, chapter):
            self.intro = intro
            self.chapter = chapter

        def output(self):
            page = PyH(self.chapter.title)
            page.attributes['lang'] = 'zh-cn'
            page.addCSS('style.css')

            page << h2(id='ch' + str(self.chapter.index)) << self.chapter.title
            for line in self.chapter.text:
                page << p(line)

            page << div(cl='pagebreak')

            page.printOut(self.intro.getoutputpath() + self.chapter.getfilename() + '.html')

    class Toc:
        def __init__(self, intro):
            self.intro = intro

            self.page = PyH('目录')
            self.page.attributes['lang'] = 'zh-cn'
            self.page.head += charset
            self.page.addCSS('style.css')
            self.page << div(id='toc')
            self.page.toc << h1('目录')
            self.ul = ul()
            self.page.toc << self.ul

        def addchapter(self, chapter):
            self.ul << li() << a(href=chapter.getfilename() + '.html' + '#ch' + str(
                chapter.index)) << chapter.title

        def output(self):
            self.page << div(cl='pagebreak')
            self.page.printOut(self.intro.getoutputpath() + 'toc.html')

    class Ncx:
        def __init__(self, intro):
            self.intro = intro

            self.ncx = etree.Element('ncx', xmlns='http://www.daisy.org/z3986/2005/ncx/', version='2005-1')
            head = etree.SubElement(self.ncx, 'head')
            docTitle = etree.SubElement(self.ncx, 'docTitle')
            docTitleText = etree.SubElement(docTitle, 'text')
            docTitleText.text = self.intro.title

            self.navmap = etree.Element('navMap')
            navPoint = etree.SubElement(self.navmap, 'navPoint', id='toc', playOrder='1')
            navLabel = etree.SubElement(navPoint, 'navLabel')
            navLabelText = etree.SubElement(navLabel, 'text')
            navLabelText.text = u'目录'
            content = etree.SubElement(navPoint, 'content', src='toc.html#toc')

            self.ncx.append(self.navmap)

        def addchapter(self, chapter):
            navPoint = etree.SubElement(self.navmap, 'navPoint', id='ch' + str(chapter.index),
                                        playOrder=str(chapter.index + 2))
            navLabel = etree.SubElement(navPoint, 'navLabel')
            navLabelText = etree.SubElement(navLabel, 'text')
            navLabelText.text = chapter.title
            content = etree.SubElement(navPoint, 'content',
                                       src=chapter.getfilename() + '.html' + '#ch' + str(chapter.index))

        def output(self):
            ncxtree = etree.ElementTree(self.ncx)
            ncxtree.write(self.intro.getoutputpath() + 'toc.ncx', xml_declaration=True, encoding='utf-8')

    class Opf:
        class XMLNamespaces:
            dc = 'http://purl.org/metadata/dublin_core'

        def __init__(self, intro):
            self.intro = intro

            etree.register_namespace('dc', self.XMLNamespaces.dc)
            self.opf = etree.Element('package', version='2.0')

            metadata = etree.SubElement(self.opf, 'metadata')
            dctitle = etree.SubElement(metadata, QName(self.XMLNamespaces.dc, 'title'))
            dctitle.text = self.intro.title
            dclanguage = etree.SubElement(metadata, QName(self.XMLNamespaces.dc, 'language'))
            dclanguage.text = 'zh'
            dccreator = etree.SubElement(metadata, QName(self.XMLNamespaces.dc, 'creator'))
            dccreator.text = self.intro.author
            dcpublisher = etree.SubElement(metadata, QName(self.XMLNamespaces.dc, 'publisher'))
            dcpublisher.text = 'NovelCrawler'
            dcdescription = etree.SubElement(metadata, QName(self.XMLNamespaces.dc, 'description'))
            dcdescription.text = self.intro.desc
            meta = etree.SubElement(metadata, 'meta', name='cover', content='cover')

            self.manifest = etree.Element('manifest')
            incx = etree.SubElement(self.manifest, 'item', id='ncx', href='toc.ncx')
            incx.set('media-type', 'application/x-dtbncx+xml')
            istyle = etree.SubElement(self.manifest, 'item', id='stylesheet', href='style.css')
            istyle.set('media-type', 'text/css')
            icover = etree.SubElement(self.manifest, 'item', id='cover', href='cover.jpg', properties='cover-image')
            icover.set('media-type', 'image/jpeg')
            itoc = etree.SubElement(self.manifest, 'item', id='content', href='toc.html')
            itoc.set('media-type', 'application/xhtml+xml')

            self.spine = etree.Element('spine', toc='ncx')
            ircontent = etree.SubElement(self.spine, 'itemref', idref='content')

            guide = etree.Element('guide')
            rtoc = etree.SubElement(guide, 'reference', type='toc', title=u'目录', href='toc.html#toc')

            self.opf.append(self.manifest)
            self.opf.append(self.spine)
            self.opf.append(guide)

        def addchapter(self, chapter):
            itextch = etree.SubElement(self.manifest, 'item', id='ch' + str(chapter.index),
                                       href=chapter.getfilename() + '.html')
            itextch.set('media-type', 'application/xhtml+xml')

            irtextch = etree.SubElement(self.spine, 'itemref', idref='ch' + str(chapter.index))

        def output(self):
            opftree = etree.ElementTree(self.opf)
            opftree.write(self.intro.getoutputpath() + self.intro.author + ' - ' + self.intro.title + '.opf',
                          xml_declaration=True, encoding='utf-8')
