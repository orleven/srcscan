#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'orleven'

import sqlite3
from lib.data import logger
from lib.common import get_safe_ex_string


# API objects
class Database(object):
    filepath = None

    def __init__(self, database=None):
        self.database = self.filepath if database is None else database
        self.connection = None
        self.cursor = None

    def connect(self, who="storage"):
        self.connection = sqlite3.connect(self.database, timeout=3, isolation_level=None, check_same_thread=False)
        self.cursor = self.connection.cursor()


    def disconnect(self):
        if self.cursor:
            self.cursor.close()

        if self.connection:
            self.connection.close()

    def commit(self):
        self.connection.commit()

    def insert_subdomain(self, subdomain,url,title,status,len,update_time,mon_domain):
        logger.debug("Insert subdomain: %s" % (subdomain))
        self.execute("INSERT  OR IGNORE INTO subdomain (subdomain,url,title,status,len,update_time,mon_domain) VALUES (?, ?, ?, ?, ?, ?, ?)",(subdomain,url,title,status,len,update_time,mon_domain))


    def update_subdomain_status(self, subdomain,url,title,status,len,update_time):
        logger.debug("Update subdomain: %s" % (subdomain))
        self.execute("UPDATE subdomain set  url = ?, title = ?, status = ?, len = ?, update_time = ? WHERE subdomain = ? and ( title != ? or status != ?)",(url,title,status,len,update_time,subdomain,title,status))

    def replace_subdomain_status(self, subdomain,url,title,status,len,update_time,mon_domain):
        logger.debug("Replace subdomain: %s" % (subdomain))
        self.execute(
            "REPLACE into subdomain (subdomain, url,title,status,len,update_time,mon_domain) VALUES (?, ?, ?, ?, ?, ?, ?) ",(subdomain, url, title, status, len, update_time,mon_domain))


    def detele_subdomain(self, subdomain):
        self.execute("DELETE from subdomain WHERE subdomain = ?",(subdomain))

    def detele_domain(self, mon_domain):
        self.execute("DELETE from subdomain WHERE mon_domain = ?",(mon_domain))

    def select_all(self):
        return self.execute("SELECT * FROM subdomain ORDER BY update_time DESC ")

    def select_mondomain(self,mon_domain):
        return self.execute("SELECT * FROM subdomain WHERE mon_domain = ? ORDER BY update_time DESC " ,(mon_domain,))

    # def select_like(self,subdomain):
    #     return self.execute("SELECT * FROM subdomain WHERE subdomain LIKE  ?" ,('%'+subdomain+'%',))

    def execute(self, statement, arguments=None):
        while True:
            try:
                if arguments:
                    self.cursor.execute(statement, arguments)
                else:
                    self.cursor.execute(statement)
            except sqlite3.OperationalError as ex:
                if not "locked" in get_safe_ex_string(type(ex).__name__):
                    raise
            else:
                break

        if statement.lstrip().upper().startswith("SELECT"):
            return self.cursor.fetchall()



    def init(self):
        self.execute("CREATE TABLE IF NOT EXISTS subdomain("
                  # "id INTEGER KEY AUTOINCREMENT, "
                  "subdomain TEXT PRIMARY KEY , url TEXT, title TEXT, status INTEGER, len INTEGER, update_time TEXT, mon_domain TEXT"
                  ")")
