#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import re
from urllib import parse
from lib.data import logger
from lib.engine.engine import ERROR
from lib.engine.engine import Engine

class AskEngine(Engine):
    """
    this engine need a proxy
    """
    def __init__(self,target,random_ua=True,proxy=False):
        self.max_pageno = 30
        self.engine = 'http://www.ask.com/'
        self.base_url = 'http://www.ask.com/web?q={query}&page={page_no}' \
                        '&o=0&l=dir&qsrc=998&qo=pagination'
        self.find_new_domain = False
        super(AskEngine, self).__init__(target, engine_name="Ask",random=random_ua,proxy=proxy)

    def extract(self, content):
        next_page = '<li class="PartialWebPagination-next">Next</li>'
        pattern = re.compile('<p class="PartialSearchResults-item-url">(.*?\.{domain}).*?</p>'
                             .format(domain=self.target.netloc))
        try:
            links = pattern.findall(content)
            self.find_new_domain = False
            for link in links:
                if not link.startswith('http://') and not link.startswith('https://'):
                    link = "http://" + link
                subdomain = parse.urlparse(link).netloc

                if subdomain != self.target.netloc and subdomain.endswith(self.target.netloc):
                    if subdomain not in self.subdomains:
                        self.logger.debug(
                        "{engine} Found {subdomain}".format(
                                engine=self.engine_name,subdomain=subdomain))
                        self.subdomains.update([subdomain])
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
            return [False, ERROR.TIMEOUT]
        if "No results for:" in content:
            return [False,ERROR.END]
        elif "webResults" in content:
            return [True,0]
        else:
            return [False,ERROR.UNKNOWN]

    def generate_query(self):
        if self.check_max_pageno(): return
        length = len(self.subdomains)

        if length==0:
            query = "site:{domain}".format(domain=self.target.netloc)
            self.queries.append((query,1))
            self.subdomains.update(["www."+self.target.netloc])# 防止 一直请求第一个页面
        elif self.find_new_domain:
            found = ' -site:'.join(list(self.subdomains))
            query = "site:{domain} -site:{found}".format(domain=self.target.netloc, found=found)
            self.queries.append((query, 1))
        else:
            self.queries.append((self.pre_query,self.pre_pageno+1))

    def format_base_url(self, *args):
        return self.base_url.format(query=args[0], page_no=args[1])