from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd

# Gathers the distribution of waits for open and riichi hands for sanmenchan, ryanmen, penchan, kanchan, tanki and shanpon waits.
# Expand to include honor once and twice cut.
# If waiting on single wait: if wait is present, classify as tanki. Else, kanchan except for 3, if 1 is present just classify as penchan (will miss 1124).
# Complex waits are ignored.

output = "./results/WaitDistribution.csv"

class WaitDistribution(LogHandAnalyzer):
    def __init__(self):
        super().__init__()

        self.riichi_counts = 0      
        self.open_counts = 0  
        self.complex_waits = 0
        self.complex_waits_open = 0
        self.riichiwait_df = pd.DataFrame(0,columns=["sanmenchan", "ryanmen", "penchan", "kanchan", "tanki"],index=[1,2,3,4,5,6,7,8,9,"honor", "honor 1", "honor 2"])
        self.riichishanpon_df = pd.DataFrame(0,columns=[1,2,3,4,5,6,7,8,9,"honor"],index=[1,2,3,4,5,6,7,8,9,"honor"])
        self.openwait_df = pd.DataFrame(0,columns=["sanmenchan", "ryanmen", "penchan", "kanchan", "tanki"],index=[1,2,3,4,5,6,7,8,9,"honor", "honor 1", "honor 2"])
        self.openshanpon_df = pd.DataFrame(0,columns=[1,2,3,4,5,6,7,8,9,"honor"],index=[1,2,3,4,5,6,7,8,9,"honor"])
        self.recorded = [False,False,False,False]

    def RoundStarted(self, init):
        self.recorded = [False,False,False,False]
        return super().RoundStarted(init)

    def RiichiCalled(self, who, step, element):
        if step != 2: return
        uke, wait = sh.calculateUkeire(self.hands[who])
        self.record(uke, wait, self.hands[who])
        self.recorded[who] = True

    def TileDiscarded(self, who, tile, tsumogiri, element):
        super().TileDiscarded(who, tile, tsumogiri, element)

        # If have called and tedashi, check if tenpai
        if len(self.calls[who]) > 0 and not tsumogiri and not self.recorded[who]:
            if sh.isTenpai(self.hands[who]):
                uke, wait = sh.calculateUkeire(self.hands[who], baseShanten = 0)
                self.record_open(uke,wait,self.hands[who])
                self.recorded[who] = True
        
    def PrintResults(self):
        # print(self.riichiwait_df)
        # print(self.riichishanpon_df)
        # print(self.openwait_df)
        # print(self.openshanpon_df)
        # print("Total riichis: " + str(self.riichi_counts))
        # print("Total opens: " + str(self.open_counts))
        self.riichiwait_df.to_csv(output, mode='a')
        self.riichishanpon_df.to_csv(output, mode='a')
        self.openwait_df.to_csv(output, mode='a')
        self.openshanpon_df.to_csv(output, mode='a')
        with open(output, "a", encoding="utf8") as f:
            f.write(f"Total riichi,{str(self.riichi_counts)}")
            f.write("\n")
            f.write(f"Complex waits,{str(self.complex_waits)}")
            f.write("\n")
            f.write(f"Total open,{str(self.open_counts)}")
            f.write("\n")
            f.write(f"Complex waits open,{str(self.complex_waits_open)}")
    
    def record(self, uke, wait, hand):
        self.riichi_counts += 1
        if len(wait) == 3:
            if all(i//10 == wait[0]//10 for i in wait) and wait[0] + 3 == wait[1] and wait[1] + 3 == wait[2]:
                    self.riichiwait_df.loc[wait[0]%10,"sanmenchan"] += 1
                    return
        if len(wait) >= 3:
            self.complex_waits += 1
            return
        if len(wait) == 1:
            if wait[0] < 30:
                if hand[wait[0]]>0 and hand[wait[0]-1] + hand[wait[0]+1] < 3: #Cases where you have the tile and waiting on it, but it's kanchan eg 22344, 12234
                    self.riichiwait_df.loc[wait[0]%10,"tanki"] += 1
                    # print("tanki" + ut.parseAmberNotation(hand))
                elif (wait[0]%10 == 3 and hand[wait[0]-2]>0) or (wait[0]%10 == 7 and hand[wait[0]+2]>0):
                    self.riichiwait_df.loc[wait[0]%10,"penchan"] += 1
                    # print("penchan" + ut.parseAmberNotation(hand))
                else:
                    self.riichiwait_df.loc[wait[0]%10,"kanchan"] += 1
                    # print("kanchan" + ut.parseAmberNotation(hand))
            else:
                honor_out = 0
                for discards in self.discards:
                    honor_out += discards.count(wait[0])
                if honor_out == 0:
                    h = "honor"
                if honor_out == 1:
                    h = "honor 1"
                if honor_out >= 2:
                    h = "honor 2"
                self.riichiwait_df.loc[h,"tanki"] += 1

        if len(wait) == 2:
            if all(i//10 == wait[0]//10 for i in wait) and wait[0] + 3 == wait[1] and uke >= 5:
                self.riichiwait_df.loc[wait[0]%10,"ryanmen"] += 1
            else:
                w0 = "honor" if wait[0] > 30 else wait[0]%10
                w1 = "honor" if wait[1] > 30 else wait[1]%10
                if w0 != "honor" and w1 != "honor":
                    if w0 > w1:
                        w0, w1 = w1, w0
                self.riichishanpon_df.loc[w0,w1] += 1

    def record_open(self, uke, wait, hand):
        self.open_counts += 1
        if len(wait) == 3:
            if all(i//10 == wait[0]//10 for i in wait) and wait[0] + 3 == wait[1] and wait[1] + 3 == wait[2]:
                    self.openwait_df.loc[wait[0]%10,"sanmenchan"] += 1
                    return
        if len(wait) >= 3:
            self.complex_waits_open += 1
            return
        if len(wait) == 1:
            if wait[0] < 30:
                if hand[wait[0]]>0 and hand[wait[0]-1]+hand[wait[0]+1] < 3: #Cases where you have the tile and waiting on it, but it's kanchan eg 22344, 12234
                    # # print("tanki" + ut.parseAmberNotation(hand))
                    self.openwait_df.loc[wait[0]%10,"tanki"] += 1
                elif (wait[0]%10 == 3 and hand[wait[0]-2]>0) or (wait[0]%10 == 7 and hand[wait[0]+2]>0):
                    self.openwait_df.loc[wait[0]%10,"penchan"] += 1
                    # print("penchan" + ut.parseAmberNotation(hand))
                else:
                    self.openwait_df.loc[wait[0]%10,"kanchan"] += 1
                    # print("kanchan" + ut.parseAmberNotation(hand))
            else:
                honor_out = 0
                for discards in self.discards:
                    honor_out += discards.count(wait[0])
                if honor_out == 0:
                    h = "honor"
                if honor_out == 1:
                    h = "honor 1"
                if honor_out >= 2:
                    h = "honor 2"
                self.openwait_df.loc[h,"tanki"] += 1
        if len(wait) == 2:
            if all(i//10 == wait[0]//10 for i in wait) and wait[0] + 3 == wait[1] and uke >= 5:
                self.openwait_df.loc[wait[0]%10,"ryanmen"] += 1
            else:
                w0 = "honor" if wait[0] > 30 else wait[0]%10
                w1 = "honor" if wait[1] > 30 else wait[1]%10
                if w0 != "honor" and w1 != "honor":
                    if w0 > w1:
                        w0, w1 = w1, w0
                self.openshanpon_df.loc[w0,w1] += 1
