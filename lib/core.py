#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import os
import socket
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

def _run(domains_dic):
    database = Database(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'submon.db'))
    database.connect()
    database.init()
    filename = ('SubMon_subdomain_check_' + time.strftime("%Y%m%d_%H%M%S", time.localtime())) + '.xlsx'
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    if not os.path.exists(path):
        os.makedirs(path)
    for key in domains_dic.keys():
        domains = list(set(domains_dic[key]))
        if len(domains) > 0:
            logger.sysinfo("Scanning %d domains at %s." % (len(domains), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
            for domain in domains:
                logger.sysinfo("Scanning domain %s." % domain)
                _engines = [_(domain) for _ in engines.values()]
                loop = asyncio.get_event_loop()
                if debug:
                    loop.set_debug(True)
                for task in [asyncio.ensure_future(_engine.run()) for _engine in _engines ]:
                    loop.run_until_complete(task)
                # loop.close()
                ret = set()
                for _engine in _engines:
                    logger.sysinfo("{engine} Found {num} sites".format(engine=_engine.engine_name,
                                                                       num=len(_engine.results['subdomain'])))
                    ret.update(_engine.results['subdomain'])

                logger.sysinfo("Found %d subdomains of %s." % (len(ret),domain))
                for subdomain in ret:
                    database.insert_subdomain(subdomain,None,None,0,0,time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),domain)

                logger.sysinfo('Checking %d subdomains of %s.' % (len(ret),domain))
                curl = Curl()
                curl.load_targets(ret)
                for subdomain,url,title,status,content_length in curl.run():
                    database.update_subdomain_status(subdomain,url,title,status,content_length,time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                logger.sysinfo("Checked subdomains' status of %s." % domain)
            datas = []
            for domain in domains:
                for _row in database.select_mondomain(domain):
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
            tocsv(datas, path,filename,key)
            logger.sysinfo("Fineshed scan %d domains at %s." % (len(domains), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        else:
            logger.error("Loading %d domains." % (len(domains)))
    send_smtp(path, filename)
    database.disconnect()
    print()
    print()

def run(domains_dic,nomal):
    _run(domains_dic)
    if not nomal:
        if len(domains_dic) > 0:
            _time =  int(conf['config']['basic']['looptimer'])
            schedule.every(_time).seconds.do(_run,domains_dic)
            while True:
                schedule.run_pending()
                time.sleep(1)

def send_smtp(path,filename):
    try:
        mail_host = conf['config']['smtp']['mail_host']
        mail_port = int(conf['config']['smtp']['mail_port'])
        mail_user = conf['config']['smtp']['mail_user']
        mail_pass = conf['config']['smtp']['mail_pass']
        timeout = int(conf['config']['basic']['timeout'])
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

    while True:
        try:
            socket.setdefaulttimeout(timeout)
            smtpObj = smtplib.SMTP_SSL()
            smtpObj.connect(mail_host, mail_port)
            smtpObj.login(mail_user, mail_pass)
            smtpObj.sendmail(sender, receivers, message.as_string())
            logger.sysinfo("SMTP send success.")
            break
        except smtplib.SMTPException as e:
            logger.error("Error for SMTP: %s" % (str(e)))
        except socket.timeout as e:
            logger.error("Timeout for SMTP.")
        except Exception as e:
            logger.error("Error for SMTP, please check SMTP' config in submon.conf.")
        time.sleep(10)