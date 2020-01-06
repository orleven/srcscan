#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import re
from urllib import parse
from lib.data import logger
from lib.enums import SEARCH_ERROR
from lib.engine.searchengine import SearchEngine

class ChinazEngine(SearchEngine):

    def __init__(self,target,engine_name="Chinaz_Domain", **kwargs):
        self.engine = "http://tool.chinaz.com/"
        self.base_url = 'http://tool.chinaz.com/subdomain?domain={query}&page={page_no}'
        super(ChinazEngine,self).__init__(target, engine_name=engine_name, **kwargs)

    def generate_query(self):
        length = len(self.results['subdomain'])
        if length==0:
            self.queries.append((self.target,1))
        else:
            self.queries.append((self.target ,self.pre_pageno+1))

    def check_response_errors(self,content):

        if not content:
            return [False, SEARCH_ERROR.TIMEOUT]

        if "没有查询到" in content:
            return [False,SEARCH_ERROR.END]
        elif "被访问网址" in content:
            return [True,0]
        else:
            return [False,SEARCH_ERROR.UNKNOWN]

    def extract(self,content):
        pattern = re.compile('<a href="javascript:" onclick="window.open.*?" target="_blank">(.*?{domain})</a>'
                             .format(domain=self.target))
        next_page = "下一页"
        try:
            links = pattern.findall(content)

            for link in links:
                if not link.startswith('http://') and not link.startswith('https://'):
                    link = "http://" + link

                subdomain = parse.urlparse(link).netloc

                if subdomain != self.target and subdomain.endswith(self.target):
                    if subdomain not in self.results['subdomain']:
                        logger.debug(
                        "{engine} Found {subdomain}".format(
                                engine=self.engine_name,subdomain=subdomain))
                        self.results['subdomain'].append(subdomain)
        except Exception:
            pass
        if next_page in content:
            # tell engine there still be next page
            return True
        else:
            return False