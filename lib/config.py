#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import os
import sys
from lib.data import logger
from lib.data import conf
import configparser

def init_conf(path):
    logger.debug("Init srcscan config...")
    crawlergo_path = os.path.join(os.path.join(os.path.join(os.path.dirname(path),'tools'), 'crawlergo_windows_amd64'), 'crawlergo')
    configs = {
        "basic": {
            "thread_num": "10",
            "looptimer": str(24*60*60*14),
            "timeout": "5",
            "max_retries": "3",
        },
        "domain": {
            "proxy": False,
            "http_proxy": "http://127.0.0.1:1080",
            "https_proxy": "https://127.0.0.1:1080"
        },
        "crawlergo": {
            "crawlergo_path": crawlergo_path,
            "chrome_path": "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            "http_proxy": "http://127.0.0.1:8000",
            "https_proxy": "https://127.0.0.1:8000",
            "username": "username",
            "password": "password",
        },
        "smtp": {
            "mail_host": "smtp.163.com",
            "mail_port": "465",
            "mail_user": "username",
            "mail_pass": "password",
            "sender": "username@163.com",
            "receivers":"username@qq.com,username@163.com",
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
    sys.exit(logger.error("Please set the tentacle config in srcscan.conf..."))

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

