from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd
import csv

# Discard Reading for properties and waits of open hands.

# Wait around last tedashi/tile discarded after call ✓
# Wait shifting (improving kanchan to ryanmen) or sliding/karagiri? ✓
# Dora pair chance based on dorasoba discard ✓

output = "./results/TedashiReading.csv"

class TedashiReading(LogHandAnalyzer):
    def __init__(self):
        super().__init__()
        self.tedashi = [[], [], [], []]
        self.previous_shape = [(0,0),(0,0),(0,0),(0,0)] #Shanten, Ukeire
        self.just_called = False

        # Each tedashi chance it reduce shanten
        self.closed_tedashi = pd.DataFrame(0, index=range(19), columns=["Reduce Shanten", "Increase Ukeire", "Same Ukeire", "Reduce Ukeire", "Increase Shanten", "Count"])
        self.open_tedashi_1 = pd.DataFrame(0, index=range(19), columns=["Reduce Shanten", "Increase Ukeire", "Same Ukeire", "Reduce Ukeire", "Increase Shanten", "Count"])
        self.open_tedashi_2 = pd.DataFrame(0, index=range(19), columns=["Reduce Shanten", "Increase Ukeire", "Same Ukeire", "Reduce Ukeire", "Increase Shanten", "Count"])
        self.open_tedashi_3 = pd.DataFrame(0, index=range(19), columns=["Reduce Shanten", "Increase Ukeire", "Same Ukeire", "Reduce Ukeire", "Increase Shanten", "Count"])

        # Wait reading from tedashis
        self.tedashi_closed_wait = pd.DataFrame(0, index=range(19), columns=["Noten", "Wait tedashi", "Not tedashi"])
        self.tedashi_1_wait = pd.DataFrame(0, index=range(19), columns=["Noten", "Wait tedashi", "Not tedashi"])
        self.tedashi_2_wait = pd.DataFrame(0, index=range(19), columns=["Noten", "Wait tedashi", "Not tedashi"])
        self.tedashi_3_wait = pd.DataFrame(0, index=range(19), columns=["Noten", "Wait tedashi", "Not tedashi"])

        # Dora pair (ignore # of calls) given dorasoba (+-1) discard
        dsoba_cols = ['1','2','3','4','5','6','7','8','9','12','21','23','32','34','43','45','54','56','65','67','76','78','87','89','98'] # 1-9 control (how many open hands have dora pair after tedashi/tsumogiri turn X). 12 = dora 1, discarded 2.
        self.dsoba_tedashi = pd.DataFrame(0, index=[0,1,2], columns=dsoba_cols) # Count of dora pair given dorasoba tedashi on row X.
        self.dsoba_tedashi_c = pd.DataFrame(0, index=[0,1,2], columns=dsoba_cols) # Count of dorasoba tedashi on row X.
        self.dsoba_tsumogiri = pd.DataFrame(0, index=[0,1,2], columns=dsoba_cols)
        self.dsoba_tsumogiri_c = pd.DataFrame(0, index=[0,1,2], columns=dsoba_cols)

    def RoundStarted(self, init):
        super().RoundStarted(init)
        self.tedashi = [[], [], [], []]
        self.just_called = False

        for who in range(4):
            shanten = sh.calculateMinimumShanten(self.hands[who])
            uke, wait = sh.calculateUkeire(self.hands[who], baseShanten = shanten)
            self.previous_shape[who] = (shanten, uke)

    def RiichiCalled(self, who, step, element):
        self.end_round = True

    def TileDrawn(self, who, tile, element):
        super().TileDrawn(who, tile, element)
        self.just_called = False

    def TileCalled(self, who, tiles, element):
        super().TileCalled(who, tiles, element)
        self.just_called = True

    def TileDiscarded(self, who, tile, tsumogiri, element):
        super().TileDiscarded(who, tile, tsumogiri, element)
        self.tedashi[who].append(not tsumogiri)

        if self.turn >= 19 or len(self.calls[who]) == 4:
            self.end_round = True
            return
        
        if not tsumogiri and not self.just_called:
            shanten = sh.calculateMinimumShanten(self.hands[who])
            uke, wait = sh.calculateUkeire(self.hands[who], baseShanten = shanten)

            # Shanten Reduction
            if shanten == self.previous_shape[who][0]:
                if uke == self.previous_shape[who][1]:
                    shanten_cat = "Same Ukeire"
                elif uke > self.previous_shape[who][1]:
                    shanten_cat = "Increase Ukeire"
                else:
                    shanten_cat = "Reduce Ukeire"
            elif shanten < self.previous_shape[who][0]:
                shanten_cat = "Reduce Shanten"
            else:
                shanten_cat = "Increase Shanten"

            # Wait around tedashi
            if shanten == 0:
                wait_cat = "Not tedashi"
                for wait_tile in wait:
                    if tile // 10 == wait_tile // 10 and tile <= wait_tile + 2 and tile >= wait_tile - 2:
                        wait_cat = "Wait tedashi"
            else:
                wait_cat = "Noten"

            if len(self.calls[who]) == 0:
                self.closed_tedashi.loc[self.turn, shanten_cat] += 1
                self.tedashi_closed_wait.loc[self.turn, wait_cat] += 1
            elif len(self.calls[who]) == 1:
                self.open_tedashi_1.loc[self.turn, shanten_cat] += 1
                self.tedashi_1_wait.loc[self.turn, wait_cat] += 1
            elif len(self.calls[who]) == 2:
                self.open_tedashi_2.loc[self.turn, shanten_cat] += 1
                self.tedashi_2_wait.loc[self.turn, wait_cat] += 1
            elif len(self.calls[who]) == 3:
                self.open_tedashi_3.loc[self.turn, shanten_cat] += 1
                self.tedashi_3_wait.loc[self.turn, wait_cat] += 1

            # Update shape
            self.previous_shape[who] = (shanten, uke)

        # Dora pair
        if self.dora[0] < 30:
            row = (self.turn + 1) // 6
            if row > 2: row = 2
            dora = self.dora[0]

            cat = [str(dora % 10)]
            if tile == dora + 1 or tile == dora - 1:
                cat.append(cat[0] + str(tile % 10))

            if tsumogiri:
                self.dsoba_tsumogiri_c.loc[row,cat] += 1
                if self.hands[who][dora] >= 2:
                    self.dsoba_tsumogiri.loc[row,cat] += 1
            else:
                self.dsoba_tedashi_c.loc[row,cat] += 1
                if self.hands[who][dora] >= 2:
                    self.dsoba_tedashi.loc[row,cat] += 1
                
    def PrintResults(self):
        self.closed_tedashi["Count"] = self.closed_tedashi.sum(axis=1)
        self.open_tedashi_1["Count"] = self.open_tedashi_1.sum(axis=1)
        self.open_tedashi_2["Count"] = self.open_tedashi_2.sum(axis=1)
        self.open_tedashi_3["Count"] = self.open_tedashi_3.sum(axis=1)

        self.closed_tedashi.to_csv(output, mode='w', index_label='closed')
        self.open_tedashi_1.to_csv(output, mode='a', index_label='1')
        self.open_tedashi_2.to_csv(output, mode='a', index_label='2')
        self.open_tedashi_3.to_csv(output, mode='a', index_label='3')

        self.tedashi_closed_wait.to_csv(output, mode='a', index_label='closed')
        self.tedashi_1_wait.to_csv(output, mode='a', index_label='1')
        self.tedashi_2_wait.to_csv(output, mode='a', index_label='2')
        self.tedashi_3_wait.to_csv(output, mode='a', index_label='3')

        d_ted = self.dsoba_tedashi/self.dsoba_tedashi_c
        d_tsu = self.dsoba_tsumogiri/self.dsoba_tsumogiri_c
        d_ted.to_csv(output, mode='a', index_label='dsoba ted')
        d_tsu.to_csv(output, mode='a', index_label='dsoba tsu')