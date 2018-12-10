#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import async_timeout
import aiohttp
import backoff as backoff
from collections import deque
from random import choice
from urllib import parse as urlparse
from lib.data import logger
from lib.data import conf


class ERROR:
    END = 10000
    UNKNOWN = 100001
    TIMEOUT = 100002


default_headers = {
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'DNT': '1',
    # 'Referer': 'https://www.baidu.com/',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}

class Engine(object):
    def __init__(self, target,engine_name=None,random=True, headers=default_headers, proxy=False,timeout = 20):
        self.logger = logger
        self.engine_name = engine_name
        self.subdomains = set() # not include original domain(self.target)
        self.headers = headers
        self.headers["User-Agent"] = choice(conf['config']['basic']['user_agent'].split('\n')) if random else self.headers["User-Agent"]
        self.queries = deque()
        self.pre_query = ""
        self.pre_pageno = 0
        self.target = target
        self.timeout = int(conf['config']['basic']['timeout'])
        if conf['config']['proxy']['proxy'].lower() == 'true':
            try:
                proxy = {
                    'http': conf['config']['proxy']['http_proxy'],
                    'https': conf['config']['proxy']['https_proxy']
                }
            except:
                logger.error("Error http(s) proxy: %s or %s." % (
                conf['config']['proxy']['http_proxy'], conf['config']['proxy']['https_proxy']))
        self.proxy = proxy

    # @staticmethod
    @backoff.on_exception(backoff.expo, TimeoutError, max_tries=3)
    async def get(self,session,url,headers = default_headers,method='GET',data=None,proxy=False,timeout=20):
        """
        fetch online resource
        :param session: aiohttp session
        :param url: like http://baidu.com/s?
        :param headers: use normal http headers to fetch online resource
        :param proxy: proxy url
        :return: online resource content
        """

        try:
            async with async_timeout.timeout(timeout):
                if not proxy:
                    async with session.request(method,url,data=data,headers=headers) as response:
                        return await response.text()
                else:
                    async with session.request(method,url,data=data,headers=headers,proxy=proxy['http']) as response:
                        return await response.text()
        except Exception as e:
            if type(e).__name__ != 'TimeoutError':
                logger.error('Fetch exception: {e} {u}'.format(e=type(e).__name__, u=url))
                return None

    def extract(self,content):
        """subclass override this function for extracting domain from response"""
        return

    async def should_sleep(self):
        """subclass should override this function for pause http request, avoiding be blocked"""
        return

    def generate_query(self):
        """subclass should override this function for generate queries
            append to queries
            according subdomains generate queries
            or according page content generate next page
            demo:
                if check_max_pageno(): return
                generate query and append to self.queries
                suggest generate 10 query one time
        """
        return

    def format_base_url(self, *args):
        """
        subclass should override this function for specific format
        :param args:
        :return:
        """
        return self.base_url.format(query=args[0], page_no=args[1])

    def check_max_pageno(self):
        return self.max_pageno <= self.pre_pageno

    def check_response_errors(self,content):
        """subclass should override this function for identify security mechanism"""
        return True

    async def check_engine_available(self,session,engine):

        content = await self.get(session,
                                 engine,
                                 headers=self.headers,
                                 proxy=self.proxy)
        if content:
            return True
        else:
            return False

    def deal_with_errors(self,error_code):
        """subclass should override this function for identify security mechanism"""
        if error_code == ERROR.END:
            self.logger.debug("{engine} has no results".format(engine=self.engine_name))
        elif error_code == ERROR.UNKNOWN:
            self.logger.error("{engine} response content error!".format(engine=self.engine_name))
            # raise ReconResponseContentErrorException
        elif error_code == ERROR.TIMEOUT:
            self.logger.debug("{engine} is not available now, Stop!".format(engine=self.engine_name))

    async def run(self):
        async with aiohttp.ClientSession() as session:
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
                url = self.format_base_url(query,self.pre_pageno)

                self.logger.debug("{engine} {url}".format(engine=self.engine_name,url=url))

                content = await self.get(session,url,headers=self.headers,timeout=self.timeout,proxy=self.proxy)
                ret = self.check_response_errors(content)
                if not ret[0]:
                    self.deal_with_errors(ret[1])
                    break

                if self.extract(content):
                    self.generate_query()
                if len(self.queries)>0:
                    await self.should_sleep()# avoid being blocked
                self.logger.debug("%s for %s: %d" %(self.engine_name ,self.target.netloc, len(self.subdomains)))
