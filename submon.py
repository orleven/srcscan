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
    parser.add_argument('-n', "--nomal", action='store_true', help="Nomal model", default=False)
    parser.add_argument('-f', "--domain_file",metavar='File', type=str, default=None,help='Load domain from file (e.g. domains.txt)')
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
        debug = True
        logger.set_level(CUSTOM_LOGGING.DEBUG)
    nomal = args.nomal
    if args.help:
        parser.print_help()
    elif args.domain:
        start(args.domain, nomal)
    elif args.domain_file:
        start(args.domain_file, nomal)
    else:
        parser.print_help()

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Submon is a SRC assistant tool that periodically scans subdomains and requests WEB services on port 80/443 to check if it is available, and send result to you by e-mail.',formatter_class=argparse.RawTextHelpFormatter, add_help=False)
    parser = arg_set(parser)
    handle(parser)

