import bz2
import sqlite3
from lxml import etree
from tqdm import tqdm
import traceback

# Change this to the analyzer being used
from analyzers.dama_winrate_by_turn import DamaWinrateByTurn
analyzer = DamaWinrateByTurn()

allowed_types = ["169", "225", "185"]
# log_database = r'C:\Users\leecs1\Downloads\es4p.db'
log_database = 'data\es4p.db'
decompress = bz2.decompress
XML = etree.XML

with sqlite3.connect(log_database) as conn:
    cursor = conn.cursor()

    rowcount = 50000  # Max: 893440
    cursor.execute(f'SELECT * FROM logs LIMIT {rowcount}')
    # cursor.fetchmany(1)

    for i in tqdm(range(rowcount), ncols=120, disable=False):
        log = cursor.fetchone()
        if log is None: break
        content = decompress(log[2])
        logxml = XML(content, etree.XMLParser(recover=True))

        # with open('data/examplelog.xml', 'wb') as f:
        #     str = etree.tostring(logxml, pretty_print=True)
        #     f.write(str)

        game_type = logxml.find("GO").attrib["type"]
        if game_type in allowed_types:
            try:
                analyzer.ParseLog(logxml, log[0])
            except Exception as error:
                print(traceback.format_exc())
                print(f"Error in log {i}: {error}")

    analyzer.PrintResults()