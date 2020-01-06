#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import re
from lib.connect import ClientSession
from lib.enums import SEARCH_ERROR
from lib.engine.searchengine import SearchEngine

class CrtSearchEngine(SearchEngine):
    """
    need a proxy
    """
    def __init__(self,target,engine_name="SSLCertificates_Domain", **kwargs):
        self.engine = "https://crt.sh"
        self.base_url = 'https://crt.sh/?q=%25.{domain}'
        super(CrtSearchEngine, self)\
            .__init__(target, engine_name=engine_name, **kwargs)

    def extract(self, content):
        pattern = re.compile('<TD>(.*?{domain})</TD>'.format(domain=self.target))
        try:
            links = pattern.findall(content)
            for link in links:
                link = link.strip('*.')
                if link != self.target and link not in self.results['subdomain']:
                    self.logger.debug(
                        "{engine} Found {subdomain}".format(
                            engine=self.engine_name, subdomain=link))
                    self.results['subdomain'].append(link)
        except Exception:
            pass

    def format_base_url(self,*args):
        return self.base_url.format(domain=args[0])

    def check_response_errors(self,content):
        if not content:
            return [False, SEARCH_ERROR.TIMEOUT]

        if "None found" in content:
            return [False,SEARCH_ERROR.END]
        elif "crt.sh ID" in content:
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

            url = self.format_base_url(self.target)

            self.logger.debug("{engine} {url}".format(engine=self.engine_name,url=url))

            async with session.get(url, proxy=self.proxy) as res:
                if res != None:
                    try:
                        content = await res.text()
                    except:
                        content = ''

                    ret = self.check_response_errors(content)
                    if not ret[0]:
                        self.deal_with_errors(ret[1])
                        return
                    self.extract(content)

    def deal_with_errors(self,error_code):
        """subclass should override this function for identify security mechanism"""
        if error_code == SEARCH_ERROR.END:
            self.logger.debug("{engine} has no results".format(engine=self.engine_name))
        elif error_code == SEARCH_ERROR.UNKNOWN:
            # raise ReconResponseContentErrorException
            self.logger.error("response content error")
        elif error_code == SEARCH_ERROR.TIMEOUT:
            self.logger.debug("{engine} is not available now, Stop!".format(engine=self.engine_name))

