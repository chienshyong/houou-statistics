from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd

# For closed hands, find your winning chances open or closed at this turn given no one has riichi, to better inform the decision of making the first call.

# First get the hand eventual winner, and whether they were closed or open.
# Measure the shanten and width of closed hands at turns 4, 6, 8, 10, 12, given that there is no one else riichi. Add to count and give the winner a +1

output = "./results/ShantenWidthWinrate.csv"

class ShantenWidthWinrate(LogHandAnalyzer):
    def __init__(self):
        super().__init__()

        #Count wins
        self.nocall_closedwin_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12])) # No one has called, won closed
        self.nocall_openwin_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12]))
        self.onecall_closedwin_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12]))
        self.onecall_openwin_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12]))
        self.twocall_closedwin_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12]))
        self.twocall_openwin_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12])) # 2 players have called, won open

        #Count all
        self.nocall_count_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12])) # No one has called, won closed
        self.onecall_count_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12]))
        self.twocall_count_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12]))

        self.hand_count = 0
        self.winner = [] # empty means no winner

    def PlayRound(self, round_):
        self.hand_count += 1
        self.winner = []
        # Get eventual winner
        for element in round_.itersiblings():
            if element.tag == "AGARI":
                self.winner.append(int(element.attrib["who"]))
            elif element.tag == "RYUUKYOKU" or element.tag == "INIT":
                break
        super().PlayRound(round_)
    
def initDF(df):
    df = df._append({"Shanten" : 4, "Width" : 0}, ignore_index=True) # Any shanten >= 4
    df = df._append({"Shanten" : 3.0, "Width" : 0}, ignore_index=True)
    df = df._append({"Shanten" : 3.32, "Width" : 0}, ignore_index=True) # Width 32 and up
    df = df._append({"Shanten" : 3.52, "Width" : 0}, ignore_index=True)
    df = df._append({"Shanten" : 2.0, "Width" : 0}, ignore_index=True)
    df = df._append({"Shanten" : 2.24, "Width" : 0}, ignore_index=True)
    df = df._append({"Shanten" : 2.40, "Width" : 0}, ignore_index=True)
    df = df._append({"Shanten" : 1.0, "Width" : 0}, ignore_index=True)
    df = df._append({"Shanten" : 1.16, "Width" : 0}, ignore_index=True)
    df = df._append({"Shanten" : 1.24, "Width" : 0}, ignore_index=True)
    df = df._append({"Shanten" : 0, "Width" : 0}, ignore_index=True)
    return df