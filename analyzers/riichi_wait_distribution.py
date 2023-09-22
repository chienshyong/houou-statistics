from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd

# Gathers the distribution of waits for riichis for sanmenchan, ryanmen, single and shanpon waits.
# Complex waits are ignored.

output = "./results/RiichiWait.csv"

class RiichiWaitDistribution(LogHandAnalyzer):
    def __init__(self):
        super().__init__()

        self.riichi_counts = 0      
        self.complex_waits = 0
        self.riichiwait_df = pd.DataFrame(0,columns=["sanmenchan", "ryanmen", "single"],index=[1,2,3,4,5,6,7,8,9,"honor"])
        self.riichishanpon_df = pd.DataFrame(0,columns=[1,2,3,4,5,6,7,8,9,"honor"],index=[1,2,3,4,5,6,7,8,9,"honor"])

    def RiichiCalled(self, who, step, element):
        if step != 2: return
        uke, wait = sh.calculateUkeire(self.hands[who])
        self.record(uke, wait)
        
    def PrintResults(self):
        print(self.riichiwait_df)
        print(self.riichishanpon_df)
        print("Total riichis: " + str(self.riichi_counts))
        self.riichiwait_df.to_csv(output, mode='w')
        self.riichishanpon_df.to_csv(output, mode='a')
        with open(output, "a", encoding="utf8") as f:
            f.write(f"Total riichi,{str(self.riichi_counts)}")
            f.write("\n")
            f.write(f"Complex waits,{str(self.complex_waits)}")
    
    def record(self, uke, wait):
        self.riichi_counts += 1
        if len(wait) == 3:
            if all(i//10 == wait[0]//10 for i in wait) and wait[0] + 3 == wait[1] and wait[1] + 3 == wait[2]:
                    self.riichiwait_df.loc[wait[0]%10,"sanmenchan"] += 1
        if len(wait) >= 3:
            self.complex_waits += 1
            return
        if len(wait) == 1:
            if wait[0] < 30:
                self.riichiwait_df.loc[wait[0]%10,"single"] += 1
            else:
                self.riichiwait_df.loc["honor","single"] += 1
        if len(wait) == 2:
            if all(i//10 == wait[0]//10 for i in wait) and wait[0] + 3 == wait[1] and uke >= 5:
                self.riichiwait_df.loc[wait[0]%10,"ryanmen"] += 1
            else:
                w0 = "honor" if wait[0] > 30 else wait[0]%10
                w1 = "honor" if wait[1] > 30 else wait[1]%10
                if w0 != "honor" and w1 != "honor":
                    if w0 > w1:
                        w0, w1 = w1, w0
                self.riichishanpon_df.loc[w0,w1] += 1
