#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import argparse
import asyncio
import sys
from lib.common import banner
from lib.core import start
from lib.data import logger
from lib.log import CUSTOM_LOGGING
from lib.common import config_parser
from lib.common import check_update

sys.dont_write_bytecode = True

try:
    __import__("lib.version")
except ImportError:
    exit("[!] wrong installation detected (missing modules). Visit 'https://' for further details")

def arg_set(parser):
    parser.add_argument('-d', "--domain", metavar='Domain', type=str, default=None, help='Set domain to scan')
    parser.add_argument('-df', "--domain_file",metavar='DomainFile', type=str, default=None,help='Load domain from file (e.g. domains.txt)')
    parser.add_argument('-ss', "--scheduled_scan", action='store_true', help="scheduled scan", default=False)
    parser.add_argument('-vs', "--vul_scan", action='store_true', help="Vul Scan", default=False)
    parser.add_argument("--debug", action='store_true', help="Show debug info", default=False)
    parser.add_argument("--update", action='store_true', help="Update", default=False)
    parser.add_argument("--help", help="Show help", default=False, action='store_true')
    return parser

def handle(parser):
    args = parser.parse_args()
    banner()
    check_update(args)
    config_parser()
    # asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    if args.debug:
        logger.set_level(CUSTOM_LOGGING.DEBUG)
    if args.help:
        parser.print_help()
    elif args.domain:
        start(args.domain, args.scheduled_scan, args.vul_scan)
    elif args.domain_file:
        start(args.domain_file, args.scheduled_scan, args.vul_scan)
    else:
        parser.print_help()

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='SRCScan is a SRC assistant tool that periodically scans subdomains and requests WEB services on port 80/443 to check if it is available, and send result to you by e-mail.',formatter_class=argparse.RawTextHelpFormatter, add_help=False)
    parser = arg_set(parser)
    handle(parser)

