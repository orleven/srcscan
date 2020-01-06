#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import os
import sys
import glob
import socket
import asyncio
import schedule
import subprocess
import time
import smtplib
import json
import re
from aiohttp import BasicAuth
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.header import Header
from lib.data import debug
from lib.connect import ClientSession
from lib.data import logger
from lib.data import conf
from lib.common import tocsv
from lib.database import Database
from lib.common import check_domain
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

def read_domain_file(domain_file, domains_dic):
    domains_dic[os.path.basename(domain_file)] = []
    logger.sysinfo("Loading and checking domains of file %s." % domain_file)
    with open(domain_file, 'r') as f:
        for d in f.readlines():
            domain = check_domain(d)
            if not domain and d.strip()!='':
                logger.error("Error domain: %s" % d)
                continue
            domains_dic[os.path.basename(domain_file)].append(domain)
    return domains_dic

def run(target, vul_scan):
    domains_dic = {}

    if os.path.isdir(target):
        domain_file_list = glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), target, '*.*'))
        for domain_file in domain_file_list:
            domains_dic = read_domain_file(domain_file, domains_dic)

    elif os.path.isfile(target):
        domains_dic = read_domain_file(target, domains_dic)

    elif check_domain(target):
        logger.sysinfo("Loading and checking domain %s." % target)
        domains_dic[target] = [target]

    else:
        sys.exit(logger.error("Error domain: %s" % target))
    _run(domains_dic, vul_scan)

def subdomain_scan(domain, ret, now_time):
    database = Database(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'srcscan.db'))
    database.connect()
    database.init()
    logger.sysinfo("Scanning domain %s." % domain)
    _engines = [_(domain) for _ in engines.values()]
    loop = asyncio.get_event_loop()
    if debug:
        loop.set_debug(True)
    for task in [asyncio.ensure_future(_engine.run()) for _engine in _engines]:
        loop.run_until_complete(task)
    # loop.close()

    for _engine in _engines:
        logger.sysinfo("{engine} Found {num} sites".format(engine=_engine.engine_name,
                                                           num=len(_engine.results['subdomain'])))
        ret.update(_engine.results['subdomain'])
    logger.sysinfo("Found %d subdomains of %s." % (len(ret), domain))
    for subdomain in ret:
        database.insert_subdomain(subdomain, None, None, 0, 0, now_time, domain)
    database.disconnect()
    return ret

def vul_scan(domain, now_time):
    datas = []
    database = Database(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'srcscan.db'))
    database.connect()
    database.init()
    logger.sysinfo("Scaning vul for: %s " % (domain))
    for _row in database.select_mondomain(domain):
        data = {
            "subdomain": _row[0],
            "url": _row[1],
            "title": _row[2],
            "status": _row[3],
            "len": _row[4],
            "update_time": _row[5],
            "domain": _row[6]
        }
        datas.append(data)


    for data in datas:
        if data['status'] != 0:
            logger.sysinfo("Scaning vul for %s." % (data['url']))
            crawlergo_scan(data['url'], data['domain'], now_time, database)

    logger.sysinfo("Scaned vul for: %s " % (domain))
    database.disconnect()

async def get_title(req_list):
    ret = []
    async with ClientSession() as session:
        for subdomain in req_list:
            try:
                logger.debug("Curling %s..." % (subdomain))
                flag = False
                for pro in ['http://', "https://"]:
                    url = pro + subdomain + '/'
                    async with session.get(url=url) as response:
                        if response != None:
                            try:
                                res = await response.read()
                            except:
                                res = ""
                            status = response.status
                            try:
                                res = str(res, 'utf-8')
                            except UnicodeDecodeError:
                                res = str(res, 'gbk')
                            except:
                                res = "网页编码错误"

                            m = re.search('<title>(.*)<\/title>', res.lower())
                            if m != None and m.group(1):
                                title = m.group(1)
                            else:
                                title = '网页没有标题'

                            try:
                                length = int(response.headers['content-length'])
                            except:
                                length = len(str(response.headers)) + len(res)

                            ret.append([subdomain, url, title, status, length])
                            flag = True
                            break
                if not flag:
                    ret.append([subdomain, "", "", 0, 0])
            except Exception as e:
                logger.error(str(e))
    return ret


def title_scan(domain, ret, now_time):
    ret = list(ret)
    database = Database(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'srcscan.db'))
    database.connect()
    database.init()
    logger.sysinfo('Checking %d subdomains of %s.' % (len(ret), domain))
    loop = asyncio.get_event_loop()
    thread_num = int(conf['config']['basic']['thread_num'])
    thread_num = thread_num if len(ret)>thread_num else thread_num
    tasks = []
    for i in range(0, thread_num):
        tasks.append(asyncio.ensure_future(get_title([ret[x] for x in range(0+i, len(ret), thread_num)])))
    loop.run_until_complete(asyncio.wait(tasks))
    for task in tasks:
        for subdomain, url, title, status, content_length in task.result():
            database.update_subdomain_status(subdomain, url, title, status, content_length, now_time)
    database.disconnect()
    logger.sysinfo("Checked subdomains' status of %s." % domain)

def _run(domains_dic, vul_scan_flag):
    now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    filename = 'srcscan_subdomain_check_' + time.strftime("%Y%m%d_%H%M%S", time.localtime()) + '.xlsx'
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    if not os.path.exists(path):
        os.makedirs(path)
    for key in domains_dic.keys():
        domains = list(set(domains_dic[key]))
        if len(domains) > 0:
            logger.sysinfo("Scanning %d domains at %s." % (len(domains), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
            for domain in domains:
                ret = set()
                ret = subdomain_scan(domain, ret, now_time)
                title_scan(domain, ret, now_time)
                if vul_scan_flag:
                    vul_scan(domain, now_time)

            logger.sysinfo("Fineshed scan %d domains at %s." % (len(domains), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))

            save(domains, path, filename, key)

        else:
            logger.error("Loading %d domains." % (len(domains)))
    send_smtp(path, filename)

def save(domains, path, filename, key):
    datas = []
    database = Database(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'srcscan.db'))
    database.connect()
    database.init()
    for domain in domains:
        for _row in database.select_mondomain(domain):
            data = {
                "subdomain": _row[0],
                "url": _row[1],
                "title": _row[2],
                "status": _row[3],
                "len": _row[4],
                "update_time": _row[5],
                "domain": _row[6]
            }
            datas.append(data)

    tocsv(datas, path, filename, key)

    database.disconnect()


def crawlergo_scan(url, domain, now_time, database):
    cmd = [conf['config']['crawlergo']['crawlergo_path'], "-c", conf['config']['crawlergo']['chrome_path'], "-t", "20", "-f",
           "smart", "--fuzz-path", "--output-mode", "json", url]
    rsp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = rsp.communicate()
    try:
        result = json.loads(output.decode().split("--[Mission Complete]--")[1])
        _req_list = result["req_list"]
        sub_domain_list = result["sub_domain_list"]
    except:
        return
    req_list = []
    for req in _req_list:
        if url.strip('http://').strip('https://').rstrip('/') in req['url']:
            req_list.append(req)
        else:
            logger.sysinfo("Skip %s url by %s." % (req['url'], url))

    logger.sysinfo("Found %d url by %s." % (len(req_list), url))
    logger.sysinfo("Found %d subdomains by %s." % (len(sub_domain_list), url))
    for subdomain in sub_domain_list:
        database.insert_subdomain(subdomain, None, None, 0, 0, now_time, domain)

    # logger.sysinfo('Checking %d subdomains by %s.' % (len(sub_domain_list), url))
    # for subdomain, url, title, status, content_length in curl.run():
    #     database.update_subdomain_status(subdomain, url, title, status, content_length, now_time)
    # logger.sysinfo("Checked subdomains' status by %s." % url)

    loop = asyncio.get_event_loop()
    thread_num = int(conf['config']['basic']['thread_num'])
    thread_num = thread_num if len(req_list) > thread_num else thread_num
    tasks = []
    for i in range(0, thread_num):
        tasks.append(asyncio.ensure_future(go_request([req_list[x] for x in range(0+i, len(req_list), thread_num)],url)))
    loop.run_until_complete(asyncio.wait(tasks))

async def go_request(req_list,source):
    async with ClientSession() as session:
        for req in req_list:
            url = req['url']
            method = req['method']
            headers = req['headers']
            logger.debug("Curling %s..." % (url))

            proxy = conf['config']['crawlergo']['http_proxy']
            username = conf['config']['crawlergo']['username']
            password = conf['config']['crawlergo']['password']

            if username.strip() != '' and password.strip() != '':
                proxy_auth = BasicAuth(username, password)
            else:
                proxy_auth = None
            try:
                logger.debug("Xray scan {}, from url {} ".format(url, source))
                async with session.request(method, url=url, headers=headers, proxy=proxy,proxy_auth=proxy_auth) as res:
                    pass
            except:
                pass


def start(target, scheduled_scan, vul_scan):
    run(target, vul_scan)
    if scheduled_scan:
        _time = int(conf['config']['basic']['looptimer'])
        schedule.every(_time).seconds.do(run, target)
        while True:
            schedule.run_pending()
            time.sleep(1)

def send_smtp(path,filename):
    try:
        mail_host = conf['config']['smtp']['mail_host'].strip()
        mail_port = int(conf['config']['smtp']['mail_port'])
        mail_user = conf['config']['smtp']['mail_user']
        mail_pass = conf['config']['smtp']['mail_pass']
        timeout = int(conf['config']['basic']['timeout'])
        sender = conf['config']['smtp']['sender']
        receivers = conf['config']['smtp']['receivers'].split(',')
    except:
        logger.error("Load config error: smtp, please check the config in srcscan.conf.")
        return


    content = '''
    你好，

        srcscan 子域名检测结果 【%s】，请查收。

                                                                                —— by srcscan
    ''' %(filename)
    message = MIMEMultipart()
    message['From'] = "srcscan<%s>" %sender
    message['To'] = ','.join(receivers)
    message['Subject'] = Header(filename, 'utf-8')
    message.attach( MIMEText(content, 'plain', 'utf-8'))

    with open(os.path.join(path,filename), 'rb') as f:
        att = MIMEText(f.read(), 'base64', 'utf-8')
        att["Content-Type"] = 'application/octet-stream'
        att.add_header("Content-Disposition", "attachment", filename=("utf-8", "", filename))
        message.attach(att)

    n = 3
    while n > 0:
        try:
            socket.setdefaulttimeout(timeout)
            smtpObj = smtplib.SMTP_SSL(host=mail_host)
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
            print(str(e))
            logger.error("Error for SMTP, please check SMTP' config in srcscan.conf.")
        time.sleep(10)
        n -= 1
