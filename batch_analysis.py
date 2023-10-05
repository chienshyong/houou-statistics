# -*- coding: utf-8 -*-
# This script is for running multiple analyses at once,
# to avoid reading the db and decompressing each log multiple times.

import bz2
import sqlite3
from lxml import etree
from tqdm import tqdm
import traceback

from analyzers.sotogawa import Sotogawa
from analyzers.first_simple_tile import FirstSimpleTile

analyzers = [Sotogawa(), FirstSimpleTile()]
allowed_types = ["169", "225", "185"]
log_database = r'C:\Users\leecs1\Downloads\es4p.db'


decompress = bz2.decompress
XML = etree.XML

with sqlite3.connect(log_database) as conn:
    cursor = conn.cursor()

    # Max: 893440
    rowcount = 50000
    cursor.execute(f'SELECT * FROM logs LIMIT {rowcount}')

    for i in tqdm(range(rowcount), ncols=80):
        log = cursor.fetchone()
        if log is None:
            break

        content = decompress(log[2])
        logxml = XML(content, etree.XMLParser(recover=True))

        game_type = logxml.find("GO").attrib["type"]
        if game_type in allowed_types:
            for analyzer in analyzers:
                try:
                    analyzer.ParseLog(logxml, log[0])
                except Exception as error:
                    print(traceback.format_exc())
                    print(f"Error in log {i}: {error}")

    for analyzer in analyzers:
        print("==========")
        analyzer.PrintResults()
