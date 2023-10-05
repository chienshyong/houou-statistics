from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd

# Gathers the danger level of the ura and matagi suji of the first (and maybe 2nd and 3rd) simple tile discarded.
# Only for riichi hands. When someone riichi, check their first 3 simple tile discards and check their final wait.

output = "./results/FirstSimpleTile.csv"
simples = [2,3,4,5,6,7,8,12,13,14,15,16,17,18,22,23,24,25,26,27,28]

class FirstSimpleTile(LogHandAnalyzer):
    def __init__(self):
        super().__init__()

        self.riichi_counts = 0
        self.firstsimple_counts = 0
        self.thirdsimple_counts = 0
        self.firstsimple_df = pd.DataFrame(0,index=[2,3,4,5,6,7,8],columns=[1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,19,"Honor"]) #Let 11-19 rep. 1 to 9 in other suits
        self.thirdsimple_df = pd.DataFrame(0,index=[2,3,4,5,6,7,8],columns=[1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,19,"Honor"]) #Let 11-19 rep. 1 to 9 in other suits

    def RiichiCalled(self, who, step, element):
        if step != 2: return
        self.riichi_counts += 1
        uke, wait = sh.calculateUkeire(self.hands[who],baseShanten=0)

        simple_count = 0
        first_simple = 0
        third_simple = 0
        for i in range(len(self.discards[who])-1):
            d = self.discards[who][i]
            if d in simples:
                simple_count += 1
                if simple_count == 1:
                    first_simple = d
                if simple_count == 3:
                    third_simple = d
                    break

        if first_simple != 0:
            self.firstsimple_counts += 1
            for w in wait:
                if w > 30:
                    wait_class = "Honor"
                elif first_simple // 10 == w // 10:
                    wait_class = w % 10
                else:
                    wait_class = w % 10 + 10
                self.firstsimple_df.loc[first_simple%10, wait_class] += 1

        if third_simple != 0:
            self.thirdsimple_counts += 1
            for w in wait:
                if w > 30:
                    wait_class = "Honor"
                elif third_simple // 10 == w // 10:
                    wait_class = w % 10
                else:
                    wait_class = w % 10 + 10
                self.thirdsimple_df.loc[third_simple%10, wait_class] += 1

    def PrintResults(self):
        print(self.firstsimple_df)
        print(self.thirdsimple_df)
        self.firstsimple_df.to_csv(output, mode='w', index_label='First simple')
        self.thirdsimple_df.to_csv(output, mode='a', index_label='Third simple')
        with open(output, "a", encoding="utf8") as f:
            f.write(f"Total riichi,{self.riichi_counts}\n")
            f.write(f"Total first simple,{self.firstsimple_counts}\n")
            f.write(f"Total third simple,{self.thirdsimple_counts}")