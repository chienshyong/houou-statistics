from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import pandas as pd

# For closed hands, find your winning chances open or closed at this turn given no one has riichi, to better inform the decision of making the first call.

# First get the hand eventual winner, and whether they were closed or open.
# Measure the shanten and width of closed hands at turns 4, 6, 8, 10, 12, given that there is no one else riichi. Add to count and give the winner a +1

output = "./results/ShantenWidthWinrate.csv"
turns_considered = [4,6,8,10,12]

class ShantenWidthWinrate(LogHandAnalyzer):
    def __init__(self):
        super().__init__()

        #Count wins
        self.nocall_closedwin_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12])) # Hand closed now and won closed
        self.nocall_openwin_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12])) # Hand clsoed now and won open
        self.onecall_openwin_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12]))
        self.twocall_openwin_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12])) # Made 2 calls and won

        self.nocall_noothercall_closedwin_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12])) # No one has called, closed hand won closed
        self.nocall_noothercall_openwin_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12])) # No one has called, closed hand won open
        self.nocall_oneothercall_closedwin_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12])) # 1 has called, closed hand won closed
        self.nocall_oneothercall_openwin_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12])) # 1 has called, closed hand won open
        self.nocall_twoothercall_closedwin_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12])) # 2 or 3 has called, closed hand won closed
        self.nocall_twoothercall_openwin_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12]))
        
        #Count all
        self.nocall_count_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12]))
        self.nocall_noothercall_count_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12])) # No one has called
        self.nocall_oneothercall_count_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12]))
        self.nocall_twoothercall_count_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12]))
        self.onecall_count_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12]))
        self.twocall_count_df = initDF(pd.DataFrame(columns=["Shanten",4,6,8,10,12]))

        self.hand_count = 0
        self.winner_open = [] # empty means no winner
        self.winner_closed = []

    def PlayRound(self, round_):
        self.hand_count += 1
        self.winner_open = []
        self.winner_closed = []

        # Get eventual winner and whether they made calls
        for element in round_.itersiblings():
            if element.tag == "AGARI":
                if "m" in element.attrib:
                    self.winner_open.append(int(element.attrib["who"]))
                else:
                    self.winner_closed.append(int(element.attrib["who"]))
            elif element.tag == "RYUUKYOKU" or element.tag == "INIT":
                break
        super().PlayRound(round_)

    def RiichiCalled(self, who, step, element):
        self.end_round = True
        return super().RiichiCalled(who, step, element)
    
    def TileDiscarded(self, who, tile, tsumogiri, element):
        super().TileDiscarded(who, tile, tsumogiri, element)
        turn = len(self.discards[(self.oya-1)%4]) #Let everyone have their nth discard
        if who == 0 and turn in turns_considered:
            for i in range(4):
                shanten = sh.calculateMinimumShanten(self.hands[i])
                uke, wait = sh.calculateUkeire(self.hands[i],self.calls[i],shanten)
                shanten_group = group_shanten(shanten, uke)
                
                num_calls = len(self.calls[i])
                if num_calls == 0:
                    self.nocall_count_df.loc[self.nocall_noothercall_count_df["Shanten"] == shanten_group,turn] += 1
                    # Get the number of other players who have called
                    callers = 0
                    for j in range(4):
                        if len(self.calls[j]) > 0:
                            callers += 1

                    if callers == 0:
                        self.nocall_noothercall_count_df.loc[self.nocall_noothercall_count_df["Shanten"] == shanten_group,turn] += 1
                    elif callers == 1:
                        self.nocall_oneothercall_count_df.loc[self.nocall_oneothercall_count_df["Shanten"] == shanten_group,turn] += 1
                    else:
                        self.nocall_twoothercall_count_df.loc[self.nocall_twoothercall_count_df["Shanten"] == shanten_group,turn] += 1

                    if i in self.winner_closed:
                        self.nocall_closedwin_df.loc[self.nocall_closedwin_df["Shanten"] == shanten_group,turn] += 1
                        if callers == 0:
                            self.nocall_noothercall_closedwin_df.loc[self.nocall_noothercall_closedwin_df["Shanten"] == shanten_group,turn] += 1
                        elif callers == 1:
                            self.nocall_oneothercall_closedwin_df.loc[self.nocall_oneothercall_closedwin_df["Shanten"] == shanten_group,turn] += 1
                        else:
                            self.nocall_twoothercall_closedwin_df.loc[self.nocall_twoothercall_closedwin_df["Shanten"] == shanten_group,turn] += 1
                        
                    if i in self.winner_open:
                        self.nocall_openwin_df.loc[self.nocall_openwin_df["Shanten"] == shanten_group,turn] += 1
                        if callers == 0:
                            self.nocall_noothercall_openwin_df.loc[self.nocall_noothercall_openwin_df["Shanten"] == shanten_group,turn] += 1
                        elif callers == 1:
                            self.nocall_oneothercall_openwin_df.loc[self.nocall_oneothercall_openwin_df["Shanten"] == shanten_group,turn] += 1
                        else:
                            self.nocall_twoothercall_openwin_df.loc[self.nocall_twoothercall_openwin_df["Shanten"] == shanten_group,turn] += 1

                    
                if num_calls == 1:
                    self.onecall_count_df.loc[self.onecall_count_df["Shanten"] == shanten_group,turn] += 1
                    if i in self.winner_open:
                        self.onecall_openwin_df.loc[self.onecall_openwin_df["Shanten"] == shanten_group,turn] += 1
                if num_calls >= 2:
                    self.twocall_count_df.loc[self.twocall_count_df["Shanten"] == shanten_group,turn] += 1
                    if i in self.winner_open:
                        self.twocall_openwin_df.loc[self.twocall_openwin_df["Shanten"] == shanten_group,turn] += 1
                
            if turn == turns_considered[-1]:
                self.end_round = True

    def PrintResults(self):
        self.nocall_count_df.to_csv(output, mode='w', index_label='No call total')
        self.nocall_closedwin_df.to_csv(output, mode='a', index_label='No call closed win')
        self.nocall_openwin_df.to_csv(output, mode='a', index_label='No call open win')

        self.nocall_noothercall_count_df.to_csv(output, mode='a', index_label='No call 0 other')
        self.nocall_noothercall_closedwin_df.to_csv(output, mode='a', index_label='No call 0 other closed win')
        self.nocall_noothercall_openwin_df.to_csv(output, mode='a', index_label='No call 0 other open win')

        self.nocall_oneothercall_count_df.to_csv(output, mode='a', index_label='No call 1 other')
        self.nocall_oneothercall_closedwin_df.to_csv(output, mode='a', index_label='No call 1 other closed win')
        self.nocall_oneothercall_openwin_df.to_csv(output, mode='a', index_label='No call 1 other open win')

        self.nocall_twoothercall_count_df.to_csv(output, mode='a', index_label='No call 2, 3 other')     
        self.nocall_twoothercall_closedwin_df.to_csv(output, mode='a', index_label='No call 2, 3 other closed win')   
        self.nocall_twoothercall_openwin_df.to_csv(output, mode='a', index_label='No call 2, 3 other open win')

        self.onecall_openwin_df.to_csv(output, mode='a', index_label='1 call win')
        self.onecall_count_df.to_csv(output, mode='a', index_label='1 call total')

        self.twocall_openwin_df.to_csv(output, mode='a', index_label='2, 3 call win')
        self.twocall_count_df.to_csv(output, mode='a', index_label='2, 3 call total')

        with open(output, "a", encoding="utf8") as f:
            f.write(f",Hands,{self.hand_count}")
    
def initDF(df):
    df = df._append({"Shanten" : "4"}, ignore_index=True) # Any shanten >= 4
    df = df._append({"Shanten" : "3.0"}, ignore_index=True)
    df = df._append({"Shanten" : "3.32"}, ignore_index=True) # Width 32 and up
    df = df._append({"Shanten" : "3.52"}, ignore_index=True)
    df = df._append({"Shanten" : "2.0"}, ignore_index=True)
    df = df._append({"Shanten" : "2.24"}, ignore_index=True)
    df = df._append({"Shanten" : "2.40"}, ignore_index=True)
    df = df._append({"Shanten" : "1.0"}, ignore_index=True)
    df = df._append({"Shanten" : "1.16"}, ignore_index=True)
    df = df._append({"Shanten" : "1.24"}, ignore_index=True)
    df = df._append({"Shanten" : "0.0"}, ignore_index=True)
    df = df._append({"Shanten" : "0.5"}, ignore_index=True)
    df = df._append({"Shanten" : "0.9"}, ignore_index=True)
    df = df.fillna(0)
    return df

def group_shanten(shanten,uke):
    if shanten >= 4: return "4"

    if shanten == 3:
        if uke >= 52: res = "3.52"
        elif uke >= 32: res = "3.32"
        else: res = "3.0"
    if shanten == 2:
        if uke >= 40: res = "2.40"
        elif uke >= 24: res = "2.24"
        else: res = "2.0"
    if shanten == 1:
        if uke >= 24: res = "1.24"
        elif uke >= 16: res = "1.16"
        else: res = "1.0"
    if shanten == 0:
        if uke >= 9: res = "0.9"
        elif uke >= 5: res = "0.5"
        else: res = "0.0"
    return res