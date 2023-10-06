from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd
import csv

# Given X tile was discarded, what is the probability for Y tile to come out after?
# Just count the first 2 rows of discards, past that people are folding/already tenpai so not so interesting. Do not count discards after anyone has riichi.
# This analysis will help for call efficiency judgement, and also to detect problems with my sotogawa analysis. If discarding 5 makes discarding 6 of that suit more likely,
# then 9 is even more dangerous than my sotogawa analysis suggests.

output = "./results/DiscardCorrelation.csv"

class DiscardCorrelation(LogHandAnalyzer):
    def __init__(self):
        super().__init__()
        self.correlation_df = pd.DataFrame(0,index=[1,2,3,4,5,6,7,8,9],columns=[1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,19,"count"]) #Let 11-19 rep. 1 to 9 in other suits

    def TileDiscarded(self, who, tile, tsumogiri, element):
        super().TileDiscarded(who, tile, tsumogiri, element)
        if len(self.discards[(self.oya-1)%4]) == 13:    #Turn 13
            self.AnalyseDiscards()

    def RiichiCalled(self, who, step, element):
        self.AnalyseDiscards()
       
    def AnalyseDiscards(self):
        self.end_round = True
        for player in range(4):
            for i in range(len(self.discards[player])-1):
                d = self.discards[player][i]
                if d > 30: continue
                for j in range(i+1, len(self.discards[player])):
                    dd = self.discards[player][j]
                    if dd > 30: continue
                    if dd // 10 == d // 10:
                        discard_class = dd % 10
                    else:
                        discard_class = dd % 10 + 10
                    self.correlation_df.loc[d%10, discard_class] += 1
                self.correlation_df.loc[d%10, "count"] += 1

    def PrintResults(self):
        print(self.correlation_df)
        self.correlation_df.to_csv(output, mode='w', index_label='Discard Correlation')