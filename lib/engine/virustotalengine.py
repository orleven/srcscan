#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'


import aiohttp
import re
from urllib import parse
from lib.data import logger
from lib.engine.engine import ERROR
from lib.engine.engine import Engine

class VirustotalEngine(Engine):
    """need a proxy"""
    def __init__(self,target,random=True,proxy=False):
        self.engine = "https://www.virustotal.com"
        self.base_url = 'https://www.virustotal.com/en/domain/{domain}/information/'
        super(VirustotalEngine, self)\
            .__init__(target, engine_name="Virustotal",random=random, proxy=proxy)

    def format_base_url(self, *args):
        return self.base_url.format(domain=args[0])

    def check_response_errors(self,content):
        if not content:
            return [False, ERROR.TIMEOUT]
        if 'No IP addresses' in content:
            return [False,ERROR.END]
        elif 'Observed subdomains' in content:
            return [True,0]
        else:
            return [False,ERROR.UNKNOWN]

    def extract(self,content):
        pattern = re.compile('<div class="enum .*?">\s*<a target="_blank" href=".*?">\s*(.*?{domain})\s*</a>'
                             .format(domain=self.target.netloc))
        try:
            links = pattern.findall(content)
            for link in links:
                if link != self.target.netloc and link not in self.subdomains:
                    self.logger.debug(
                        "{engine} Found {subdomain}".format(
                            engine=self.engine_name, subdomain=link))
                    self.subdomains.update([link])
        except Exception:
            pass

    async def run(self):
        async with aiohttp.ClientSession() as session:

            flag = await self.check_engine_available(session,self.engine)
            if not flag:
                self.logger.error("{engine_name} is not available, skipping!"
                                  .format(engine_name=self.engine_name))
                return
            self.logger.debug("{engine_name} is available, starting!"
                             .format(engine_name=self.engine_name))

            url = self.format_base_url(self.target.netloc)

            self.logger.debug("{engine} {url}".format(engine=self.engine_name,url=url))

            content = await self.get(session, url, headers=self.headers, proxy=self.proxy)

            ret = self.check_response_errors(content)
            if not ret[0]:
                self.deal_with_errors(ret[1])
                return

            self.extract(content)

            self.logger.debug(self.engine_name + " " + str(len(self.subdomains)))