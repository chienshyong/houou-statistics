from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd

# Find your winning chances open or closed at this turn given no one has riichi.
# At turns 4, 6, 8, 10, 12, measure the shanten and width of every hand. Width round down to nearest 4.
# Group together and ignore if there is any riichi.
# 4 tables of no call, 1 call, 2 call.

output = "./results/ShantenWidth.csv"
turns_considered = [4,6,8,10,12]

class ShantenWidth(LogHandAnalyzer):
    def __init__(self):
        super().__init__()

        self.nocall_df = initDF(pd.DataFrame(columns=["Shanten","Width",4,6,8,10,12]))
        self.onecall_df = initDF(pd.DataFrame(columns=["Shanten","Width",4,6,8,10,12]))
        self.twocall_df = initDF(pd.DataFrame(columns=["Shanten","Width",4,6,8,10,12])) #Include 3 calls too

        self.any_riichi = False
        self.any_riichi_counts = Counter({4:0,6:0,8:0,10:0,12:0})
        self.hand_count = 0

    def RoundStarted(self, init):
        self.any_riichi = False
        self.hand_count += 1
        return super().RoundStarted(init)

    def TileDiscarded(self, who, tile, tsumogiri, element):
        super().TileDiscarded(who, tile, tsumogiri, element)
        turn = len(self.discards[(self.oya-1)%4]) #Let everyone have their nth discard
        if who == 0 and turn in turns_considered:
            if self.any_riichi:
                self.any_riichi_counts[turn] += 1
                return
            for i in range(4):
                shanten = sh.calculateMinimumShanten(self.hands[i])
                uke, wait = sh.calculateUkeire(self.hands[i],self.calls[i],shanten)
                width = group_width(shanten, uke)
                
                num_calls = len(self.calls[i])
                if num_calls == 0:
                    self.nocall_df.loc[(self.nocall_df["Shanten"] == shanten) & (self.nocall_df["Width"] == width),turn] += 1
                if num_calls == 1:
                    self.onecall_df.loc[(self.nocall_df["Shanten"] == shanten) & (self.nocall_df["Width"] == width),turn] += 1
                if num_calls >= 2:
                    self.twocall_df.loc[(self.nocall_df["Shanten"] == shanten) & (self.nocall_df["Width"] == width),turn] += 1
                
            if turn == turns_considered[-1]:
                self.end_round = True
    
    def RiichiCalled(self, who, step, element):
        self.any_riichi = True
        return super().RiichiCalled(who, step, element)
    
    def PrintResults(self):
        self.nocall_df.to_csv(output, mode='w', index_label='No call')
        self.onecall_df.to_csv(output, mode='a', index_label='1 call')
        self.twocall_df.to_csv(output, mode='a', index_label='2 or 3 call')
    
        with open(output, "a", encoding="utf8") as f:
            f.write(f",,Any Riichi counts,{self.any_riichi_counts[4]},{self.any_riichi_counts[6]},{self.any_riichi_counts[8]},{self.any_riichi_counts[10]},{self.any_riichi_counts[12]}")
            f.write(f"\n,,Hands,{self.hand_count}")

def initDF(df):
    df = df._append({"Shanten" : 6, "Width" : 0}, ignore_index=True)
    df = df._append({"Shanten" : 5, "Width" : 0}, ignore_index=True)
    df = df._append({"Shanten" : 4, "Width" : 0}, ignore_index=True)
    for i in range(80, 3, -4):
        df = df._append({"Shanten" : 3, "Width" : i}, ignore_index=True)
    for i in range(60, 3, -4):
        df = df._append({"Shanten" : 2, "Width" : i}, ignore_index=True)
    for i in range(40, 3, -4):
        df = df._append({"Shanten" : 1, "Width" : i}, ignore_index=True)
    df = df._append({"Shanten" : 0, "Width" : 0}, ignore_index=True)
    df = df.fillna(0)
    return df

def group_width(shanten, uke):
    uke = uke - uke % 4
    if shanten == 0 or shanten >= 4:
        return 0
    if shanten == 3:
        if uke > 80: uke = 80
        if uke < 4: uke = 4
    if shanten == 2:
        if uke > 60: uke = 60
        if uke < 4: uke = 4
    if shanten == 1:
        if uke > 40: uke = 40
        if uke < 4: uke = 4
    return uke