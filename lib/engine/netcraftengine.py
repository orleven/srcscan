#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import re
import asyncio
import execjs
from lib.connect import ClientSession
from yarl import URL
from urllib import parse
from random import randint
from lib.data import logger
from lib.enums import SEARCH_ERROR
from lib.engine.searchengine import SearchEngine

class NetcraftEngine(SearchEngine):

    def __init__(self,target,engine_name="Netcraft_Domain", **kwargs):
        self.engine = "https://searchdns.netcraft.com/"
        self.base_url = 'https://searchdns.netcraft.com/' \
                        '?restriction=site+ends+with&host={domain}' \
                        '&last={last_domain}&from={page_no}'
        self.js_url = 'https://searchdns.netcraft.com/errors/sha1.js'
        self.js_function = '''
            function get_netcraft_js_verification_response() {
                var challenge_token = unescape('{{netcraft_js_verification_challenge}}');
                var response = CryptoJS.SHA1(challenge_token);
			     return response +'';
            };
            '''
        self.last_domain = ''
        self.find_new_domain = False
        super(NetcraftEngine, self)\
            .__init__(target, engine_name=engine_name, **kwargs)

    def extract(self, content):
        next_page = re.compile('<A.*?>\s*<b>Next page</b>\s*</a>')
        pattern = re.compile('<a href="http[s]*://(.*{domain}).*?" rel="nofollow">'
                             .format(domain=self.target))
        try:
            links = pattern.findall(content)
            self.last_domain=self.target
            for link in links:
                if not link.startswith('http://') and not link.startswith('https://'):
                    link = "http://" + link
                subdomain = parse.urlparse(link).netloc

                if subdomain != self.target and subdomain.endswith(self.target):
                    if subdomain not in self.results['subdomain']:
                        self.logger.debug(
                        "{engine} Found {subdomain}".format(
                                engine=self.engine_name,subdomain=subdomain))
                        self.results['subdomain'].append(subdomain)
                self.last_domain = subdomain
        except Exception:
            pass
        if next_page.findall(content):
            # tell engine there still be next page
            return True
        else:
            return False

    def check_response_errors(self,content):
        if not content:
            return [False, SEARCH_ERROR.TIMEOUT]
        pattern = re.compile('Found (\d*) site')
        ret = pattern.findall(content)
        if ret:
            if int(ret[0]) == 0:
                return [False, SEARCH_ERROR.END]
            else:
                return [True, 0]
        else:
            return [False,SEARCH_ERROR.UNKNOWN]

    def generate_query(self):
        length = len(self.results['subdomain'])
        query = self.target
        if length==0:
            self.queries.append((query,0))
        else:
            self.queries.append((query,self.pre_pageno+1))

    def format_base_url(self, *args):
        if self.last_domain == self.target or not self.last_domain:
            self.last_domain = ''
        return self.base_url.format(domain=args[0],last_domain=self.last_domain,page_no=args[1]*20+1)

    async def should_sleep(self):
        self.logger.debug("{engine} sleep random time...".format(engine=self.engine_name))
        await asyncio.sleep(randint(3, 4))

    async def run(self):
        # cookies = {'netcraft_js_verification_response': ''}
        async with ClientSession() as session:
            async with session.get(self.engine, proxy=self.proxy) as res:
                if res!=None:
                    self.logger.error("{engine_name} is not available, skipping!"
                                      .format(engine_name=self.engine_name))
                    return
                self.logger.debug("{engine_name} is available, starting!"
                                 .format(engine_name=self.engine_name))
            try:
                filtered = session.cookie_jar.filter_cookies(self.engine)
                netcraft_js_verification_challenge = filtered['netcraft_js_verification_challenge'].value

                async with session.get(self.js_url, proxy=self.proxy) as res:
                    if res != None:
                        try:
                            _js = await res.text()
                        except:
                            return
                        cont_js = (_js + self.js_function.replace("{{netcraft_js_verification_challenge}}",netcraft_js_verification_challenge))
                        s = execjs.compile(cont_js)
                        netcraft_js_verification_response = s.call('get_netcraft_js_verification_response')
                        cookies = {
                            'netcraft_js_verification_challenge':netcraft_js_verification_challenge,
                            'netcraft_js_verification_response': netcraft_js_verification_response
                        }
                        session.cookie_jar.update_cookies(cookies,URL(self.engine))
            except:
                self.logger.error("{engine_name} is not available, skipping!".format(engine_name=self.engine_name))
                return
            self.generate_query()
            while len(self.queries):
                # session.cookie_jar.clear()
                # print(session.cookie_jar.filter_cookies(self.engine))
                (query, self.pre_pageno) = self.queries.popleft()
                self.pre_query = query
                url = self.format_base_url(query,self.pre_pageno)
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
                            break

                        if self.extract(content):
                            self.generate_query()
                        if len(self.queries)>0:
                            await self.should_sleep()# avoid being blocked
                        self.logger.debug("%s for %s: %d" %(self.engine_name ,self.target, len(self.results['subdomain'])))

