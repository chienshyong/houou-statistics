from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd

# Riichi winrate, drawrate and dealin rate by wait width and turn. Lateral movement rate is implied.
# Does not count visible tiles, only intinsic width.
# If any honor in wait classify as honor wait.
# Else anything >8 tiles classify as sanmenchan+, Anything 4-8 tiles classify as ryanmen, Anything <4 tiles classify as single
# Split data for oikake riichi.
# For chasing riichi, does NOT include deal ins on the riichi tile. Safety of the tile to push is a big factor & out of scope of this analysis.

output = "./results/RiichiWinrate.csv"

class RiichiWinrate(LogHandAnalyzer):
    def __init__(self):
        super().__init__()

        # counts_df[type, turn]
        self.counts_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"])
        self.oikakecounts_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"]) # Second riichi
        self.oioikakecounts_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"]) # Third riichi

        # wins_df[type, turn]
        self.wins_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"])
        self.oikakewins_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"]) # Second riichi
        self.oioikakewins_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"]) # Third riichi
        
        # draws_df[type, turn]
        self.draws_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"])
        self.oikakedraws_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"]) # Second riichi
        self.oioikakedraws_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"]) # Third riichi

        # dealin_df[type,turn]
        self.dealins_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"])
        self.oikakedealins_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"]) # Second riichi
        self.oioikakedealins_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"]) # Third riichi

        # [status, width], status = ["Nil", "Riichi", "Win", "Draw", "Dealin"]. Append to df at the end of each hand.
        self.handstatus = [[0, 0],[0, 0],[0, 0],[0, 0]]

    def RoundStarted(self, init):
        self.handstatus = [[0, 0],[0, 0],[0, 0],[0, 0]]
        return super().RoundStarted(init)

    def RiichiCalled(self, who, step, element):
        if step != 2: return
        uke, wait = sh.calculateUkeire(self.hands[who], calls=self.calls[who], baseShanten=0)
        self.handstatus[who] = [1, uke]

    #https://github.com/Euophrys/phoenix-logs/blob/develop/analysis/dealin_by_seat.py