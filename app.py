import bz2
import sqlite3
from lxml import etree
from tqdm import tqdm
from collections import Counter
import util.analysis_utils as u
import util.shanten as s

# Change this
from analyzers.mentanpin import Mentanpin
analyzer = Mentanpin()

allowed_types = ["169", "225", "185"] # Not sure what these are but I will leave it
log_database = r'C:\Users\leecs1\Downloads\es4p.db'
decompress = bz2.decompress
XML = etree.XML

with sqlite3.connect(log_database) as conn:
    cursor = conn.cursor()
    rowcount = 50000
    cursor.execute(f'SELECT * FROM logs LIMIT {rowcount}')

    for i in tqdm(range(rowcount)):
        log = cursor.fetchone()
        if log is None:
            break

        content = decompress(log[2])
        logxml = XML(content, etree.XMLParser(recover=True))

        game_type = logxml.find("GO").attrib["type"]
        if game_type in allowed_types:
            try:
                analyzer.ParseLog(logxml, log[0])
            except:
                print(f"Error in log {i}")
                print(f"Hands: {analyzer.hands}")
                print(f"Calls: {analyzer.calls}")

    analyzer.PrintResults()