#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author = 'orleven'
import asyncio
import random
import backoff
import aiohttp
import async_timeout
from collections import deque
from lib.data import conf
from lib.common import random_IP
from lib.data import logger
from lib.enums import SEARCH_ERROR
from lib.enums import USER_AGENTS
from lib.common import get_safe_ex_string
from aiohttp.client_exceptions import TooManyRedirects
from aiohttp.client_exceptions import ClientConnectorError

class SearchEngine(object):
    '''
        API search engine base class
    '''

    def __init__(self, target, engine_name=None, timeout=5, proxy=None, random_ua=True,random_ip=False):
        self.headers = {
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'DNT': '1',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        self.target = target
        self.logger = logger
        self.engine_name = engine_name
        self.random_ua = random_ua
        self.random_ip = random_ip
        self.results = {'subdomain':[], 'dns_domain': [], 'cdn_ip': []}
        self.queries = deque()
        self.timeout = timeout
        if conf['config']['proxy']['proxy'].lower() == 'true':
            try:
                proxy = conf['config']['proxy']['http_proxy']
            except:
                logger.error("Error http(s) proxy: %s or %s." % (
                    conf['config']['proxy']['http_proxy'], conf['config']['proxy']['https_proxy']))
        self.proxy = proxy
        self.pre_pageno = 0
        self.pre_query = ""

    @backoff.on_exception(backoff.expo, (asyncio.TimeoutError,TimeoutError) , max_time=60)
    async def get(self, session, url, method='GET', **kwargs):
        """
        fetch online resource
        :param session: aiohttp session
        :param url: like http://baidu.com/s?
        :param headers: use normal http headers to fetch online resource
        :param proxy: proxy url
        :return: online resource content
        """
        headers = kwargs.get('headers')
        if headers == None:
            headers = self.headers
        if 'Referer' not in headers.keys():
            headers['Referer'] = url
        headers['Accept-Charset'] = 'GB2312,utf-8;q=0.7,*;q=0.7'
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        headers['Accept-Encoding'] = 'gzip, deflate, sdch'
        if self.random_ip:
            headers['X-Forwarded-For'] = random_IP()
        if self.random_ua:
            headers["User-Agent"] = random.choice(USER_AGENTS)
        kwargs.setdefault('headers', headers)
        kwargs.setdefault('timeout', self.timeout)
        # kwargs.setdefault('verify', False)
        kwargs.setdefault('proxy', self.proxy)

        try:
            async with async_timeout.timeout(self.timeout):
                async with session.request(method, url, **kwargs) as response:
                    return await response.text()
        except TooManyRedirects as e:
            kwargs.setdefault('allow_redirects', False)
            try:
                async with async_timeout.timeout(self.timeout):
                    async with session.request(method, url, **kwargs) as response:
                        return await response.text()
            except:
                return None
        except ClientConnectorError as e:
            return None
        except asyncio.TimeoutError as e:
            self.logger.error('Fetch exception: {e}, {u}'.format(e=get_safe_ex_string(e), u=url))
            return None
        except Exception as e:
            if type(e).__name__ not in ['asyncio.TimeoutError', 'TimeoutError']:
                self.logger.error('Fetch exception: {e}, {u}'.format(e=get_safe_ex_string(e), u=url))
            return None

    def extract(self, content):
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

    def check_response_errors(self, content):
        """
        subclass should override this function for identify security mechanism
        """
        return [True,0]

    async def check_engine_available(self, session, engine):

        content = await self.get(session,engine)
        if content:
            return True
        else:
            return False

    def deal_with_errors(self, error_code):
        """
        subclass should override this function for identify security mechanism
        """
        if error_code == SEARCH_ERROR.END:
            self.logger.debug("{engine} has no results".format(engine=self.engine_name))
        elif error_code == SEARCH_ERROR.UNKNOWN:
            self.logger.error("{engine} response content error!".format(engine=self.engine_name))
            # raise ReconResponseContentErrorException
        elif error_code == SEARCH_ERROR.TIMEOUT:
            self.logger.debug("{engine} is not available now, Stop!".format(engine=self.engine_name))


    async def run(self):
        async with aiohttp.ClientSession() as session:
            flag = await self.check_engine_available(session, self.engine)
            if not flag:
                self.logger.error("{engine_name} is not available, skipping!" .format(engine_name=self.engine_name))
                return
            self.logger.debug("{engine_name} is available, starting!".format(engine_name=self.engine_name))

            self.generate_query()
            while len(self.queries):
                session.cookie_jar.clear()
                (query, self.pre_pageno) = self.queries.popleft()
                self.pre_query = query
                url = self.format_base_url(query, self.pre_pageno)

                self.logger.debug("{engine}: {url}".format(engine=self.engine_name, url=url))
                content = await self.get(session, url)
                ret = self.check_response_errors(content)
                if not ret[0]:
                    self.deal_with_errors(ret[1])
                    break

                if self.extract(content):
                    self.generate_query()
                if len(self.queries) > 0:
                    await self.should_sleep()  # avoid being blocked
