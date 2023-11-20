from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd
import csv

# Discard Reading to identify 1-shanten chance for menzen hands, to judge if safe tile should be kept.
# Analyse only first 12 turns when no riichi has been called.

# 1/2/3 middle tiles of different colours discarded on turn X1 vs shanten on turn X2
# Riichi forecast from first two tedashi - simple then simple, or honor then terminal etc

output = "./results/SpeedReading.csv"

class SpeedReading(LogHandAnalyzer):
    def __init__(self):
        super().__init__()
        self.tedashi = [[], [], [], []]
        self.prev_shanten = [6,6,6,6]
        self.simple_colours_by = [[],[],[],[]] # [3,6,9] means 1 simple by turn 3, 2 by turn 6, 3 by turn 9
        self.middle_colours_by = [[],[],[],[]]
        self.first_tedashis = [False,False,False,False] #Category of first tedashis
        self.honor_tedashis = [[],[],[],[]]

        self.overall = pd.DataFrame(0, index=range(13), columns=[0,1,2,3,4,"riichi_in_3","count"]) # Avg shanten for closed hands 

        self.one_simple_colour = pd.DataFrame(0, index=range(13), columns=range(13)) # 2 simple colours discarded by turn X2 vs 1 shanten on turn X1
        self.one_middle_colour = pd.DataFrame(0, index=range(13), columns=range(13))
        self.two_simple_colours = pd.DataFrame(0, index=range(13), columns=range(13)) # 2 simple colours discarded by turn X2 vs 1 shanten on turn X1
        self.two_middle_colours = pd.DataFrame(0, index=range(13), columns=range(13)) # 2 middle colours discarded by turn X2 vs 1 shanten on turn X1
        self.three_simple_colours = pd.DataFrame(0, index=range(13), columns=range(13))
        self.three_middle_colours = pd.DataFrame(0, index=range(13), columns=range(13)) # 3 middle colours discarded by turn X2 vs 1 shanten on turn X1
        self.one_simple_colour_c = pd.DataFrame(0, index=range(13), columns=range(13))
        self.one_middle_colour_c = pd.DataFrame(0, index=range(13), columns=range(13))
        self.two_simple_colours_c = pd.DataFrame(0, index=range(13), columns=range(13))
        self.two_middle_colours_c = pd.DataFrame(0, index=range(13), columns=range(13))
        self.three_simple_colours_c = pd.DataFrame(0, index=range(13), columns=range(13))
        self.three_middle_colours_c = pd.DataFrame(0, index=range(13), columns=range(13))

        self.first_tedashi_cats = []
        for i in ["guest,","yakuhai,","terminal,","simple,"]:
            for j in ["guest,","yakuhai,","terminal,","simple,"]:
                self.first_tedashi_cats.append(i+j)
        self.riichi_forecast_t6 = pd.DataFrame(0,index=self.first_tedashi_cats,columns=["dama","1shanten","riichi_in_3","riichi_in_6","open_in_6","count"])
        self.honor_tedashi = pd.DataFrame(0,index=range(13),columns=["dama","1shanten","riichi_in_3","riichi_in_6","count"])

    def RoundStarted(self, init):
        super().RoundStarted(init)
        self.tedashi = [[], [], [], []]
        self.first_tedashis = [False,False,False,False]
        self.honor_tedashis = [[],[],[],[]]
        self.simple_colours_by = [[],[],[],[]]
        self.middle_colours_by = [[],[],[],[]]
        for who in range(4):
            self.prev_shanten[who] = min(sh.calculateMinimumShanten(self.hands[who]), 4)

    def RiichiCalled(self, who, step, element):
        if step == 2:
            self.end_round = True
            t = self.turn
            i = 3
            while t >= 0 and i > 0:
                self.overall.loc[t, "riichi_in_3"] += 1
                t -= 1
                i -= 1

            if self.first_tedashis[who]:
                if self.turn <= 9:
                    self.riichi_forecast_t6.loc[self.first_tedashis[who],"riichi_in_3"] += 1
                if self.turn <= 12:
                    self.riichi_forecast_t6.loc[self.first_tedashis[who],"riichi_in_6"] += 1

            for h in self.honor_tedashis[who]:
                if self.turn < h + 3:
                    self.honor_tedashi.loc[h,"riichi_in_3"] += 1
                if self.turn < h + 6:
                    self.honor_tedashi.loc[h,"riichi_in_6"] += 1

    def TileCalled(self, who, tiles, element):
        super().TileCalled(who, tiles, element)
        if self.turn >= 6:
            if len(self.calls[who]) == 1 and self.first_tedashis[who]: # First call
                self.riichi_forecast_t6.loc[self.first_tedashis[who],"open_in_6"] += 1

    def TileDiscarded(self, who, tile, tsumogiri, element):
        super().TileDiscarded(who, tile, tsumogiri, element)
        self.tedashi[who].append(not tsumogiri)

        if self.turn > 12:
            self.end_round = True
            return
     
        if len(self.calls[who]) == 0:
            if not tsumogiri:
                self.prev_shanten[who] = min(sh.calculateMinimumShanten(self.hands[who]), 4)
            self.overall.loc[self.turn, [self.prev_shanten[who], "count"]] += 1 

            if tile < 30 and tile % 10 >= 2 and tile % 10 <= 8:
                suit_discarded = False
                for check_tile in range(tile - tile%10 + 2, tile - tile%10 + 9):
                    if check_tile in self.discards[who][:-1]:
                        suit_discarded = True
                        break
                if not suit_discarded:
                    self.simple_colours_by[who].append(self.turn)

            if tile < 30 and tile % 10 >= 3 and tile % 10 <= 7:
                suit_discarded = False
                for check_tile in range(tile - tile%10 + 3, tile - tile%10 + 8):
                    if check_tile in self.discards[who][:-1]:
                        suit_discarded = True
                        break
                if not suit_discarded:
                    self.middle_colours_by[who].append(self.turn)

            for simple_colours in range(len(self.simple_colours_by[who])):
                if simple_colours == 0:
                    self.one_simple_colour_c.loc[self.turn, self.simple_colours_by[who][0]] += 1
                    if self.prev_shanten[who] == 1:
                        self.one_simple_colour.loc[self.turn, self.simple_colours_by[who][0]] += 1
                if simple_colours == 1:
                    self.two_simple_colours_c.loc[self.turn, self.simple_colours_by[who][1]] += 1
                    if self.prev_shanten[who] == 1:
                        self.two_simple_colours.loc[self.turn, self.simple_colours_by[who][1]] += 1
                if simple_colours == 2:
                    self.three_simple_colours_c.loc[self.turn, self.simple_colours_by[who][2]] += 1
                    if self.prev_shanten[who] == 1:
                        self.three_simple_colours.loc[self.turn, self.simple_colours_by[who][2]] += 1

            for middle_colours in range(len(self.middle_colours_by[who])):
                if middle_colours == 0:
                    self.one_middle_colour_c.loc[self.turn, self.middle_colours_by[who][0]] += 1
                    if self.prev_shanten[who] == 1:
                        self.one_middle_colour.loc[self.turn, self.middle_colours_by[who][0]] += 1
                if middle_colours == 1:
                    self.two_middle_colours_c.loc[self.turn, self.middle_colours_by[who][1]] += 1
                    if self.prev_shanten[who] == 1:
                        self.two_middle_colours.loc[self.turn, self.middle_colours_by[who][1]] += 1
                if middle_colours == 2:
                    self.three_middle_colours_c.loc[self.turn, self.middle_colours_by[who][2]] += 1
                    if self.prev_shanten[who] == 1:
                        self.three_middle_colours.loc[self.turn, self.middle_colours_by[who][2]] += 1

        if self.turn == 6 and who == self.oya:
            for player in range(4):
                if len(self.calls[player]) > 0: continue

                ted_count = 0
                cat = ""
                for index, discard in enumerate(self.discards[player]):
                    if self.tedashi[player][index]:
                        ted_count += 1
                        if discard < 30 and discard % 10 >= 2 and discard % 10 <= 8:
                            cat += "simple,"
                        if discard < 30 and (discard % 10 == 1 or discard % 10 == 9):
                            cat += "terminal,"
                        if discard > 30:
                            if self.isYakuhai(discard,player) >= 1:
                                cat += "yakuhai,"
                            else:
                                cat += "guest,"
                        if ted_count == 2:
                            break
                if cat in self.first_tedashi_cats:
                    self.first_tedashis[player] = cat
                    self.riichi_forecast_t6.loc[cat,"count"] += 1
                    shanten = sh.calculateMinimumShanten(self.hands[player])
                    if shanten == 1:
                        self.riichi_forecast_t6.loc[cat,"1shanten"] += 1
                    if shanten == 0:
                        self.riichi_forecast_t6.loc[cat,"dama"] += 1

        if tile > 30 and not tsumogiri:
            self.honor_tedashis[who].append(self.turn)
            self.honor_tedashi.loc[self.turn,"count"] += 1
            shanten = sh.calculateMinimumShanten(self.hands[who])
            if shanten == 1:
                self.honor_tedashi.loc[self.turn,"1shanten"] += 1
            if shanten == 0:
                self.honor_tedashi.loc[self.turn,"dama"] += 1

    def PrintResults(self):
        self.overall[[0,1,2,3,4,"riichi_in_3"]] = self.overall[[0,1,2,3,4,"riichi_in_3"]].div(self.overall["count"], axis=0).round(3)
        self.overall.to_csv(output, mode='w', index_label='overall')

        self.one_simple_colour = self.one_simple_colour / self.one_simple_colour_c
        self.two_simple_colours = self.two_simple_colours / self.two_simple_colours_c
        self.three_simple_colours = self.three_simple_colours / self.three_simple_colours_c
        self.one_middle_colour = self.one_middle_colour / self.one_middle_colour_c
        self.two_middle_colours = self.two_middle_colours / self.two_middle_colours_c
        self.three_middle_colours = self.three_middle_colours / self.three_middle_colours_c

        self.one_simple_colour.to_csv(output, mode='a', index_label='1s')
        self.two_simple_colours.to_csv(output, mode='a', index_label='2s')
        self.three_simple_colours.to_csv(output, mode='a', index_label='3s')
        self.one_middle_colour.to_csv(output, mode='a', index_label='1m')
        self.two_middle_colours.to_csv(output, mode='a', index_label='2m')
        self.three_middle_colours.to_csv(output, mode='a', index_label='3m')

        self.riichi_forecast_t6[["dama","1shanten","riichi_in_3","riichi_in_6","open_in_6"]] = self.riichi_forecast_t6[["dama","1shanten","riichi_in_3","riichi_in_6","open_in_6"]].div(self.riichi_forecast_t6["count"], axis=0).round(3)
        self.riichi_forecast_t6.to_csv(output, mode='a', index_label='1st2ted')

        self.honor_tedashi[["dama","1shanten","riichi_in_3","riichi_in_6"]] = self.honor_tedashi[["dama","1shanten","riichi_in_3","riichi_in_6"]].div(self.honor_tedashi["count"], axis=0).round(3)
        self.honor_tedashi.to_csv(output, mode='a', index_label='honorted')

    def isYakuhai(self, tile, who):
        if tile >= 35:
            return 1
        yaku = 0
        if self.round[0] <= 3 and tile == 31:
            yaku += 1
        if self.round[0] >= 4 and tile == 32:
            yaku += 1
        if tile - ((who-self.oya)%4) == 31:
            yaku += 1
        return yaku