from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd
import csv

# How often do players skip dragon pons?
# Possible reasons - Hand is too slow / cheap. It is the only pair. Going for chiitoitsu. Middle game and sensing danger. Need to go for riichi for a bigger hand. Can pon the second one. Not the dealer.
# self.round[0] 0-3 is East and 4-7 is South.  East = self.oya, South = (self.oya + 1) % 4, West = (self.oya + 2) % 4, North = (self.oya + 3) % 4 

output = "./results/SkippingYakuhai.csv"
categories = ["E34 1 Han", "E34 2 Han", "E34 3 Han", "E34 4 Han", "S12 1 Han", "S12 2 Han", "S12 3 Han", "S12 4 Han", "S3 1 Han", "S3 2 Han", "S3 3 Han", "S3 4 Han"]

class SkippingYakuhai(LogHandAnalyzer):
    def __init__(self):
        super().__init__()

        self.honorsThrown = [None,0,0,0,0,0,0,0]
        self.couldPonFlag = (-1, []) #(player who could call, categories)

        self.yakuhai_df = pd.DataFrame(0,index=range(17),columns=categories)
        self.yakuhaicounts_df = pd.DataFrame(0,index=range(17),columns=categories)

    def RoundStarted(self, init):
        super().RoundStarted(init)
        self.honorsThrown = [None,0,0,0,0,0,0,0]
        self.couldPonFlag = (-1, [])
        if self.round[0] < 2:
            self.end_round = True

    def TileDiscarded(self, who, tile, tsumogiri, element):
        super().TileDiscarded(who, tile, tsumogiri, element)
        turn = len(self.discards[(self.oya-1)%4])
        if turn > 16:
            self.end_round = True
            return
        
        self.couldPonFlag = (-1, [])

        #If honor discarded, check if someone has a pair.
        if tile > 30:
            self.honorsThrown[tile%10] += 1
            if self.honorsThrown[tile%10] <= 2:
                for i in range(4):
                    if i == who: pass

                    if self.scores[i] != min(self.scores): break # Check if player is first

                    if self.hands[i][tile] == 2:
                        yaku = isYakuhai(tile, i, self.round[0], self.oya)
                        if yaku >= 1:
                            self.couldPonFlag = (i, [])
                            dora = self.hands[i][self.dora[0]] + self.aka.count(i)

                            min_han = dora + yaku
                            if min_han > 4: min_han = 4

                            if self.round[0] < 4:
                                cat = f"E34 {min_han} Han"
                            elif self.round[0] < 6:
                                cat = f"S12 {min_han} Han"
                            elif self.round[0] == 6:
                                cat = f"S3 {min_han} Han"
                            else:
                                break

                            self.yakuhaicounts_df.loc[len(self.discards[(self.oya-1)%4]), cat] += 1
                            self.couldPonFlag[1].append(cat)

                            break

                            
    def TileCalled(self, who, tiles, element):
        if self.couldPonFlag[0] != -1:
            for category in self.couldPonFlag[1]:
                self.yakuhai_df.loc[len(self.discards[(self.oya-1)%4]), category] += 1
            self.couldPonFlag = (-1, [])
        super().TileCalled(who, tiles, element)

    def RiichiCalled(self, who, step, element):
        self.end_round = True

    def PrintResults(self):
        print(self.yakuhaicounts_df)
        print(self.yakuhai_df)
        self.yakuhaicounts_df.to_csv(output, mode='w', index_label='Could pon')
        self.yakuhai_df.to_csv(output, mode='a', index_label='Did pon')
        

def isYakuhai(tile, who, round, oya):
    if tile >= 35:
        return 1
    yaku = 0

    if round <= 3 and tile == 31:
        yaku += 1
    if round >= 4 and tile == 32:
        yaku += 1

    if tile - ((who-oya)%4) == 31:
        yaku += 1
    return yaku
