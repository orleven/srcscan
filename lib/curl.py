#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import sys
import random
import traceback
import threading
from bs4 import BeautifulSoup
from lib.data import conf
from collections import deque
from lib.data import logger
from lib.engine.engine import default_headers
from requests import request
from requests import packages
from requests.exceptions import ConnectionError
from requests.exceptions import TooManyRedirects
from requests.exceptions import ChunkedEncodingError
from requests.exceptions import ConnectTimeout
from requests.exceptions import ReadTimeout
packages.urllib3.disable_warnings()

class Curl():
    def __init__(self):
        self.targets = deque()
        self.ret = deque()
        self.type_code = sys.getfilesystemencoding()
        self.thread_count = self.thread_num = int(conf['config']['basic']['thread_num'])
        self.scanning_count = self.scan_count = self.found_count = self.error_count = self.total = 0
        self.is_continue = True
        self.load_lock = threading.Lock()


    def load_targets(self,targets):
        for target in targets:
            self.targets.append(target)

    def run(self):
        thread_list = []
        for i in range(0, self.thread_num):
            t = threading.Thread(target=self._work, name=str(i))
            t.setDaemon(True)
            t.start()
            thread_list.append(t)
        for _thread in thread_list:
            _thread.join()

        return self.ret

    def _work(self):
        while True:
            self.load_lock.acquire()
            if len(self.targets) > 0 and self.is_continue:
                subdomain = self.targets.popleft()
                self.load_lock.release()
                try:
                    logger.debug("Curling %s..." %(subdomain))
                    flag = False
                    codes = ['utf-8', 'gbk']
                    for pro in ['http://', "https://"]:
                        url = pro + subdomain + '/'
                        res = self._curl(url,headers = default_headers)
                        if res != None:
                            try:
                                length = int(res.headers['content-length'])
                            except:
                                length = len(str(res.headers)) + len(res.text)
                            soup = BeautifulSoup(res.text, "html5lib")
                            if soup !=None:
                                title = soup.title
                                if title == None or title.string == None or title.string == '':
                                    title = "网页没有标题".encode('utf-8')
                                else:
                                    if res.encoding!= None:
                                        title = title.string.encode(res.encoding)
                                        codes.append(res.encoding)
                                    else:
                                        title = title.string
                                codes.append(self.type_code)
                                for j in range(0, len(codes)):
                                    try:
                                        title = title.decode(codes[j]).strip().replace("\r", "").replace("\n", "")
                                        break
                                    except:
                                        continue
                                    finally:
                                        if j + 1 == len(codes):
                                            title = '[网页标题编码错误]'
                                self.ret.append([subdomain, url, title, res.status_code, length])
                                flag = True
                                break
                            else:
                                title = '[网页标题编码错误]'
                                self.ret.append(
                                    [subdomain, url, title, res.status_code,length])
                    if not flag:
                        self.ret.append([subdomain, "", "", 0, 0])
                except Exception:
                    self.errmsg = traceback.format_exc()
                    self.is_continue = False
                    logger.error(self.errmsg)
            else:
                self.load_lock.release()
                break

    def _curl(self,url, params = None, **kwargs):
        headers = kwargs.get('headers')
        if headers == None:
            headers = {}
        headers["User-Agent"] = random.choice(conf['config']['basic']['user_agent'].split('\n'))
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        headers['Referer'] = url
        kwargs.setdefault('headers', headers)
        kwargs.setdefault('timeout', int(conf['config']['basic']['timeout']))
        kwargs.setdefault('verify', False)

        if conf['config']['proxy']['proxy'].lower() == 'true':
            try:
                _proxies = {
                    'http': conf['config']['proxy']['http_proxy'],
                    'https': conf['config']['proxy']['https_proxy']
                }
                kwargs.setdefault('proxies', _proxies)
            except:
                logger.error("Error http(s) proxy: %s or %s." % (
                conf['config']['proxy']['http_proxy'], conf['config']['proxy']['https_proxy']))
        try:
            return request('get', url, params=params, **kwargs)
        except ConnectionError as e:
            return None
        except ReadTimeout as e:
            return None
        except TooManyRedirects as e:
            kwargs.setdefault('allow_redirects', False)
            return request('get', url, params=params, **kwargs)
        except Exception as e:
            logger.error(type(e).__name__)

