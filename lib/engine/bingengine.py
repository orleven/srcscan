#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'


import asyncio
from random import randint
import re
from urllib import parse
from lib.data import logger
from lib.engine.engine import ERROR
from lib.engine.engine import Engine
class BingEngine(Engine):

    def __init__(self,target,random=True,proxy=False):
        self.max_pageno= 25
        self.engine = "https://www.bing.com"
        self.base_url = 'https://www.bing.com/search?q={query}&qs=n&sp=-1&sc=0-13&sk=&first={page_no}'
        self.find_new_domain = False
        super(BingEngine, self).__init__(target, engine_name="Bing",random=random,proxy=proxy)

    def extract(self, content):
        next_page = '<div class="sw_next">下一页</div>'
        pattern = re.compile('<cite>(.*?<strong>{domain}</strong>).*?</cite>'
                             .format(domain=self.target.netloc))
        try:
            links = pattern.findall(content)

            self.find_new_domain = False
            for link in links:
                link = re.sub('<.*?>','',link)

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

    def generate_query(self):
        if self.check_max_pageno(): return
        length = len(self.subdomains)

        if length==0:
            query = "site:{domain}".format(domain=self.target.netloc)
            self.queries.append((query,0))
            self.subdomains.update(["www."+self.target.netloc])# 防止 一直请求第一个页面
        elif self.find_new_domain:
            found = ' -site:'.join(list(self.subdomains))
            query = "site:{domain} -site:{found}".format(domain=self.target.netloc, found=found)
            self.queries.append((query, 0))
        else:
            self.queries.append((self.pre_query,self.pre_pageno+1))

    def format_base_url(self, *args):
        return self.base_url.format(query=args[0], page_no=args[1]*10+1)

    def check_response_errors(self,content):
        if not content:
            return [False, ERROR.TIMEOUT]

        if "没有与此相关的结果" in content:
            return [False,ERROR.END]
        elif "条结果" in content:
            return [True,0]
        else:
            return [False,ERROR.UNKNOWN]

    async def should_sleep(self):
        self.logger.debug("{engine} sleep random time...".format(engine=self.engine_name))
        await asyncio.sleep(randint(1, 2))