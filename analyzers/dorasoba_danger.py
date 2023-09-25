from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd

# Gathers the danger level of dorasoba vs non-dorasoba, for open hands and riichi hands.
# Only consider the original dora.
# Ignores cases when dora honor has been discarded thrice.

# For each tile dealt after a riichi or call, check if they are tenpai. If they are, tabulate the wait:
# Waiting on dora complex, dora sanmenchan, dora ryanmen, dora single, dora shanpon, dorasoba sanmenchan, dorasoba ryanmen, dorasoba single, none.
# Eg for dora 5m: 258m 25m1p 2356m, 25m 58m, 5m, 5m4s, 36m 47m, 4m 6m. Can compare to expected data from riichi waits.

output = "./results/DorasobaDanger.csv"

class DorasobaDanger(LogHandAnalyzer):
    def __init__(self):
        super().__init__()

        self.riichi_counts = 0      
        self.open_counts = 0
        self.riichiwait_df = pd.DataFrame(0,columns=[1,2,3,4,5,6,7,8,9,"honor fresh","honor 1 out","honor 2 out"],index=["dora complex", "dora sanmenchan", "dora ryanmen", "dora single", "dora shanpon", "dorasoba complex", "dorasoba sanmenchan", "dorasoba ryanmen", "dorasoba single", "none"])
        self.openwait_df = pd.DataFrame(0,columns=[1,2,3,4,5,6,7,8,9,"honor fresh","honor 1 out","honor 2 out"],index=["dora complex", "dora sanmenchan", "dora ryanmen", "dora single", "dora shanpon", "dorasoba complex", "dorasoba sanmenchan", "dorasoba ryanmen", "dorasoba single", "none"])

        self.recorded = [False,False,False,False]

    def RoundStarted(self, init):
        self.recorded = [False,False,False,False]
        return super().RoundStarted(init)

    def RiichiCalled(self, who, step, element):
        if step != 2: return
        if not self.recorded[who]:
            uke, wait = sh.calculateUkeire(self.hands[who])
            self.record(isRiichi=True, wait=wait)
            self.recorded[who] = True

    def TileDiscarded(self, who, tile, tsumogiri, element):
        super().TileDiscarded(who, tile, tsumogiri, element)

        # If have called and tedashi, check if tenpai
        if len(self.calls[who]) > 0 and not tsumogiri and not self.recorded[who]:
            if sh.isTenpai(self.hands[who]):
                uke, wait = sh.calculateUkeire(self.hands[who], baseShanten = 0)
                self.record(isRiichi=False,wait=wait)
                self.recorded[who] = True

    def record(self, isRiichi, wait):
        d = self.dora[0]
        wait_type = "none"

        if d > 30:
            honor_out = 0
            for discards in self.discards:
                honor_out += discards.count(d)

            if honor_out == 0:
                dora_type = "honor fresh"
            if honor_out == 1:
                dora_type = "honor 1 out"
            if honor_out == 2:
                dora_type = "honor 2 out"
            if honor_out >= 3:
                return
                
            if d in wait:
                if len(wait) == 1:
                    wait_type = "dora single"
                elif len(wait) == 2:
                    wait_type = "dora shanpon"
                else:
                    wait_type = "dora complex"

        else:
            dora_type = d % 10
            if d in wait:
                wait_type = "dora "
                if len(wait) >= 3:
                    if wait[1] == wait[0] + 3 and wait[2] == wait[0] + 6 and wait[0] // 10 == wait[2] // 10:
                        wait_type += "sanmenchan"
                    else:
                        wait_type += "complex"
                elif len(wait) == 1:
                    wait_type += "single"
                elif wait[1] == wait[0] + 3 and wait[0] // 10 == wait[1] // 10:
                    wait_type += "ryanmen"
                else:
                    wait_type += "shanpon"

            else:
                dorasoba_flag = False
                for i in range(-2,3):
                    if d+i in wait and d+i // 10 == d+i // 10:
                        dorasoba_flag = True
                if dorasoba_flag:
                    if len(wait) >= 3:
                        if wait[1] == wait[0] + 3 and wait[2] == wait[0] + 6 and d > wait[0] and d < wait [2] and wait[0] // 10 == wait[2] // 10: # Only include if the dora is in the joint
                            wait_type = "dorasoba sanmenchan"
                        elif d > wait[0] and d < wait [-1]:
                            wait_type = "dorasoba complex"
                    elif len(wait) == 1:
                        wait_type = "dorasoba single"
                    elif wait[1] == wait[0] + 3 and d > wait[0] and d < wait [1]: # Only include if the dora is in the joint
                        wait_type = "dorasoba ryanmen"

        #print(wait, d, dora_type, wait_type)
        if isRiichi:
            self.riichi_counts += 1
            self.riichiwait_df.loc[wait_type, dora_type] += 1
        else:
            self.open_counts += 1
            self.openwait_df.loc[wait_type, dora_type] += 1

    def PrintResults(self):
        self.riichiwait_df.to_csv(output, mode='w', index_label='Riichi wait')
        self.openwait_df.to_csv(output, mode='a', index_label='Open wait')
        with open(output, "a", encoding="utf8") as f:
            f.write(f"Total riichi,{self.riichi_counts}")
            f.write(f"\nTotal open,{self.open_counts}")