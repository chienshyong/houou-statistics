from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd

# Let's count the tiles in the wall from 1 player's perspective. Based on 3 players' discards, how many are in my hand + the wall.

output = "./results/WallReading.csv"
turns_considered = [4,6,8,10,12,14,16,18]

class WallReading(LogHandAnalyzer):
    def __init__(self):
        super().__init__()
        self.wall = [4] * 38
        self.wallsize = 136
        self.nonoya_discards = [0] * 38

        # X1 discarded X2 times by others on turn X3, how many are in wall + own hand?
        self.not_discarded_df = pd.DataFrame(0, index=turns_considered, columns=[1,2,3,4,5,6,7,8,9,"Dragon","Wind","Wall"]) #Count round wind as a dragon
        self.once_discarded_df = pd.DataFrame(0, index=turns_considered, columns=[1,2,3,4,5,6,7,8,9,"Dragon","Wind"])
        self.twice_discarded_df = pd.DataFrame(0, index=turns_considered, columns=[1,2,3,4,5,6,7,8,9,"Dragon","Wind"])
        self.thrice_discarded_df = pd.DataFrame(0, index=turns_considered, columns=[1,2,3,4,5,6,7,8,9,"Dragon","Wind"])

        self.not_discarded_c_df = pd.DataFrame(0, index=turns_considered, columns=[1,2,3,4,5,6,7,8,9,"Dragon","Wind","Wall"])
        self.once_discarded_c_df = pd.DataFrame(0, index=turns_considered, columns=[1,2,3,4,5,6,7,8,9,"Dragon","Wind"])
        self.twice_discarded_c_df = pd.DataFrame(0, index=turns_considered, columns=[1,2,3,4,5,6,7,8,9,"Dragon","Wind"])
        self.thrice_discarded_c_df = pd.DataFrame(0, index=turns_considered, columns=[1,2,3,4,5,6,7,8,9,"Dragon","Wind"])

        # X1 of souzu discarded X2 times by others on turn X3, how many are in wall + own hand?
        self.souzu_df = pd.DataFrame(0, index=turns_considered, columns=range(24))
        self.souzu_c_df = pd.DataFrame(0, index=turns_considered, columns=range(24))

        # X1 discarded but X2 not discarded, how many X2 in wall?
        self.turn4_oneneighbor = pd.DataFrame(0, index=[1,2,3,4,5,6,7,8,9], columns=[1,2,3,4,5,6,7,8,9]) #One of column discarded, how many of row in wall?
        self.turn8_oneneighbor = pd.DataFrame(0, index=[1,2,3,4,5,6,7,8,9], columns=[1,2,3,4,5,6,7,8,9])
        self.turn4_twoneighbor = pd.DataFrame(0, index=[1,2,3,4,5,6,7,8,9], columns=[1,2,3,4,5,6,7,8,9])
        self.turn8_twoneighbor = pd.DataFrame(0, index=[1,2,3,4,5,6,7,8,9], columns=[1,2,3,4,5,6,7,8,9])

        self.turn4_oneneighbor_c = pd.DataFrame(0, index=[1,2,3,4,5,6,7,8,9], columns=[1,2,3,4,5,6,7,8,9])
        self.turn8_oneneighbor_c = pd.DataFrame(0, index=[1,2,3,4,5,6,7,8,9], columns=[1,2,3,4,5,6,7,8,9])
        self.turn4_twoneighbor_c = pd.DataFrame(0, index=[1,2,3,4,5,6,7,8,9], columns=[1,2,3,4,5,6,7,8,9])
        self.turn8_twoneighbor_c = pd.DataFrame(0, index=[1,2,3,4,5,6,7,8,9], columns=[1,2,3,4,5,6,7,8,9])

    def RoundStarted(self, init):
        super().RoundStarted(init)
        self.wall = [4] * 38
        self.wallsize = 136
        self.nonoya_discards = [0] * 38

        for idx, hands in enumerate(self.hands):
            if idx == self.oya: continue
            for h in hands:
                self.wall[h] -= hands[h]
                self.wallsize -= hands[h]

        dora = self.dora[0]
        if dora < 30 and dora % 10 == 1:
            dora_indicator = dora + 8
        elif dora == 31:
            dora_indicator = 34
        elif dora == 35:
            dora_indicator = 37
        else:
            dora_indicator = dora - 1
        self.wall[dora_indicator] -= 1
        self.wallsize -= 1

    def DoraRevealed(self, hai, element):
        super().DoraRevealed(hai, element)
        dora = self.dora[-1]
        if dora < 30 and dora % 10 == 1:
            dora_indicator = dora + 8
        elif dora == 31:
            dora_indicator = 34
        elif dora == 35:
            dora_indicator = 37
        else:
            dora_indicator = dora - 1
        self.wall[dora_indicator] -= 1
        self.wallsize -= 1

    def TileDrawn(self, who, tile, element):
        super().TileDrawn(who, tile, element)
        if not who == self.oya:
            self.wall[tile] -= 1
            self.wallsize -= 1

    def TileDiscarded(self, who, tile, tsumogiri, element):
        super().TileDiscarded(who, tile, tsumogiri, element)

        if not who == self.oya:
            self.nonoya_discards[tile] += 1

        if self.turn in turns_considered and who == self.oya:
            for i in range(38):
                if i % 10 == 0: continue
                if i < 30:
                    cat = i % 10
                elif i >= 35 or i % 10 == self.round[0] // 4 + 1:
                    cat = "Dragon"
                else:
                    cat = "Wind"

                if self.nonoya_discards[i] == 0:
                    self.not_discarded_df.loc[self.turn, cat] += self.wall[i]
                    self.not_discarded_c_df.loc[self.turn, cat] += 1
                    self.not_discarded_df.loc[self.turn, "Wall"] += self.wallsize
                    self.not_discarded_c_df.loc[self.turn, "Wall"] += 1
                elif self.nonoya_discards[i] == 1:
                    self.once_discarded_df.loc[self.turn, cat] += self.wall[i]
                    self.once_discarded_c_df.loc[self.turn, cat] += 1
                elif self.nonoya_discards[i] == 2:
                    self.twice_discarded_df.loc[self.turn, cat] += self.wall[i]
                    self.twice_discarded_c_df.loc[self.turn, cat] += 1
                elif self.nonoya_discards[i] == 3:
                    self.thrice_discarded_df.loc[self.turn, cat] += self.wall[i]
                    self.thrice_discarded_c_df.loc[self.turn, cat] += 1

            discards_souzu_count = 0
            wall_souzu_count = 0
            for i in range(1,10):
                discards_souzu_count += self.nonoya_discards[i]
                wall_souzu_count += self.wall[i]

            if discards_souzu_count > 23: discards_souzu_count = 23
            if wall_souzu_count > 23: wall_souzu_count = 23

            self.souzu_df.loc[self.turn,discards_souzu_count] += wall_souzu_count
            self.souzu_c_df.loc[self.turn,discards_souzu_count] += 1

        if (self.turn == 4 or self.turn == 8) and who == self.oya:
            for i in range(30):
                if i % 10 == 0: continue
                if self.nonoya_discards[i] == 1:
                    for j in range((i//10)*10+1,(i//10)*10+10):
                        if self.nonoya_discards[j] == 0:
                            if self.turn == 4:
                                self.turn4_oneneighbor.loc[j%10,i%10] += self.wall[j]
                                self.turn4_oneneighbor_c.loc[j%10,i%10] += 1
                            if self.turn == 8:
                                self.turn8_oneneighbor.loc[j%10,i%10] += self.wall[j]
                                self.turn8_oneneighbor_c.loc[j%10,i%10] += 1
                elif self.nonoya_discards[i] == 2:
                    for j in range((i//10)*10+1,(i//10)*10+10):
                        if self.nonoya_discards[j] == 0:
                            if self.turn == 4:
                                self.turn4_twoneighbor.loc[j%10,i%10] += self.wall[j]
                                self.turn4_twoneighbor_c.loc[j%10,i%10] += 1
                            if self.turn == 8:
                                self.turn8_twoneighbor.loc[j%10,i%10] += self.wall[j]
                                self.turn8_twoneighbor_c.loc[j%10,i%10] += 1
            
    def PrintResults(self):
        not_d = self.not_discarded_df / self.not_discarded_c_df
        one_d = self.once_discarded_df / self.once_discarded_c_df
        two_d = self.twice_discarded_df / self.twice_discarded_c_df
        three_d = self.thrice_discarded_df / self.thrice_discarded_c_df
        not_d.to_csv(output, mode='w')
        one_d.to_csv(output, mode='a')
        two_d.to_csv(output, mode='a')
        three_d.to_csv(output, mode='a')

        souzu = self.souzu_df/self.souzu_c_df
        souzu.to_csv(output, mode='a')
        self.souzu_c_df.to_csv(output, mode='a')

        t4_1 = self.turn4_oneneighbor/self.turn4_oneneighbor_c
        t8_1 = self.turn8_oneneighbor/self.turn8_oneneighbor_c
        t4_2 = self.turn4_twoneighbor/self.turn4_twoneighbor_c
        t8_2 = self.turn8_twoneighbor/self.turn8_twoneighbor_c
        t4_1.to_csv(output, mode='a')
        t8_1.to_csv(output, mode='a')
        t4_2.to_csv(output, mode='a')
        t8_2.to_csv(output, mode='a')
