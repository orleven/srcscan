#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import os
import sys
import argparse
# import uvloop
import asyncio
from lib.common import banner
from lib.core import run
from lib.data import logger
from lib.data import debug
from lib.data import conf
from lib.log import CUSTOM_LOGGING
from lib.common import config_parser
from lib.common import check_domain
from lib.common import check_update

sys.dont_write_bytecode = True

try:
    __import__("lib.version")
except ImportError:
    exit("[!] wrong installation detected (missing modules). Visit 'https://' for further details")

def arg_set(parser):
    parser.add_argument('-d', "--domain", metavar='Domain', type=str, default=None, help='Set domain to scan')
    parser.add_argument('-f', "--domain_file",metavar='File', type=str, default=None,help='Load domain from file (e.g. domains.txt)')
    parser.add_argument("--debug", action='store_true', help="Show debug info", default=False)
    parser.add_argument("--update", action='store_true', help="Update", default=False)
    return parser

def handle(parser):
    args = parser.parse_args()
    banner()
    check_update(args)
    config_parser()
    domains = []
    # asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    if args.debug:
        debug = True
        logger.set_level(CUSTOM_LOGGING.DEBUG)
    if args.domain:
        domain = check_domain(args.domain)
        if not domain:
            sys.exit(logger.error("Error domain: %s" % domain))
        logger.sysinfo("Loading and checking domain %s." % args.domain)
        domains.append(domain)
    elif args.domain_file:
        if os.path.isfile(args.domain_file):
            logger.sysinfo("Loading and checking domains of file %s." % args.domain_file)
            with open(args.domain_file, 'r') as f:
                for domain in  f.readlines():
                    domain = check_domain(domain)
                    if not domain:
                        logger.error("Error domain: %s" % domain)
                    domains.append(domain)
        else:
            logger.sysinfo("Error for domain file, please check the file %s." % args.domain_file)
    else:
        parser.print_help()

    run(domains)

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='submon', epilog='submon',formatter_class=argparse.RawTextHelpFormatter, add_help=False)
    parser = arg_set(parser)
    handle(parser)

