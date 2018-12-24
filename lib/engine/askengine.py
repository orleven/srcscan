#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import re
import asyncio
from urllib import parse
from random import randint
from lib.data import logger
from lib.enums import SEARCH_ERROR
from lib.engine.searchengine import SearchEngine

class AskEngine(SearchEngine):
    """
    this engine need a proxy
    """
    def __init__(self,target,engine_name="Ask_Domain", **kwargs):
        self.max_pageno = 30
        self.engine = 'http://www.ask.com/'
        self.base_url = 'http://www.ask.com/web?q={query}&page={page_no}' \
                        '&o=0&l=dir&qsrc=998&qo=pagination'
        self.find_new_domain = False
        super(AskEngine, self).__init__(target, engine_name=engine_name, **kwargs)

    def extract(self, content):
        next_page = '<li class="PartialWebPagination-next">Next</li>'
        pattern = re.compile('<p class="PartialSearchResults-item-url">(.*?\.{domain}).*?</p>'
                             .format(domain=self.target))
        try:
            links = pattern.findall(content)
            self.find_new_domain = False
            for link in links:
                if not link.startswith('http://') and not link.startswith('https://'):
                    link = "http://" + link
                subdomain = parse.urlparse(link).netloc

                if subdomain != self.target and subdomain.endswith(self.target):

                    if subdomain not in self.results['subdomain']:
                        self.logger.debug(
                        "{engine} Found {subdomain}".format(
                                engine=self.engine_name,subdomain=subdomain))
                        self.results['subdomain'].append(subdomain)
                        self.find_new_domain = True
        except Exception:
            pass
        if next_page in content:
            # tell engine there still be next page
            return True
        else:
            return False

    def check_response_errors(self,content):
        if not content:
            return [False, SEARCH_ERROR.TIMEOUT]
        if "No results for:" in content:
            return [False,SEARCH_ERROR.END]
        elif "webResults" in content:
            return [True,0]
        else:
            return [False,SEARCH_ERROR.UNKNOWN]

    def generate_query(self):
        if self.check_max_pageno(): return
        length = len(self.results['subdomain'])

        if length==0:
            query = "site:{domain}".format(domain=self.target)
            self.queries.append((query,1))
            self.results['subdomain'].append("www." + self.target)  # 防止 一直请求第一个页面
        elif self.find_new_domain:
            found = ' -site:'.join([x for x in self.results['subdomain']])
            query = "site:{domain} -site:{found}".format(domain=self.target, found=found)
            self.queries.append((query, 1))
        else:
            self.queries.append((self.pre_query,self.pre_pageno+1))

    def format_base_url(self, *args):
        return self.base_url.format(query=args[0], page_no=args[1])