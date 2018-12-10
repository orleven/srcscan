#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'


import os
import sys
import random
from lib.data import logger
from lib.data import conf
import configparser

def init_conf(path):
    logger.debug("Init tentacle config...")
    configs = {
        "basic": {
            "thread_num": "100",
            "looptimer": str(12*60*60),
            "timeout": "5",
            "user_agent": '\n'.join([
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
                'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.0.16 (.NET CLR 3.5.30729)',
                'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.514.0 Safari/534.7',
                'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; de-de) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7',
                'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.4 (KHTML, like Gecko) Chrome/6.0.481.0 Safari/534.4',
                'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.1b4) Gecko/20090423 Firefox/3.5b4 (.NET CLR 3.5.30729)',
                'Mozilla/5.0 (Windows; U; Windows NT 6.0; nb-NO) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/5.0.2 Safari/533.18.5',
                'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.0.14) Gecko/2009082505 Red Hat/3.0.14-1.el5_4 Firefox/3.0.14',
                'Mozilla/5.0 (X11; U; Linux i686; tr-TR; rv:1.9.0.10) Gecko/2009042523 Ubuntu/9.04 (jaunty) Firefox/3.0.10',
                'Opera/9.80 (Macintosh; Intel Mac OS X; U; nl) Presto/2.6.30 Version/10.61',
            ])

        },
        "smtp": {
            "mail_host": "smtp.163.com",
            "mail_port": str(465),
            "mail_user": "username",
            "mail_pass": "password",
            "sender": "username@163.com",
            "receivers":"username@qq.com,username@163.com",
        },
        "proxy": {
            "proxy": False,
            "http_proxy": "http://127.0.0.1:1080",
            "https_proxy": "https://127.0.0.1:1080"
        },
        "google_api": {
            "developer_key": "developer_key",
            "search_enging": "search_enging"
        },
        # 下面接口以后再说
        # "zoomeye_api": {
        #     "username": "token@orleven.com",
        #     "password": "token@orleven.com"
        # },
        # "fofa_api": {
        #     "email": "test@orleven.com",
        #     "token": "test@orleven.com"
        # },
        # "shodan_api": {
        #     "token": "token@tentacle"
        # },
        # "github_api": {
        #     "token": "token@tentacle",
        # },
    }
    cf = configparser.ConfigParser()
    for section in configs.keys():
        cf[section] = configs[section]
    with open(path, 'w+') as configfile:
        cf.write(configfile)
    sys.exit(logger.error("Please set the tentacle config in tentacle.conf..."))

def load_conf(path):
    logger.debug("Load tentacle config...")
    cf = configparser.ConfigParser()
    cf.read(path)
    sections = cf.sections()
    configs = {}
    for section in sections:
        logger.debug("Load config: %s" % (section))
        config = {}
        for option in cf.options(section):
            config[option] = cf.get(section,option)
        configs[section] = config
    conf['config'] = configs

def update_conf(path,section,option,value):
    logger.debug("Update tentacle config: [%s][%s] => %s" %(section,option,value))
    cf = configparser.ConfigParser()
    cf.set(section,option,value)
    with open(path, 'w+') as configfile:
        cf.write(configfile)

