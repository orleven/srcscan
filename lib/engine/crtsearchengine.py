#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'


import aiohttp
import re
from urllib import parse
from lib.data import logger
from lib.engine.engine import ERROR
from lib.engine.engine import Engine

class CrtSearchEngine(Engine):
    """
    need a proxy
    """
    def __init__(self,target,random=True,proxy=False):
        self.engine = "https://crt.sh"
        self.base_url = 'https://crt.sh/?q=%25.{domain}'
        super(CrtSearchEngine, self)\
            .__init__(target, engine_name="SSL Certificates",random=random,proxy=proxy)

    def extract(self, content):
        pattern = re.compile('<TD>(.*?{domain})</TD>'.format(domain=self.target.netloc))
        try:
            links = pattern.findall(content)
            for link in links:
                link = link.strip('*.')
                if link != self.target.netloc and link not in self.subdomains:
                    self.logger.debug(
                        "{engine} Found {subdomain}".format(
                            engine=self.engine_name, subdomain=link))
                    self.subdomains.update([link])
        except Exception:
            pass

    def format_base_url(self,*args):
        return self.base_url.format(domain=args[0])

    def check_response_errors(self,content):
        if not content:
            return [False, ERROR.TIMEOUT]

        if "None found" in content:
            return [False,ERROR.END]
        elif "crt.sh ID" in content:
            return [True,0]
        else:
            return [False,ERROR.UNKNOWN]


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

            content = await self.get(session, url, self.headers,timeout=50)

            ret = self.check_response_errors(content)
            if not ret[0]:
                self.deal_with_errors(ret[1])
                return
            self.extract(content)

    def deal_with_errors(self,error_code):
        """subclass should override this function for identify security mechanism"""
        if error_code == ERROR.END:
            self.logger.debug("{engine} has no results".format(engine=self.engine_name))
        elif error_code == ERROR.UNKNOWN:
            # raise ReconResponseContentErrorException
            self.logger.error("response content error")
        elif error_code == ERROR.TIMEOUT:
            self.logger.debug("{engine} is not available now, Stop!".format(engine=self.engine_name))

