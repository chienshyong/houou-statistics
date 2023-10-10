from .log_analyzer import LogAnalyzer
from util.analysis_utils import convertHai, convertTile, convertTileCheckAka, discards, draws, GetNextRealTag, GetStartingHands, getTilesFromCall, GetDora
from abc import abstractmethod

# Analyzer template that takes care of all the annoying work of gathering hands, discards, and calls. 
# Has empty functions to override as needed. eg. if need riichi data, override RiichiCalled

class LogHandAnalyzer(LogAnalyzer):
    def __init__(self):
        self.current_log_id = ""
        self.hands = [[], [], [], []] # Stores the hands, calls, discards for one hand only, from 0th to 3rd player.
        self.aka = [-1, -1, -1] # Who has drawn the akadora (5, 15, 25). If they have it in winning hand just assume it's aka.
        self.calls = [[], [], [], []]
        self.discards = [[], [], [], []] # Define turn as len(self.discards[(self.oya-1)%4])
        self.last_draw = [50,50,50,50]
        self.end_round = False # Can set this manually to go next log

        self.round = [0,0] # East 1 honba 1 = [0,1]
        self.oya = 0
        self.scores = [[],[],[],[]]
        self.dora = []

    def ParseLog(self, log, log_id):
        self.current_log_id = log_id
        for round_ in log.iter("INIT"):
            self.PlayRound(round_)
        self.ReplayComplete()

    def PlayRound(self, round_):
        self.RoundStarted(round_)

        for element in round_.itersiblings():
            if self.end_round: break

            if element.tag == "DORA":
                self.DoraRevealed(element.attrib["hai"], element)

            elif element.tag[0] in discards:
                who = ord(element.tag[0]) - 68
                tile = convertTile(element.tag[1:])
                self.TileDiscarded(who, tile, tile == self.last_draw[who], element)

            elif element.tag == "UN":
                self.Reconnection(element)
                
            elif element.tag[0] in draws:
                who = ord(element.tag[0]) - 84
                tile, aka = convertTileCheckAka(element.tag[1:])
                if aka != None:
                    self.aka[aka] = who
                self.last_draw[who] = tile
                self.TileDrawn(who, tile, element)

            elif element.tag == "N":
                self.TileCalled(int(element.attrib["who"]), getTilesFromCall(element.attrib["m"]), element)
            
            elif element.tag == "REACH":
                self.RiichiCalled(int(element.attrib["who"]), int(element.attrib["step"]), element)

            elif element.tag == "AGARI":
                self.Win(element)
                break
            
            elif element.tag == "RYUUKYOKU":
                if "type" in element.attrib:
                    self.AbortiveDraw(element)
                else:
                    self.ExhaustiveDraw(element)
                break

            elif element.tag == "BYE":
                self.Disconnection(element)

        self.RoundEnded(round_)
    
    def RoundStarted(self, init):
        self.hands, self.aka = GetStartingHands(init) 
        self.calls = [[], [], [], []]
        self.discards = [[], [], [], []]
        self.end_round = False

        self.dora = []
        self.dora.append(GetDora(convertTile(init.attrib["seed"].split(',')[5])))
        self.round = init.attrib["seed"].split(',')[:2]
        self.round = [int(i) for i in self.round]
        self.scores = init.attrib["ten"].split(',')
        self.scores = [int(i) for i in self.scores]
        self.oya = int(init.attrib["oya"])
    
    def DoraRevealed(self, hai, element):
        self.dora.append(GetDora(convertTile(int(hai))))

    def TileDiscarded(self, who, tile, tsumogiri, element):
        self.hands[who][tile] -= 1
        self.discards[who].append(tile)

    def TileDrawn(self, who, tile, element):
        self.hands[who][tile] += 1

    def TileCalled(self, who, tiles, element):
        length = len(tiles)
        if length == 1:
            self.hands[who][tiles[0]] -= 1
        elif length == 4:
            self.hands[who][tiles[0]] = 0
        else:
            self.hands[who][tiles[1]] -= 1
            self.hands[who][tiles[2]] -= 1
        self.calls[who].append(tiles)

    def RiichiCalled(self, who, step, element):
        pass

    def RoundEnded(self, init):
        pass

    def Win(self, element):
        pass

    def ExhaustiveDraw(self, element):
        pass

    def AbortiveDraw(self, element):
        pass

    def ReplayComplete(self):
        pass

    def Disconnection(self, element):
        pass

    def Reconnection(self, element):
        pass
    
    def PrintResults(self):
        pass