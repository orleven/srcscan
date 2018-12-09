#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'


import json
import aiohttp
from urllib import parse
from lib.data import logger
from lib.engine.engine import ERROR
from lib.engine.engine import Engine
class BugscannerEngine(Engine):

    def __init__(self,target,random=True,proxy=False):
        self.engine = "http://tools.bugscaner.com"
        self.base_url = 'http://tools.bugscaner.com/api/subdomain/'
        self.find_new_domain = False
        super(BugscannerEngine, self).__init__(target, engine_name="Bugscanner",random=random,proxy=proxy)

    def check_response_errors(self,content):
        if not content:
            return [False, ERROR.TIMEOUT]

        if "{\"code\": 404}" in content:
            return [False,ERROR.END]
        elif "\"nb\":" in content:
            return [True,0]
        else:
            return [False,ERROR.UNKNOWN]

    def extract(self,content):
        try:
            domain = json.loads(content)['domain']
            self.subdomains.update(domain)
        except Exception:
            pass

    async def run(self):
        async with aiohttp.ClientSession() as session:

            flag = await self.check_engine_available(session,self.engine)
            if not flag:
                logger.error("{engine_name} is not available, skipping!"
                                  .format(engine_name=self.engine_name))
                return
            logger.sysinfo("{engine_name} is available, starting!"
                             .format(engine_name=self.engine_name))

            data = {
                'inputurl':self.target.netloc
            }
            content = await self.get(session,
                                       self.base_url,
                                       method="POST",
                                       data=data,
                                       headers=self.headers,
                                       timeout=self.timeout,
                                       proxy=self.proxy)

            ret = self.check_response_errors(content)
            if not ret[0]:
                self.deal_with_errors(ret[1])

            self.extract(content)
            logger.sysinfo("{engine} Found {num} sites".format(engine=self.engine_name,num=len(self.subdomains)))
            logger.debug(self.engine_name + " " + str(len(self.subdomains)))
