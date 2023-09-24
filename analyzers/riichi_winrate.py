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

        #Total count of riichis
        self.sample = 0

        # counts_df[type, turn]
        self.counts_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"],index=range(1,19))
        self.oikakecounts_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"],index=range(1,19)) # Second riichi
        self.oioikakecounts_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"],index=range(1,19)) # Third riichi

        # wins_df[type, turn]
        self.wins_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"],index=range(1,19))
        self.oikakewins_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"],index=range(1,19)) # Second riichi
        self.oioikakewins_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"],index=range(1,19)) # Third riichi
        
        # draws_df[type, turn]
        self.draws_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"],index=range(1,19))
        self.oikakedraws_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"],index=range(1,19)) # Second riichi
        self.oioikakedraws_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"],index=range(1,19)) # Third riichi

        # dealin_df[type,turn]
        self.dealins_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"],index=range(1,19))
        self.oikakedealins_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"],index=range(1,19)) # Second riichi
        self.oioikakedealins_df = pd.DataFrame(0,columns=["sanmenchan+", "ryanmen", "single", "honor"],index=range(1,19)) # Third riichi

        # [status, riichinum, waittype, turn], status = ["Nil", "Riichi", "Win", "Draw", "Dealin"]. Append to df at the end of each hand.
        self.handstatus = [[0, 0, 0, 0],[0, 0, 0, 0],[0, 0, 0, 0],[0, 0, 0, 0]]
        self.num_of_riichi = 0

    def RoundStarted(self, init):
        self.handstatus = [[0, 0, 0, 0],[0, 0, 0, 0],[0, 0, 0, 0],[0, 0, 0, 0]]
        self.num_of_riichi = 0
        return super().RoundStarted(init)

    def RiichiCalled(self, who, step, element):
        if step != 2: return
        uke, wait = sh.calculateUkeire(self.hands[who], calls=self.calls[who], baseShanten=0)
        if not all(x < 30 for x in wait):
            waittype = "honor"
        elif uke <= 4:
            waittype = "single"
        elif uke <= 8:
            waittype = "ryanmen"
        else:
            waittype = "sanmenchan+"

        turn = len(self.discards[0])
        if turn < 1: turn = 1
        if turn > 18: turn = 18

        self.num_of_riichi += 1
        self.handstatus[who] = [1, self.num_of_riichi, waittype, turn]
        self.sample += 1

    def Win(self, element):
        who = int(element.attrib["who"])
        fromWho = int(element.attrib["fromWho"])
        if self.handstatus[who][0] == 1:
            self.handstatus[who][0] = 2
        if self.handstatus[fromWho][0] == 1:
            self.handstatus[fromWho][0] = 4

    def ExhaustiveDraw(self, element):
        for who in range(4):
            if self.handstatus[who][0] == 1:
                self.handstatus[who][0] = 3

    def RoundEnded(self, init):
        # print(self.handstatus)
        for who in range(4):
            status = self.handstatus[who][0]
            if status != 0:
                if self.handstatus[who][1] == 1: #First riichi
                    waittype = self.handstatus[who][2]
                    turn = self.handstatus[who][3]
                    self.counts_df.loc[turn, waittype] += 1
                    if status == 2:
                        self.wins_df.loc[turn, waittype] += 1
                    if status == 3:
                        self.draws_df.loc[turn, waittype] += 1
                    if status == 4:
                        self.dealins_df.loc[turn, waittype] += 1

                if self.handstatus[who][1] == 2:
                    waittype = self.handstatus[who][2]
                    turn = self.handstatus[who][3]
                    self.oikakecounts_df.loc[turn, waittype] += 1
                    if status == 2:
                        self.oikakewins_df.loc[turn, waittype] += 1
                    if status == 3:
                        self.oikakedraws_df.loc[turn, waittype] += 1
                    if status == 4:
                        self.oikakedealins_df.loc[turn, waittype] += 1

                if self.handstatus[who][1] == 3:
                    waittype = self.handstatus[who][2]
                    turn = self.handstatus[who][3]
                    self.oioikakecounts_df.loc[turn, waittype] += 1
                    if status == 2:
                        self.oioikakewins_df.loc[turn, waittype] += 1
                    if status == 3:
                        self.oioikakedraws_df.loc[turn, waittype] += 1
                    if status == 4:
                        self.oioikakedealins_df.loc[turn, waittype] += 1
    
    def PrintResults(self):
        self.counts_df.to_csv(output, mode='w', index_label='Riichi counts')
        self.wins_df.to_csv(output, mode='a', index_label='Win')
        self.draws_df.to_csv(output, mode='a', index_label='Draw')
        self.dealins_df.to_csv(output, mode='a', index_label='Dealin')

        self.oikakecounts_df.to_csv(output, mode='a', index_label='Oikake Riichi counts')
        self.oikakewins_df.to_csv(output, mode='a', index_label='Win')
        self.oikakedraws_df.to_csv(output, mode='a', index_label='Draw')
        self.oikakedealins_df.to_csv(output, mode='a', index_label='Dealin')

        self.oioikakecounts_df.to_csv(output, mode='a', index_label='Oioikake Riichi counts')
        self.oioikakewins_df.to_csv(output, mode='a', index_label='Win')
        self.oioikakedraws_df.to_csv(output, mode='a', index_label='Draw')
        self.oioikakedealins_df.to_csv(output, mode='a', index_label='Dealin')

        with open(output, "a", encoding="utf8") as f:
            f.write(f"Total riichi,{str(self.sample)}")
