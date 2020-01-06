#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import sys
import locale
import subprocess
import os
import re
import time
from lib.data import logger



def update_program():
    git_repository = "https://github.com/orleven/srcscan.git"
    success = False
    path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.exists(os.path.join(path, ".git")):
        msg = "Have not a git repository. Please checkout the 'srcscan' repository "
        msg += "from GitHub (e.g. 'git clone --depth 1 https://github.com/orleven/srcscan.git srcscan')"
        logger.error(msg)
    else:
        msg = "Updating srcscan to the latest version from the gitHub repository."
        logger.sysinfo(msg)

        msg = "The srcscan will try to update itself using 'git' command."
        logger.sysinfo(msg)

        logger.sysinfo("Update in progress.")

    try:
        process = subprocess.Popen("git checkout . && git pull %s HEAD" % git_repository, shell=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=path.encode(
                locale.getpreferredencoding()))  # Reference: http://blog.stastnarodina.com/honza-en/spot/python-unicodeencodeerror/
        poll_process(process, True)
        stdout, stderr = process.communicate()
        success = not process.returncode
    except (IOError, OSError) as ex:
        success = False
        logger.error(type(ex).__name__)


    if success:
        logger.success("The latest revision '%s'" % (get_revision_number()))
    else:
        if "Not a git repository" in stderr:
            msg = "Not a valid git repository. Please checkout the 'orleven/srcscan' repository "
            msg += "from GitHub (e.g. 'git clone --depth 1 https://github.com/orleven/srcscan.git srcscan')"
            logger.error(msg)
        else:
            logger.error("Update could not be completed ('%s')" % re.sub(r"\W+", " ", stderr).strip())

    if not success:
        if sys.platform == 'win32':
            msg = "for Windows platform it's recommended "
            msg += "to use a GitHub for Windows client for updating "
            msg += "purposes (http://windows.github.com/) or just "
            msg += "download the latest snapshot from "
            msg += "https://github.com/orleven/srcscan"
        else:
            msg = "For Linux platform it's required "
            msg += "to install a standard 'git' package (e.g.: 'sudo apt-get install git')"

        logger.sysinfo(msg)



def get_revision_number():
    """
    Returns abbreviated commit hash number as retrieved with "git rev-parse --short HEAD"
    """

    retVal = None
    filePath = None
    _ = os.path.dirname(__file__)

    while True:
        filePath = os.path.join(_, ".git", "HEAD")
        if os.path.exists(filePath):
            break
        else:
            filePath = None
            if _ == os.path.dirname(_):
                break
            else:
                _ = os.path.dirname(_)

    while True:
        if filePath and os.path.isfile(filePath):
            with open(filePath, "r") as f:
                content = f.read()
                filePath = None
                if content.startswith("ref: "):
                    filePath = os.path.join(_, ".git", content.replace("ref: ", "")).strip()
                else:
                    match = re.match(r"(?i)[0-9a-f]{32}", content)
                    retVal = match.group(0) if match else None
                    break
        else:
            break

    if not retVal:
        process = subprocess.Popen("git rev-parse --verify HEAD", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = process.communicate()
        match = re.search(r"(?i)[0-9a-f]{32}", stdout or "")
        retVal = match.group(0) if match else None

    return retVal[:7] if retVal else None


def poll_process(process, suppress_errors=False):
    """
    Checks for process status (prints . if still running)
    """

    while True:
        time.sleep(1)

        returncode = process.poll()

        if returncode is not None:
            if not suppress_errors:
                if returncode == 0:
                    logger.sysinfo(" done\n")
                elif returncode < 0:
                    logger.sysinfo(" process terminated by signal %d\n" % returncode)
                elif returncode > 0:
                    logger.sysinfo(" quit unexpectedly with return code %d\n" % returncode)

            break
