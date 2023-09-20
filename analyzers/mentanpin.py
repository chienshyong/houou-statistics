from .log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree

# When a player with at least 1 call gets to tenpai, check the suit of the wait of the hand. Ignore honors.
# Start with 2 call cases
call_classes = ["1 Suit", "1 Honor", "2 Same Suit", "2 Different Suits", "1 Suit 1 Honor", "2 Honors"]
wait_classes = ["Same Suit", "Different Suit", "Multiple Suit/Honor"]

class Mentanpin(LogHandAnalyzer):
    def __init__(self):
        super().__init__()

        self.tenpai = [False, False, False, False] #Flag for tenpai. Only check each player once.
        self.callwait = [(None, None), (None, None), (None, None), (None, None)] #Tuple of (call, wait) to store results

        # Append it to a big dictionary at the end of each hand
        # counts[call][wait] = ?
        self.counts = defaultdict(Counter)

    def ParseLog(self, log, log_id):
        print(f"Parsing log {log_id}")
        super().ParseLog(log, log_id)

    def RoundStarted(self, init):
        super().RoundStarted(init)
        input("\nInput for next hand")
        self.tenpai = [False, False, False, False]
        self.callwait = [(None, None), (None, None), (None, None), (None, None)]

    def TileDiscarded(self, who, tile, tsumogiri, element):
        super().TileDiscarded(who, tile, tsumogiri, element)
        if sh.isTenpai(self.hands[who], self.calls[who]):
            if not self.tenpai[who]:
                self.tenpai[who] = True
                ukeire, utiles = sh.calculateUkeire(self.hands[who], self.calls[who])

                print(f"\n{who} is tenpai, hand : {ut.parseAmberNotation(self.hands[who], self.calls[who])}")
                print(f"Waiting on {ut.parseAmberNotation(list=utiles)}")

                if(len(self.calls[who]) != 0):
                    callsuits = []
                    waitsuits = []
                    
                    for call in self.calls[who]:
                        callsuits.append(call[0]//10)
                    print(f"Called in suits {callsuits}")

                    for utile in utiles:
                        waitsuits.append(utile//10)
                    print(f"Waiting in suits {waitsuits}")

                    self.callwait[who] = getCallWait(callsuits,waitsuits)
                    print(self.callwait[who])
                else:
                    print(f"But didn't call, skip")

    def PrintResults(self):
        pass

def getCallWait(callsuits, waitsuits):
    if len(callsuits) == 0:
        return (None, None)
    
    callclass = None
    if len(callsuits) == 1:
        if callsuits[0] == 3:
            callclass = "1 Honor"
        else:
            callclass = "1 Suit"
    if len(callsuits) == 2:
        if callsuits[0] == callsuits[1]:
            if callsuits[0] == 3:
                callclass = "2 Honors"
            else:
                callclass = "2 Same Suit"
        else:
            if callsuits[0] == 3 or callsuits[1] == 3:
                callclass = "1 Suit 1 Honor"
            else:
                callclass = "2 Different Suits"
    if len(callsuits) >= 3: #TO BE IMPLEMENT
        callclass = "2 Different Suits"

    waitclass = None
    if all(i == waitsuits[0] for i in waitsuits):
        if waitsuits[0] == 3:
            waitclass = "Multiple Suit/Honor"
        elif waitsuits[0] in callsuits:
            waitclass = "Same Suit"
        else:
            waitclass = "Different Suit"
    else:
        waitclass = "Multiple Suit/Honor"

    return (callclass, waitclass)
