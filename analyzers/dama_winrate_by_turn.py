from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd

# Estimating dama winrate by counting tiles thrown before any players are dangerous.
# Change to 1st, 2nd, 3rd, 4th.

output = "./results/DamaWinrateByTurn.csv"

class DamaWinrateByTurn(LogHandAnalyzer):
    def __init__(self):
        super().__init__()
        self.discarded = [0] * 38 # Times discarded before

        # Tiles thrown out if there is no danger players
        dama_cats = ['19','28','37','46','5','Honor']
        self.first_tile = pd.DataFrame(0, columns=range(19), index=dama_cats) # Number of fresh tiles discarded. eg. fresh 19 discarded -> += 1
        self.second_tile = pd.DataFrame(0, columns=range(19), index=dama_cats)
        self.third_tile = pd.DataFrame(0, columns=range(19), index=dama_cats)
        self.fourth_tile = pd.DataFrame(0, columns=range(19), index=dama_cats)

        self.first_dora = pd.DataFrame(0, columns=range(19), index=dama_cats)
        self.second_dora = pd.DataFrame(0, columns=range(19), index=dama_cats)
        self.third_dora = pd.DataFrame(0, columns=range(19), index=dama_cats)
        self.fourth_dora = pd.DataFrame(0, columns=range(19), index=dama_cats)

        self.first_tile_c = pd.DataFrame(0, columns=range(19), index=dama_cats) # Number of fresh tiles of that type. eg. all terminals fresh -> '19' += 6
        self.second_tile_c = pd.DataFrame(0, columns=range(19), index=dama_cats)
        self.third_tile_c = pd.DataFrame(0, columns=range(19), index=dama_cats)
        self.fourth_tile_c = pd.DataFrame(0, columns=range(19), index=dama_cats)

        self.first_dora_c = pd.DataFrame(0, columns=range(19), index=dama_cats)
        self.second_dora_c = pd.DataFrame(0, columns=range(19), index=dama_cats)
        self.third_dora_c = pd.DataFrame(0, columns=range(19), index=dama_cats)
        self.fourth_dora_c = pd.DataFrame(0, columns=range(19), index=dama_cats)

    def RoundStarted(self, init):
        super().RoundStarted(init)
        self.discarded = [0] * 38 #

    def TileCalled(self, who, tiles, element):
        super().TileCalled(who, tiles, element)
        if len(tiles) >= 3:
            if tiles[0] in self.dora and tiles[1] in self.dora:
                self.end_round = True

    def RiichiCalled(self, who, step, element):
        super().RiichiCalled(who, step, element)
        self.end_round = True

    def TileDiscarded(self, who, tile, tsumogiri, element):
        super().TileDiscarded(who, tile, tsumogiri, element)
        if self.turn >= 19:
            self.end_round = True
            return

        # Count of possible tiles = 37 total. ~3 throws average to ~3/37 chance of each tile thrown before your next draw.
        if who == self.oya:
            for i in range(38):
                if i % 10 == 0: continue
                dama_cat = getDamaCat(i)
                if i in self.dora:
                    if self.discarded[i] == 0:
                        self.first_dora_c.loc[dama_cat, self.turn] += 1
                    elif self.discarded[i] == 1:
                        self.second_dora_c.loc[dama_cat, self.turn] += 1
                    elif self.discarded[i] == 2:
                        self.third_dora_c.loc[dama_cat, self.turn] += 1
                    elif self.discarded[i] == 3:
                        self.fourth_dora_c.loc[dama_cat, self.turn] += 1
                else:
                    if self.discarded[i] == 0:
                        self.first_tile_c.loc[dama_cat, self.turn] += 1
                    elif self.discarded[i] == 1:
                        self.second_tile_c.loc[dama_cat, self.turn] += 1
                    elif self.discarded[i] == 2:
                        self.third_tile_c.loc[dama_cat, self.turn] += 1
                    elif self.discarded[i] == 3:
                        self.fourth_tile_c.loc[dama_cat, self.turn] += 1

        if who != self.oya:
            dama_cat = getDamaCat(tile)
            if tile in self.dora:
                if self.discarded[tile] == 0:
                    self.first_dora.loc[dama_cat, self.turn] += 1
                elif self.discarded[tile] == 1:
                    self.second_dora.loc[dama_cat, self.turn] += 1
                elif self.discarded[tile] == 2:
                    self.third_dora.loc[dama_cat, self.turn] += 1
                elif self.discarded[tile] == 3:
                    self.fourth_dora.loc[dama_cat, self.turn] += 1
            else:
                if self.discarded[tile] == 0:
                    self.first_tile.loc[dama_cat, self.turn] += 1
                elif self.discarded[tile] == 1:
                    self.second_tile.loc[dama_cat, self.turn] += 1
                elif self.discarded[tile] == 2:
                    self.third_tile.loc[dama_cat, self.turn] += 1
                elif self.discarded[tile] == 3:
                    self.fourth_tile.loc[dama_cat, self.turn] += 1

        self.discarded[tile] += 1

    def PrintResults(self):
        first_tile = self.first_tile/self.first_tile_c
        second_tile = self.second_tile/self.second_tile_c
        third_tile = self.third_tile/self.third_tile_c
        fourth_tile = self.fourth_tile/self.fourth_tile_c
        first_dora = self.first_dora/self.first_dora_c
        second_dora = self.second_dora/self.second_dora_c
        third_dora = self.third_dora/self.third_dora_c
        fourth_dora = self.fourth_dora/self.fourth_dora_c

        first_tile.to_csv(output, mode='w', index_label='1st')
        second_tile.to_csv(output, mode='a', index_label='2nd')
        third_tile.to_csv(output, mode='a', index_label='3rd')
        fourth_tile.to_csv(output, mode='a', index_label='4th')
        first_dora.to_csv(output, mode='a', index_label='1st d')
        second_dora.to_csv(output, mode='a', index_label='2nd d')
        third_dora.to_csv(output, mode='a', index_label='3rd d')
        fourth_dora.to_csv(output, mode='a', index_label='4th d')

catmap = {1:'19',2:'28',3:'37',4:'46',5:'5',6:'46',7:'37',8:'28',9:'19'}
def getDamaCat(tile):
    if tile > 30: return 'Honor'
    return catmap[tile%10]