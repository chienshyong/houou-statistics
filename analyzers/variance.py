from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
from util.analysis_utils import convertHai, convertTile, convertTileCheckAka, discards, draws, GetNextRealTag, GetStartingHands, getTilesFromCall, GetDora
import pandas as pd
import numpy as np
import statistics

# Finding the mean and std dev score change by position and round.

output = "./results/Variance.csv"

positions = [1,2,3,4,"Ahead <4000","Ahead 4000","Ahead 8000","Ahead 12000","Ahead 16000","Behind <4000","Behind 4000","Behind 8000","Behind 12000","Behind 16000", "All"]
rounds = [0,1,2,3,4,5,6,7]

class Variance(LogHandAnalyzer):
    def __init__(self):
        super().__init__()
        self.round_position_score_df = [[[] for _ in range(len(positions))] for _ in range(len(rounds))]
        self.dealer_round_position_score_df = [[[] for _ in range(len(positions))] for _ in range(len(rounds))]
    
    def PlayRound(self, round_):
        self.RoundStarted(round_)
        if self.round[0] > 7: return

        current_positions = [[],[],[],[]]
        sorted_scores = self.scores.copy()
        sorted_scores.sort()
        for i in range(4):
            current_positions[i].append(4 - sorted_scores.index(self.scores[i]))
            if current_positions[i][0] == 1:
                if sorted_scores[3] - sorted_scores[2] > 160:
                    current_positions[i].append("Ahead 16000")
                elif sorted_scores[3] - sorted_scores[2] > 120:
                    current_positions[i].append("Ahead 12000")
                elif sorted_scores[3] - sorted_scores[2] > 80:
                    current_positions[i].append("Ahead 8000")
                elif sorted_scores[3] - sorted_scores[2] > 40:
                    current_positions[i].append("Ahead 4000")
                else:
                    current_positions[i].append("Ahead <4000")
            elif current_positions[i][0] == 4:
                if sorted_scores[1] - sorted_scores[0] > 160:
                    current_positions[i].append("Behind 16000")
                elif sorted_scores[1] - sorted_scores[0] > 120:
                    current_positions[i].append("Behind 12000")
                elif sorted_scores[1] - sorted_scores[0] > 80:
                    current_positions[i].append("Behind 8000")
                elif sorted_scores[1] - sorted_scores[0] > 40:
                    current_positions[i].append("Behind 4000")
                else:
                    current_positions[i].append("Behind <4000")

        for element in round_.itersiblings():
            if element.tag == "AGARI":
                sc = element.attrib["sc"].split(',')
                newscores = [int(sc[0]),int(sc[2]),int(sc[4]),int(sc[6])] #After riichi bets
                change = [int(sc[1]),int(sc[3]),int(sc[5]),int(sc[7])]
                delta = [x - y + z for x,y,z in zip(newscores, self.scores, change)]
                for i in range(4):
                    if self.oya == i:
                        for p in current_positions[i]:
                            self.dealer_round_position_score_df[self.round[0]][positions.index(p)].append(delta[i])
                            self.dealer_round_position_score_df[self.round[0]][-1].append(delta[i])
                    else:
                        for p in current_positions[i]:
                            self.round_position_score_df[self.round[0]][positions.index(p)].append(delta[i])
                            self.round_position_score_df[self.round[0]][-1].append(delta[i])
                break
            
            elif element.tag == "RYUUKYOKU":
                if "type" in element.attrib:
                    self.AbortiveDraw(element)
                else:
                    sc = element.attrib["sc"].split(',')
                    newscores = [int(sc[0]),int(sc[2]),int(sc[4]),int(sc[6])]
                    change = [int(sc[1]),int(sc[3]),int(sc[5]),int(sc[7])]
                    delta = [x - y + z for x,y,z in zip(newscores, self.scores, change)]
                    for i in range(4):
                        if self.oya == i:
                            for p in current_positions[i]:
                                self.dealer_round_position_score_df[self.round[0]][positions.index(p)].append(delta[i])
                                self.dealer_round_position_score_df[self.round[0]][-1].append(delta[i])
                        else:
                            for p in current_positions[i]:
                                self.round_position_score_df[self.round[0]][positions.index(p)].append(delta[i])
                                self.round_position_score_df[self.round[0]][-1].append(delta[i])
                break    

    def PrintResults(self):
        with open(output, "w", encoding="utf8") as f:
            f.write("Round,Position,Mean,Stddev\n")
            for r, round in enumerate(rounds):
                for p, position in enumerate(positions):
                    if len(self.round_position_score_df[r][p]) > 2:
                        f.write(f"{round},{position},")
                        f.write(f"{statistics.mean(self.round_position_score_df[r][p])},")
                        f.write(f"{statistics.stdev(self.round_position_score_df[r][p])}\n")
            f.write("\nDealer\n")
            for r, round in enumerate(rounds):
                for p, position in enumerate(positions):
                    if len(self.dealer_round_position_score_df[r][p]) > 2:
                        f.write(f"{round},{position},")
                        f.write(f"{statistics.mean(self.dealer_round_position_score_df[r][p])},")
                        f.write(f"{statistics.stdev(self.dealer_round_position_score_df[r][p])}\n")