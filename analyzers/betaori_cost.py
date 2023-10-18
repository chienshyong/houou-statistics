from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
from util.analysis_utils import convertHai, convertTile, convertTileCheckAka, discards, draws, GetNextRealTag, GetStartingHands, getTilesFromCall, GetDora
import pandas as pd
import numpy as np
import statistics

# What is the point loss of not winning a hand & not being tenpai? (Point loss from tsumos and noten penalty)
# Given that X1 players have riichi and X2 players are open
# Given the turn
# Given who is the dealer
# eg What is the cost of not winning hand on turn 9 with 1 open player, 1 riichi as the dealer?

output = "./results/BetaoriCost.csv"
turns_considered = [4,6,8,10,12,14,16,18]

class BetaoriCost(LogHandAnalyzer):
    def __init__(self):
        super().__init__()
        self.score_change = [-1,-1,-1,-1]
        self.eventual_winner = -1
        self.eventual_dealin = -1
        self.riichi_turn = [-1,-1,-1,-1]
        self.call_turn = [-1,-1,-1,-1]

        # Case: no riichi, 0,1,2,3 open
        self.calls_turn_df = pd.DataFrame(0, index=turns_considered, columns=["D", "ND", "D vs ND", "ND vs ND", "ND vs D", "D vs ND ND", "ND vs ND ND", "ND vs D ND", "D vs ND ND ND", "ND vs D ND ND"])
        self.calls_turn_count_df = pd.DataFrame(0, index=turns_considered, columns=["D", "ND", "D vs ND", "ND vs ND", "ND vs D", "D vs ND ND", "ND vs ND ND", "ND vs D ND", "D vs ND ND ND", "ND vs D ND ND"])

        # Case: vs 1,2,3 riichi, any number of calls
        self.riichi_turn_df = pd.DataFrame(0, index=turns_considered, columns=["D vs ND", "ND vs ND", "ND vs D", "D vs ND ND", "ND vs ND ND", "ND vs D ND", "D vs ND ND ND", "ND vs D ND ND"]) # Cost of folding on turn X vs a riichi. 
        self.riichi_turn_count_df = pd.DataFrame(0, index=turns_considered, columns=["D vs ND", "ND vs ND", "ND vs D", "D vs ND ND", "ND vs ND ND", "ND vs D ND", "D vs ND ND ND", "ND vs D ND ND"])

    def RoundStarted(self, init):
        super().RoundStarted(init)
        self.score_change = [-1,-1,-1,-1]
        self.riichi_turn = [-1,-1,-1,-1]
        self.call_turn = [-1,-1,-1,-1]

        self.eventual_winner = -1
        self.eventual_dealin = -1

        # Get eventual winner, dealin and score change
        for element in init.itersiblings():
            if element.tag == "AGARI":
                self.eventual_winner = int(element.attrib["who"])
                self.eventual_dealin = int(element.attrib["fromWho"])
                self.score_change = element.attrib["sc"].split(',')[1::2]
                break
            elif element.tag == "RYUUKYOKU":
                self.score_change = element.attrib["sc"].split(',')[1::2]
                if element.attrib["ba"].split(',')[1] != 0 and self.score_change.count("0") == 4: #All tenpai
                    self.end_round = True
                break
        self.score_change = [int(i) for i in self.score_change]

    def TileCalled(self, who, tiles, element):
        super().TileCalled(who, tiles, element)
        if self.call_turn[who] == -1:
            self.call_turn[who] = self.turn

    def RiichiCalled(self, who, step, element):
        self.riichi_turn[who] = self.turn
        super().RiichiCalled(who, step, element)
    
    def TileDiscarded(self, who, tile, tsumogiri, element):
        super().TileDiscarded(who, tile, tsumogiri, element)
        if who == 0 and self.turn in turns_considered:
            for player in range(4):
                if self.eventual_winner == -1: #Eventual draw. Append for all those noten.
                    if self.score_change[player] > 0: continue #Ended up tenpai
                else: #Eventual win. Append for all non winners and non dealins.
                    if player == self.eventual_winner or player == self.eventual_dealin: 
                        continue

                if self.riichi_turn.count(-1) == 4: #No riichis
                    if player == self.oya:
                        cat = "D"
                    else:
                        cat = "ND"

                    if self.call_turn.count(-1) == 4 or (self.call_turn.count(-1) == 3 and self.call_turn[player] != -1): #No other calls
                        pass
                    else:
                        cat += " vs"
                        if self.oya != player and self.call_turn[self.oya] != -1:
                            cat += " D"
                        for other_player in range(4):
                            if other_player == player or other_player == self.oya:
                                continue
                            if self.call_turn[other_player] != -1:
                                cat += " ND"
                    
                    self.calls_turn_df.loc[self.turn,cat] += self.score_change[player]
                    self.calls_turn_count_df.loc[self.turn,cat] += 1

                else: #At least 1 riichi
                    if self.riichi_turn[player] != -1: continue
                    if player == self.oya:
                        cat = "D vs"
                    else:
                        cat = "ND vs"

                    if self.oya != player and self.riichi_turn[self.oya] != -1:
                            cat += " D"
                    for other_player in range(4):
                        if other_player == player or other_player == self.oya:
                            continue
                        if self.riichi_turn[other_player] != -1:
                            cat += " ND"

                    self.riichi_turn_df.loc[self.turn,cat] += self.score_change[player]
                    self.riichi_turn_count_df.loc[self.turn,cat] += 1

    def PrintResults(self):
        call_turn = self.calls_turn_df / self.calls_turn_count_df
        call_turn.to_csv(output, mode='w', index_label='callturn')
        self.calls_turn_count_df.to_csv(output, mode='a', index_label='callturn')
        
        riichi_turn = self.riichi_turn_df / self.riichi_turn_count_df
        riichi_turn.to_csv(output, mode='a', index_label='riichiturn')
        self.riichi_turn_count_df.to_csv(output, mode='a', index_label='riichiturn')