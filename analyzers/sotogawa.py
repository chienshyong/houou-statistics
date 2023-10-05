from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd

# Gathers the usefulness of sotogawa, split by early and mid game discards

output = "./results/Sotogawa.csv"

class Sotogawa(LogHandAnalyzer):
    def __init__(self):
        super().__init__()

        self.riichi_counts = 0
        self.firstrow_counts = 0
        self.secondrow_counts = 0
        self.firstrow_df = pd.DataFrame(0,index=[1,2,3,4,5,6,7,8,9],columns=[1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,19,"Honor"]) #Let 11-19 rep. 1 to 9 in other suits
        self.secondrow_df = pd.DataFrame(0,index=[1,2,3,4,5,6,7,8,9],columns=[1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,19,"Honor"]) #Let 11-19 rep. 1 to 9 in other suits

    def RiichiCalled(self, who, step, element):
        if step != 2: return
        self.riichi_counts += 1
        uke, wait = sh.calculateUkeire(self.hands[who],baseShanten=0)

        for i in range(min(len(self.discards[who])-1, 12)):
            d = self.discards[who][i]
            if d < 30:
                if i <= 6:
                    self.firstrow_counts += 1
                    for w in wait:
                        if w > 30:
                            wait_class = "Honor"
                        elif d // 10 == w // 10:
                            wait_class = w % 10
                        else:
                            wait_class = w % 10 + 10
                        self.firstrow_df.loc[d%10, wait_class] += 1  
                else:
                    self.secondrow_counts += 1
                    for w in wait:
                        if w > 30:
                            wait_class = "Honor"
                        elif d // 10 == w // 10:
                            wait_class = w % 10
                        else:
                            wait_class = w % 10 + 10
                        self.secondrow_df.loc[d%10, wait_class] += 1

    def PrintResults(self):
        print(self.firstrow_df)
        print(self.secondrow_df)
        self.firstrow_df.to_csv(output, mode='w', index_label='First row')
        self.secondrow_df.to_csv(output, mode='a', index_label='Second row')
        with open(output, "a", encoding="utf8") as f:
            f.write(f"Total riichi,{self.riichi_counts}\n")
            f.write(f"Total first row,{self.firstrow_counts}\n")
            f.write(f"Total second row,{self.secondrow_counts}")