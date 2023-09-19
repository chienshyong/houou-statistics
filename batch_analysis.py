# -*- coding: utf-8 -*-
# This script is for running multiple analyses at once,
# to avoid reading the db and decompressing each log multiple times.

import bz2
import sqlite3
from lxml import etree
from tqdm import tqdm
import cProfile

from analyzers.pond_traits import PondTraits

analyzers = [PondTraits()]
allowed_types = ["169", "225", "185"]
log_database = r'C:\Users\leecs1\Downloads\es4p.db'

def RunAnalysis():
    decompress = bz2.decompress
    XML = etree.XML

    with sqlite3.connect(log_database) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM logs')
        rowcount = cursor.fetchone()[0]
        cursor.execute('SELECT * FROM logs LIMIT 1000')
        last_print = 0

        for i in tqdm(range(1000), ncols=80):
            log = cursor.fetchone()
            if log is None:
                break

            content = decompress(log[2])
            xml = XML(content, etree.XMLParser(recover=True))
            game_type = xml.find("GO").attrib["type"]

            if game_type in allowed_types:
                for analyzer in analyzers:
                    analyzer.ParseLog(xml, log[0])
            
            if i - last_print > 100000:
                last_print = i
                for analyzer in analyzers:
                    print("==========")
                    analyzer.PrintResults()

    for analyzer in analyzers:
        print("==========")
        analyzer.PrintResults()
    
    return True

RunAnalysis()