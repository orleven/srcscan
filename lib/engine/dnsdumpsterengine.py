#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import aiohttp
import re
from urllib import parse
from lib.data import logger
from lib.engine.engine import ERROR
from lib.engine.engine import Engine

class DNSdumpsterEngine(Engine):

    def __init__(self,target,random=True,proxy=False):
        self.max_pageno = 30
        self.engine = "https://dnsdumpster.com/"
        self.base_url = 'https://dnsdumpster.com/'
        self.find_new_domain = False
        super(DNSdumpsterEngine, self)\
            .__init__(target, engine_name="DNSdumpster",random=random,proxy=proxy)
        self.headers['Origin'] = "https://dnsdumpster.com/"
        self.headers['Referer'] = "https://dnsdumpster.com/"
        self.headers['Content-Type'] = "application/x-www-form-urlencoded"

    async def check_engine_available(self,session,engine):
        content = await self.get(session,
                                 engine,
                                 headers=self.headers,
                                 proxy=self.proxy)
        if content:
            self.data = {
                'csrfmiddlewaretoken': self.extract_csrf_token(content),
                'targetip': self.target.netloc
            }
            return True
        else:
            return False

    def extract_csrf_token(self,content):
        pattern = re.compile('<input type=\'hidden\' name=\'csrfmiddlewaretoken\' value=\'(.*?)\'')
        try:
            token = pattern.findall(content)
            if len(token)>0:
                return token[0]
        except Exception:
            pass
        return None

    def extract(self,content):
        pattern = re.compile('<tr>\s*<td class=.*?>(.*?{domain})<br>'
                   .format(domain=self.target.netloc))
        try:
            links = pattern.findall(content)

            for link in links:
                if link not in self.subdomains:
                    self.logger.info(
                        "{engine} Found {subdomain}".format(
                            engine=self.engine_name, subdomain=link))
                    self.subdomains.update([link])
        except Exception:
            pass

    def check_response_errors(self,content):
        if not content:
            return [False, ERROR.TIMEOUT]

        if "There was an error getting results" in content:
            return [False,ERROR.END]
        elif "Showing results for" in content:
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

            self.logger.debug("{engine} {url}".format(engine=self.engine_name,url=self.base_url))

            content = await self.get(session,
                                       self.base_url,
                                       method='POST',
                                       data=self.data,
                                       headers=self.headers,
                                       proxy=self.proxy,
                                       timeout=50)

            ret = self.check_response_errors(content)
            if not ret[0]:
                self.deal_with_errors(ret[1])

            self.extract(content)

            self.logger.debug(self.engine_name + " " + str(len(self.subdomains)))
