import bz2
import sqlite3
from lxml import etree
from tqdm import tqdm
from collections import Counter
import util.analysis_utils as u
import util.shanten as s

from analyzers.mentanpin import Mentanpin

allowed_types = ["169", "225", "185"] #Not sure what these are but I will leave it
log_database = r'C:\Users\leecs1\Downloads\es4p.db'
decompress = bz2.decompress
XML = etree.XML

mentanpin = Mentanpin()

with sqlite3.connect(log_database) as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM logs')
    rowcount = cursor.fetchone()[0]
    cursor.execute('SELECT * FROM logs LIMIT 1')

    for i in range(rowcount):
        log = cursor.fetchone()
        if log is None:
            break

        content = decompress(log[2])
        logxml = XML(content, etree.XMLParser(recover=True))

        game_type = logxml.find("GO").attrib["type"]
        if game_type in allowed_types:
            mentanpin.ParseLog(logxml, log[0])