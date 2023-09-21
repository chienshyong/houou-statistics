from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree

# When a player with at least 1 call gets to tenpai, check the suit of the wait and calls of the hand.
# Once/Twice Called Suit only for the 2 same 1 diff case: refers to the 1 diff suit
call_classes = ["2 Suits", "2 Suits 1 Honor", "2 Same Suit 1 Diff Suit"]
wait_classes = ["Same Suit", "Twice Called Suit", "Once Called Suit", "Different Suit", "Multiple Suit/Honor"]

class Mentanpin(LogHandAnalyzer):
    def __init__(self):
        super().__init__()

        self.tenpai = [False, False, False, False] #Flag for tenpai. Only check each player once.
        self.callwait = [(None, None), (None, None), (None, None), (None, None)] #Tuple of (call, wait) to store results

        # Append it to a big dictionary at the end of each hand
        # counts[call][wait] = ?
        self.counts = defaultdict(Counter)

    def ParseLog(self, log, log_id):
        # print(f"Parsing log {log_id}")
        super().ParseLog(log, log_id)

    def RoundStarted(self, init):
        super().RoundStarted(init)
        self.tenpai = [False, False, False, False]
        self.callwait = [(None, None), (None, None), (None, None), (None, None)]

    def TileDiscarded(self, who, tile, tsumogiri, element):
        super().TileDiscarded(who, tile, tsumogiri, element)
        if(len(self.calls[who]) >= 2) and not self.tenpai[who]:
            if sh.isTenpai(self.hands[who]):
                self.tenpai[who] = True
                ukeire, utiles = sh.calculateUkeire(self.hands[who], self.calls[who], baseShanten = 0)

                # print(f"\n{who} is tenpai, hand : {ut.parseAmberNotation(self.hands[who], self.calls[who])}")
                # print(f"Waiting on {ut.parseAmberNotation(list=utiles)}")

                callsuits = []
                waitsuits = []
                
                for call in self.calls[who]:
                    callsuits.append(call[0]//10)
                # print(f"Called in suits {callsuits}")

                for utile in utiles:
                    waitsuits.append(utile//10)
                # print(f"Waiting in suits {waitsuits}")

                self.callwait[who] = getCallWait(callsuits,waitsuits)
                # print(self.callwait[who])

    def RoundEnded(self, init):
        super().RoundEnded(init)
        for cw in self.callwait:
            if cw != (None, None):
                self.counts[cw[0]][cw[1]] += 1

    def PrintResults(self):
        with open("./results/Mentanpin.csv", "w", encoding="utf8") as f:
            f.write("Wait,2 Suits,2 Suits 1 Honor\n")

            f.write("%s," % "Same Suit")
            f.write("%d," % self.counts["2 Suits"]["Same Suit"])
            f.write("%d," % self.counts["2 Suits 1 Honor"]["Same Suit"])
            f.write("\n")
            f.write("%s," % "Different Suit")
            f.write("%d," % self.counts["2 Suits"]["Different Suit"])
            f.write("%d," % self.counts["2 Suits 1 Honor"]["Different Suit"])
            f.write("\n")
            f.write("%s," % "Multiple Suit/Honor")
            f.write("%d," % self.counts["2 Suits"]["Multiple Suit/Honor"])
            f.write("%d" % self.counts["2 Suits 1 Honor"]["Multiple Suit/Honor"])
            f.write("\n\n")

            f.write("Wait,2 Same Suit 1 Diff Suit\n")
            f.write("%s," % "Twice Called Suit")
            f.write("%d," % self.counts["2 Same Suit 1 Diff Suit"]["Twice Called Suit"])
            f.write("\n")
            f.write("%s," % "Once Called Suit")
            f.write("%d," % self.counts["2 Same Suit 1 Diff Suit"]["Once Called Suit"])
            f.write("\n")
            f.write("%s," % "Different Suit")
            f.write("%d," % self.counts["2 Same Suit 1 Diff Suit"]["Different Suit"])
            f.write("\n")
            f.write("%s," % "Multiple Suit/Honor")
            f.write("%d," % self.counts["2 Same Suit 1 Diff Suit"]["Multiple Suit/Honor"])
            f.write("\n")

def getCallWait(callsuits, waitsuits):
    if len(callsuits) < 2:
        return (None, None)
    
    callclass = None
    if len(callsuits) == 2:
        if 3 in callsuits or callsuits[0] == callsuits[1]: #If either is an honor or if it's the same suit, don't count
            return (None, None)
        else:
            callclass = "2 Suits"

    if len(callsuits) == 3 and callsuits.count(3) < 2:
        unique = len(set(callsuits))
        if callsuits.count(3) == 1:
            if unique == 3:
                callclass = "2 Suits 1 Honor"
        if callsuits.count(3) == 0:
            if unique == 2:
                callclass = "2 Same Suit 1 Diff Suit"

    if callclass == None:
        return (None, None)

    waitclass = None
    if waitsuits.count(3) == len(waitsuits):
        waitclass = "Multiple Suit/Honor"
    elif waitsuits.count(3) >= 1:
        waitsuits = [i for i in waitsuits if i != 3] # Shanpon on honor, remove it and continue calculating.
        
    if all(i == waitsuits[0] for i in waitsuits):
        if waitsuits[0] == 3:
            waitclass = "Multiple Suit/Honor"
        elif waitsuits[0] in callsuits:
            waitclass = "Same Suit"
            if callclass == "2 Same Suit 1 Diff Suit":
                if callsuits.count(waitsuits[0]) == 1:
                    waitclass = "Once Called Suit"
                else:
                    waitclass = "Twice Called Suit"
        else:
            waitclass = "Different Suit"
    else:
        waitclass = "Multiple Suit/Honor"

    return (callclass, waitclass)
