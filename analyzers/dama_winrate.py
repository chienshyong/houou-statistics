from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd

# Estimating dama winrate by counting tiles thrown before any players are dangerous.

output = "./results/DamaWinrate.csv"

class DamaWinrate(LogHandAnalyzer):
    def __init__(self):
        super().__init__()
        self.fresh = [True] * 38 # Has been discarded before

        # Tiles thrown out if there is no danger players
        dama_cats = ['19','28','37','46','5','Honor']
        self.first_tile = pd.DataFrame(0, columns=range(19), index=dama_cats) # Number of fresh tiles discarded. eg. fresh 19 discarded -> += 1
        self.nonfirst_tile = pd.DataFrame(0, columns=range(19), index=dama_cats)
        self.first_dora = pd.DataFrame(0, columns=range(19), index=dama_cats)
        self.nonfirst_dora = pd.DataFrame(0, columns=range(19), index=dama_cats)

        self.first_tile_c = pd.DataFrame(0, columns=range(19), index=dama_cats) # Number of fresh tiles of that type. eg. all terminals fresh -> '19' += 6
        self.nonfirst_tile_c = pd.DataFrame(0, columns=range(19), index=dama_cats)
        self.first_dora_c = pd.DataFrame(0, columns=range(19), index=dama_cats)
        self.nonfirst_dora_c = pd.DataFrame(0, columns=range(19), index=dama_cats)

    def RoundStarted(self, init):
        super().RoundStarted(init)
        self.fresh = [True] * 38

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
                    if self.fresh[i]:
                        self.first_dora_c.loc[dama_cat, self.turn] += 1
                    else:
                        self.nonfirst_dora_c.loc[dama_cat, self.turn] += 1
                else:
                    if self.fresh[i]:
                        self.first_tile_c.loc[dama_cat, self.turn] += 1
                    else:
                        self.nonfirst_tile_c.loc[dama_cat, self.turn] += 1

        if who != self.oya:
            if tile % 10 != 0: 
                dama_cat = getDamaCat(tile)
                if tile in self.dora:
                    if self.fresh[tile]:
                        self.first_dora.loc[dama_cat, self.turn] += 1
                    else:
                        self.nonfirst_dora.loc[dama_cat, self.turn] += 1
                else:
                    if self.fresh[tile]:
                        self.first_tile.loc[dama_cat, self.turn] += 1
                    else:
                        self.nonfirst_tile.loc[dama_cat, self.turn] += 1

        if self.fresh[tile]:
            self.fresh[tile] = False

    def PrintResults(self):
        first_tile = self.first_tile/self.first_tile_c
        nfirst_tile = self.nonfirst_tile/self.nonfirst_tile_c
        first_dora = self.first_dora/self.first_dora_c
        nfirst_dora = self.nonfirst_dora/self.nonfirst_dora_c

        first_tile.to_csv(output, mode='w', index_label='1st')
        nfirst_tile.to_csv(output, mode='a', index_label='n1st')
        first_dora.to_csv(output, mode='a', index_label='1st d')
        nfirst_dora.to_csv(output, mode='a', index_label='n1st d')


def getDamaCat(tile):
    if tile > 30: return 'Honor'
    if tile % 10 == 1 or tile % 10 == 9: return '19'
    if tile % 10 == 2 or tile % 10 == 8: return '28'
    if tile % 10 == 3 or tile % 10 == 7: return '37'
    if tile % 10 == 4 or tile % 10 == 6: return '46'
    if tile % 10 == 5: return '5'