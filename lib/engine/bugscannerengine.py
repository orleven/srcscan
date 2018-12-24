#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import re
import json
import aiohttp
from urllib import parse
from random import randint
from lib.data import logger
from lib.enums import SEARCH_ERROR
from lib.engine.searchengine import SearchEngine

class BugscannerEngine(SearchEngine):

    def __init__(self,target,engine_name="Bugscanner_Domain", **kwargs):
        self.engine = "http://tools.bugscaner.com"
        self.base_url = 'http://tools.bugscaner.com/api/subdomain/'
        self.find_new_domain = False
        super(BugscannerEngine, self).__init__(target, engine_name=engine_name, **kwargs)

    def check_response_errors(self,content):
        if not content:
            return [False, SEARCH_ERROR.TIMEOUT]

        if "{\"code\": 404}" in content:
            return [False,SEARCH_ERROR.END]
        elif "\"nb\":" in content:
            return [True,0]
        else:
            return [False,SEARCH_ERROR.UNKNOWN]

    def extract(self,content):
        try:
            domain = json.loads(content)['domain']
            for i in domain:
                self.results['subdomain'].append(i)
        except Exception:
            pass

    async def run(self):
        async with aiohttp.ClientSession() as session:

            flag = await self.check_engine_available(session,self.engine)
            if not flag:
                logger.error("{engine_name} is not available, skipping!"
                                  .format(engine_name=self.engine_name))
                return
            logger.debug("{engine_name} is available, starting!"
                             .format(engine_name=self.engine_name))

            data = {
                'inputurl':self.target
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
            logger.sysinfo("{engine} Found {num} sites".format(engine=self.engine_name,num=len(self.results['subdomain'])))
            logger.debug(self.engine_name + " " + str(len(self.results['subdomain'])))
