# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os
import pprint
from pymongo import MongoClient

class MyPrettyPrinter(pprint.PrettyPrinter):
    def format(self, object, context, maxlevels, level):
        if isinstance(object, unicode):
            return (object.encode('utf-8'), True, False)
        return pprint.PrettyPrinter.format(self, object, context, maxlevels, level)

class CachedpagefinderPipeline(object):

    def open_spider(self, spider):
        self.client = MongoClient()
        self.db = self.client['girlspic-database']
        self.db.dbtest.drop()

    def close_spider(self, spider):

        if os.path.exists('Log') != True:
            try:
                os.makedirs('Log')
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        # for debug use, make sure every links status
        file = open ('Log/PrepareLink.txt', 'w')
        for item in spider.prepare_Links:
            print>>file, item.encode('utf-8')
        file.close()

        file = open ('Log/DoneLink.txt', 'w')
        for item in spider.done_links:
            print>>file, item.encode('utf-8')
        file.close()

        file = open ('Log/IgnoreLink.txt', 'w')
        for item in spider.unhandle_links:
            print>>file, item.encode('utf-8')
        file.close()


    def process_item(self, item, spider):
        if item['personal'] != None:
            self.db.dbtest.insert_one(item['personal'])
        return item
