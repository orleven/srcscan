#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import re
import json
import asyncio
import execjs
import aiohttp
from urllib import parse
from random import randint
from lib.data import logger
from lib.enums import SEARCH_ERROR
from lib.engine.searchengine import SearchEngine

class ThreatCrowdEngine(SearchEngine):
    """need a proxy"""
    def __init__(self,target,engine_name="ThreatCrowd_Domain", **kwargs):
        self.engine = "https://www.threatcrowd.org"
        self.base_url = 'https://www.threatcrowd.org/searchApi/v2/domain/report/?domain={domain}'
        super(ThreatCrowdEngine, self)\
            .__init__(target, engine_name=engine_name, **kwargs)

        self.headers['referer'] = "https://www.threatcrowd.org/" \
                                  "searchApi/v2/domain/report/?domain={domain}"\
                                    .format(domain=self.target)



    def format_base_url(self, *args):
        return self.base_url.format(domain=args[0])

    def check_response_errors(self,content):
        if not content:
            return [False, SEARCH_ERROR.TIMEOUT]
        if '"response_code":"0"' in content:
            return [False,SEARCH_ERROR.END]
        elif '"response_code":"1"' in content:
            return [True,0]
        else:
            return [False,SEARCH_ERROR.UNKNOWN]

    def extract(self,content):
        try:
            subdomains = json.loads(content)['subdomains']
            for subdomain in subdomains:
                self.results['subdomain'].append(subdomain)
            self.logger.debug("{engine} Found {num} subdomains"
                             .format(engine=self.engine_name,num=len(self.results['subdomain'])))
        except Exception:
            pass

    def extract_pass(self,content):
        """
        提取block内容
        :param content:
        :return:
        """
        jschl_vc = re.compile('<input type="hidden" name="jschl_vc" value="(.*?)"/>')
        jschl_vc = self.regex(jschl_vc,content)
        pass_ = re.compile('<input type="hidden" name="pass" value="(.*?)"/>')
        pass_ = self.regex(pass_,content)
        pattern = re.compile('setTimeout\(function\(\)\{(.*?)f.action \+= location.hash;', re.S)
        code = self.regex(pattern,content)
        code = re.sub('\s+(t = document.*?);\s+;', '', code, flags=re.S)
        code = re.sub('a.value', 'value', code)
        code = re.sub('t.length', '19', code)
        code = 'function test(){' + code.strip() + ';return value;}'
        s = execjs.compile(code)
        t = s.call('test')
        params = "/cdn-cgi/l/chk_jschl?jschl_vc={0}&pass={1}&jschl_answer={2}"
        self.params = params.format(jschl_vc,pass_,t)
        self.logger.debug(self.params)

    def regex(self,pattern,content):
        data = pattern.findall(content)
        if data:
            return data[0]
        return None

    async def should_sleep(self):
        self.logger.debug("{engine} sleep random time...".format(engine=self.engine_name))
        await asyncio.sleep(randint(4, 5))


    async def check_engine_available(self,session,engine):
        content = await self.get(session, engine)
        if content:
            try:
                self.extract_pass(content)
                return self.engine + self.params
            except:
                return None
        else:
            return None


    async def run(self):
        async with aiohttp.ClientSession() as session:
            url = self.format_base_url(self.target)
            url = await self.check_engine_available(session,url)
            if not url:
                self.logger.error("{engine_name} is not available, skipping!"
                                  .format(engine_name=self.engine_name))
                return
            self.logger.debug("{engine_name} is available, starting!"
                             .format(engine_name=self.engine_name))
            await self.should_sleep()
            self.logger.debug("{engine} {url}".format(engine=self.engine_name,url=url))
            content = await self.get(session, url)


            ret = self.check_response_errors(content)
            if not ret[0]:
                self.deal_with_errors(ret[1])
                return

            self.extract(content)
            self.logger.debug(self.engine_name + " " + str(len(self.results['subdomain'])))