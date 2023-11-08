from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
from util.analysis_utils import convertHai, convertTile, convertTileCheckAka, discards, draws, GetNextRealTag, GetStartingHands, getTilesFromCall, GetDora
import pandas as pd
import numpy as np
import statistics

# Finding the chance of getting last given position in all last (look at 3rd and 4th place only)

output = "./results/AllLast.csv"

class AllLast(LogHandAnalyzer):
    def __init__(self):
        super().__init__()
        self.final_pos = [-1,-1,-1,-1]

        self.ND3rd = pd.DataFrame(0,index=range(13), columns=range(1,5)) # Score gap in 1000s, final position
        self.NDvD3rd = pd.DataFrame(0,index=range(13), columns=range(1,5)) # Dealer is last
        self.ND4th = pd.DataFrame(0,index=range(13), columns=range(1,5))
        self.NDvD4th = pd.DataFrame(0,index=range(13), columns=range(1,5))
        self.D3rd = pd.DataFrame(0,index=range(13), columns=range(1,5))
        self.D4th = pd.DataFrame(0,index=range(13), columns=range(1,5))

    def ParseLog(self, log, log_id):
        self.final_pos = [-1,-1,-1,-1]
        for round_ in log.iter("AGARI"):
            if "owari" in round_.attrib:
                s = round_.attrib["owari"].split(',')
                final_scores = [int(s[0]),int(s[2]),int(s[4]),int(s[6])]
        for round_ in log.iter("RYUUKYOKU"):
            if "owari" in round_.attrib:
                s = round_.attrib["owari"].split(',')
                final_scores = [int(s[0]),int(s[2]),int(s[4]),int(s[6])]
        sorted_scores = final_scores.copy()
        sorted_scores.sort()
        for i in range(4):
            self.final_pos[i] = 4 - sorted_scores.index(final_scores[i])
        return super().ParseLog(log, log_id)
    
    def PlayRound(self, round_):
        self.RoundStarted(round_)
        if self.round[0] != 7: return

        current_positions = [-1,-1,-1,-1]
        sorted_scores = self.scores.copy()
        sorted_scores.sort()
        for i in range(4):
            current_positions[i] = 4 - sorted_scores.index(self.scores[i])

        gap_3rd_4th = sorted_scores[1] - sorted_scores[0]
        gap_1000s = gap_3rd_4th // 10
        if gap_1000s > 12: gap_1000s = 12

        try:
            third = current_positions.index(3)
            fourth = current_positions.index(4)
        except:
            return
        
        if third == self.oya:
            self.D3rd.loc[gap_1000s, self.final_pos[third]] += 1
        else:
            if fourth == self.oya:
                self.NDvD3rd.loc[gap_1000s, self.final_pos[third]] += 1
            else:
                self.ND3rd.loc[gap_1000s, self.final_pos[third]] += 1
        if fourth == self.oya:
            self.D4th.loc[gap_1000s, self.final_pos[fourth]] += 1
        else:
            if third == self.oya:
                self.NDvD4th.loc[gap_1000s, self.final_pos[fourth]] += 1
            else:
                self.ND4th.loc[gap_1000s, self.final_pos[fourth]] += 1

    def PrintResults(self):
        self.D3rd.to_csv(output, mode='w', index_label='D3')
        self.ND3rd.to_csv(output, mode='a', index_label='ND3')
        self.NDvD3rd.to_csv(output, mode='a', index_label='ND3vD')
        self.D4th.to_csv(output, mode='a', index_label='D4')
        self.ND4th.to_csv(output, mode='a', index_label='ND4')
        self.NDvD4th.to_csv(output, mode='a', index_label='ND4vD')