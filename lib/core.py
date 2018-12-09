#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import os
import sys
import asyncio
import schedule
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.header import Header
from lib.data import debug
from lib.data import logger
from lib.data import conf
from lib.curl import Curl
from lib.common import tocsv
from lib.database import Database
from lib.engine.chinazengine import ChinazEngine
from lib.engine.askengine import AskEngine
from lib.engine.bingengine import BingEngine
from lib.engine.baiduengine import BaiduEngine
from lib.engine.crtsearchengine import CrtSearchEngine
from lib.engine.netcraftengine import NetcraftEngine
from lib.engine.yahooengine import YahooEngine
from lib.engine.bugscannerengine import BugscannerEngine
from lib.engine.dnsdumpsterengine import DNSdumpsterEngine
from lib.engine.threatcrowdengine import ThreatCrowdEngine
from lib.engine.virustotalengine import VirustotalEngine
from lib.engine.googleengine import GoogleEngine

engines = {
    'google': GoogleEngine,
    'ask': AskEngine,
    'yahoo': YahooEngine,
    'baidu': BaiduEngine,
    'threatcrowd': ThreatCrowdEngine,
    'bing': BingEngine,
    'ssl': CrtSearchEngine,
    'dnsdumpster': DNSdumpsterEngine,
    'virustotal': VirustotalEngine,
    'netcraft': NetcraftEngine,
    'chinaz': ChinazEngine,
    'bugscanner': BugscannerEngine,
}

def _run(domains):
    if len(domains) > 0:
        logger.sysinfo("Scanning %d domains at %s." % (len(domains), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        database = Database(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'submon.db'))
        database.connect()
        database.init()
        for domain in domains:
            logger.sysinfo("Scanning and checking domain %s." % domain.netloc)
            _engines = [_(domain) for _ in engines.values()]
            loop = asyncio.get_event_loop()
            if debug:
                loop.set_debug(True)
            for task in [asyncio.ensure_future(_engine.run()) for _engine in _engines ]:
                loop.run_until_complete(task)
            # loop.close()
            ret = set()
            for _engine in _engines:
                ret.update(_engine.subdomains)

            logger.sysinfo("Found %d subdomains of %s." % (len(ret),domain.netloc))
            for subdomain in ret:
                database.insert_subdomain(subdomain,None,None,0,0,time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),domain.netloc)
            logger.sysinfo("Checking subdomains' status of %s." % domain.netloc)

            logger.sysinfo('Checking %d subdomains of %s.' % (len(ret),domain.netloc))
            curl = Curl()
            curl.load_targets(ret)
            for subdomain,url,title,status,content_length in curl.run():
                database.update_subdomain_status(subdomain,url,title,status,content_length,time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            logger.sysinfo("Check subdomains' status of %s over." % domain.netloc)


        datas = []
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        if not os.path.exists(path):
            os.makedirs(path)
        filename = ('SubMon_子域名检测_' + time.strftime("%Y%m%d_%H%M%S", time.localtime())) + '.xlsx'
        for domain in domains:
            for _row in database.select_mondomain(domain.netloc):
                data = {
                    "subdomain": _row[0],
                    "url": _row[1],
                    "title": _row[2],
                    "status": _row[3],
                    "len": _row[4],
                    "update_time" : _row[5],
                    "domain": _row[6]
                }
                datas.append(data)
        tocsv(datas, path,filename)
        send_smtp(path,filename)
        database.disconnect()
        logger.sysinfo("Fineshed scan %d domains at %s." % (len(domains), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        print()
        print()
        print()
        print()
    else:
        logger.error("Loading %d domains." % (len(domains)))



def run(domains):
    _run(domains)
    if len(domains) > 0:
        _time =  int(conf['config']['basic']['looptimer'])
        schedule.every(_time).seconds.do(_run,domains)
        while True:
            schedule.run_pending()
            time.sleep(1)

def send_smtp(path,filename):

    try:
        mail_host = conf['config']['smtp']['mail_host']
        mail_port = int(conf['config']['smtp']['mail_port'])
        mail_user = conf['config']['smtp']['mail_user']
        mail_pass = conf['config']['smtp']['mail_pass']

        sender = conf['config']['smtp']['sender']
        receivers = conf['config']['smtp']['receivers'].split(',')
    except:
        logger.error("Load config error: smtp, please check the config in submon.conf.")
        return

    content = '''
    你好，

        SubMon 子域名检测结果 【%s】，请查收。

                                                                                —— by SubMon
    ''' %(filename)
    message = MIMEMultipart()
    message['From'] = "submon<%s>" %sender
    message['To'] = ','.join(receivers)
    message['Subject'] = Header(filename, 'utf-8')
    message.attach( MIMEText(content, 'plain', 'utf-8'))

    with open(os.path.join(path,filename), 'rb') as f:
        att = MIMEText(f.read(), 'base64', 'utf-8')
        att["Content-Type"] = 'application/octet-stream'
        att.add_header("Content-Disposition", "attachment", filename=("utf-8", "", filename))
        message.attach(att)

    try:
        smtpObj = smtplib.SMTP()
        smtpObj.connect(mail_host, mail_port)  # 25 为 SMTP 端口号
        smtpObj.login(mail_user, mail_pass)
        smtpObj.sendmail(sender, receivers, message.as_string())
        logger.sysinfo("SMTP send success.")
    except smtplib.SMTPException as e:
        logger.error("Error for SMTP: %s" %(type(e).__name__))
