from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
from util.analysis_utils import convertHai, convertTile, convertTileCheckAka, discards, draws, GetNextRealTag, GetStartingHands, getTilesFromCall, GetDora
import pandas as pd

# Distribution of hand scores won by Round and Position. In South 1, how many pts can you expect 4th place to win? 1st place? What if ahead or behind by more than 10000?

output = "./results/HandsWon.csv"

positions = [1,2,3,4,"Ahead <4000","Ahead 4000","Ahead 8000","Ahead 12000","Ahead 16000","Behind <4000","Behind 4000","Behind 8000","Behind 12000","Behind 16000"]
rounds = [1,2,3,4,5,6,7]
scores = [1100, 2000, 2700, 4000, 5200, 8000, 12000, 18000, 192000, "called", "riichi", "win", "dealin", "tenpai", "noten", "hands"] #Includes scores up to and inclusive of, excluding sticks

class HandsWon(LogHandAnalyzer):
    def __init__(self):
        super().__init__()
        self.position_score_dfs = {}
        for i in range(1,8): # Skip East 1
            self.position_score_dfs[i] = pd.DataFrame(0,index=scores,columns=positions)
    
    def PlayRound(self, round_):
        self.RoundStarted(round_)
        if self.round[0] == 0 or self.round[0] > 7: return # Skip East 1

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
            self.position_score_dfs[self.round[0]].loc["hands",current_positions[i]] += 1
        
        # print(self.round)
        # print(self.scores, sorted_scores)
        # print(current_positions)

        hascalled = [False,False,False,False]

        for element in round_.itersiblings():
            if element.tag == "N":
                who = int(element.attrib["who"])
                if not hascalled[who]:
                    self.position_score_dfs[self.round[0]].loc["called",current_positions[who]] += 1
                    hascalled[who] = True
            
            elif element.tag == "REACH":
                if element.attrib["step"] == "1":
                    who = int(element.attrib["who"])
                    self.position_score_dfs[self.round[0]].loc["riichi",current_positions[who]] += 1

            elif element.tag == "AGARI":
                self.Win(element, current_positions)
                break
            
            elif element.tag == "RYUUKYOKU":
                if "type" in element.attrib:
                    self.AbortiveDraw(element)
                else:
                    self.ExhaustiveDraw(element, current_positions)
                break
    
    def Win(self, element, current_positions):
        score = int(element.attrib["ten"].split(',')[1])
        who = int(element.attrib["who"])
        fromWho = int(element.attrib["fromWho"])
        for i in range(7,-1,-1):
            if score > scores[i]:
                score = scores[i+1]
                break
        if score == 1000: score = 1100
        
        self.position_score_dfs[self.round[0]].loc["win",current_positions[who]] += 1
        self.position_score_dfs[self.round[0]].loc[score,current_positions[who]] += 1
        if who != fromWho:
            self.position_score_dfs[self.round[0]].loc["dealin",current_positions[fromWho]] += 1

    def ExhaustiveDraw(self, element, current_positions):
        sc = element.attrib["sc"].split(',')
        for i in range(4):
            score = int(sc[2*i + 1])
            if score > 0:
                ten = "tenpai"
            else:
                ten = "noten"
            self.position_score_dfs[self.round[0]].loc[ten,current_positions[i]] += 1

    def PrintResults(self):
        for i in range(1,8):
            print(self.position_score_dfs[i])

        self.position_score_dfs[1].to_csv(output, mode='w', index_label='Rnd 1')
        for i in range(2,8):
            self.position_score_dfs[i].to_csv(output, mode='a', index_label=f'Rnd {i}')