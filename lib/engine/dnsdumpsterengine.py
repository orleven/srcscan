#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import re
from lib.connect import ClientSession
from lib.enums import SEARCH_ERROR
from lib.engine.searchengine import SearchEngine

class DNSdumpsterEngine(SearchEngine):

    def __init__(self,target,engine_name="DNSdumpster_Domain", **kwargs):
        self.max_pageno = 30
        self.engine = "https://dnsdumpster.com/"
        self.base_url = 'https://dnsdumpster.com/'
        self.find_new_domain = False
        super(DNSdumpsterEngine, self)\
            .__init__(target, engine_name=engine_name, **kwargs)
        self.headers['Origin'] = "https://dnsdumpster.com/"
        self.headers['Referer'] = "https://dnsdumpster.com/"
        self.headers['Content-Type'] = "application/x-www-form-urlencoded"

    async def check_engine_available(self,session,engine):
        async with session.get(engine, proxy=self.proxy) as response:
            if response != None:
                try:
                    content = await response.text()
                except:
                    content = ""
                self.data = {
                    'csrfmiddlewaretoken': self.extract_csrf_token(content),
                    'targetip': self.target
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
                   .format(domain=self.target))
        try:
            links = pattern.findall(content)

            for link in links:
                if link not in self.results['subdomain']:
                    self.logger.info(
                        "{engine} Found {subdomain}".format(
                            engine=self.engine_name, subdomain=link))
                    self.results['subdomain'].append(link)
        except Exception:
            pass

    def check_response_errors(self,content):
        if not content:
            return [False, SEARCH_ERROR.TIMEOUT]

        if "There was an error getting results" in content:
            return [False,SEARCH_ERROR.END]
        elif "Showing results for" in content:
            return [True,0]
        else:
            return [False,SEARCH_ERROR.UNKNOWN]

    async def run(self):
        async with ClientSession() as session:
            flag = await self.check_engine_available(session,self.engine)
            if not flag:
                self.logger.error("{engine_name} is not available, skipping!"
                                  .format(engine_name=self.engine_name))
                return
            self.logger.debug("{engine_name} is available, starting!"
                             .format(engine_name=self.engine_name))

            self.logger.debug("{engine} {url}".format(engine=self.engine_name,url=self.base_url))
            async with session.post(self.base_url, proxy=self.proxy, data=self.data) as res:
                if res != None:
                    try:
                        content = await res.text()
                    except:
                        content = ""
                    ret = self.check_response_errors(content)
                    if not ret[0]:
                        self.deal_with_errors(ret[1])

                    self.extract(content)

                    self.logger.debug(self.engine_name + " " + str(len(self.results['subdomain'])))
