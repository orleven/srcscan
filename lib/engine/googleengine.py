#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import json
import asyncio
from lib.connect import ClientSession
from urllib import parse
from random import randint
from lib.data import logger
from lib.data import conf
from lib.enums import SEARCH_ERROR
from lib.engine.searchengine import SearchEngine

class GoogleEngine(SearchEngine):

    def __init__(self,target,engine_name="Google_Domain", **kwargs):
        self.max_pageno= 20
        self.engine = "https://www.googleapis.com/"
        self.base_url = 'https://www.googleapis.com/customsearch/v1?cx={search_enging}&key={developer_key}&num=10&start={page_no}&q={query}'
        self.find_new_domain = False

        super(GoogleEngine,self)\
            .__init__(target, engine_name=engine_name, **kwargs)


    def generate_query(self):
        if self.check_max_pageno(): return
        length = len(self.results['subdomain'])

        if length==0:
            query = "site:{domain}".format(domain=self.target)
            self.queries.append((query,0))
            self.results['subdomain'].append("www." + self.target)  # 防止 一直请求第一个页面
        elif self.find_new_domain:
            found = ' -site:'.join([x for x in self.results['subdomain']])
            query = "site:{domain} -site:{found}".format(domain=self.target, found=found)
            self.queries.append((query, 0))
        else:
            self.queries.append((self.pre_query,self.pre_pageno+1))

    def format_base_url(self, *args):
        return self.base_url.format(query=args[0], page_no=str(args[1] * 10 +1),search_enging=args[2],developer_key=args[3])

    async def should_sleep(self):
        self.logger.debug("{engine} sleep random time...".format(engine=self.engine_name))
        await asyncio.sleep(randint(4, 5))

    def check_response_errors(self,content):
        if not content:
            return [False, SEARCH_ERROR.TIMEOUT]
        try:
            res_json = json.loads(content)
            num = int(res_json.get('searchInformation').get('totalResults'))
            if num == 0  :
                return [False, SEARCH_ERROR.END]
            elif num > 0:
                return [True, 0]
        except Exception as e:
            return [False, SEARCH_ERROR.UNKNOWN]


    def extract(self,content):
        self.find_new_domain = False
        try:
            res_json = json.loads(content)

            for item in res_json.get('items'):
                link = item.get('link')
                if not link.startswith('http://') and not link.startswith('https://'):
                    link = "http://" + link
                subdomain = parse.urlparse(link).netloc
                if subdomain != self.target and subdomain.endswith(self.target):
                    if subdomain not in self.results['subdomain']:
                        self.logger.debug(
                        "{engine} Found {subdomain}".format(
                                engine=self.engine_name,subdomain=subdomain))
                        self.results['subdomain'].append( subdomain)
                        self.find_new_domain = True
        except:
            return False
        return True


    async def run(self):
        try:
            developer_key = conf['config']['google_api']['developer_key']
            search_enging = conf['config']['google_api']['search_enging']
        except KeyError:
            self.logger.error("Load srcscan config error: google_api, please check the config in tentacle.conf，skipping!")
            return
        async with ClientSession() as session:
            flag = await self.check_engine_available(session,self.engine)
            if not flag:
                self.logger.error("{engine_name} is not available, skipping!"
                                  .format(engine_name=self.engine_name))
                return
            self.logger.debug("{engine_name} is available, starting!"
                             .format(engine_name=self.engine_name))

            self.generate_query()
            while len(self.queries):
                session.cookie_jar.clear()
                (query, self.pre_pageno) = self.queries.popleft()
                self.pre_query = query
                url = self.format_base_url(query, self.pre_pageno, search_enging, developer_key)
                self.logger.debug("{engine} {url}".format(engine=self.engine_name, url=url))

                async with session.get(url, proxy=self.proxy) as res:
                    if res != None:
                        try:
                            content = await res.text()
                        except:
                            content = ''
                        ret = self.check_response_errors(content)
                        if not ret[0]:
                            self.deal_with_errors(ret[1])
                            break

                        if self.extract(content):
                            self.generate_query()
                        if len(self.queries) > 0:
                            await self.should_sleep()  # avoid being blocked
                        self.logger.debug("%s for %s: %d" % (self.engine_name, self.target, len(self.results['subdomain'])))
