from .log_hand_analyzer import LogHandAnalyzer
from analysis_utils import GetDora, convertTile, yaku_names
from collections import defaultdict, Counter

# Reference analyzer from https://github.com/Euophrys/phoenix-logs/tree/develop
# Counts the tile types in the discard pool depending on the Yaku

terminal_tiles = [1,9,11,19,21,29]
two_eight_tiles = [2,8,12,18,22,28]

class PondTraits(LogHandAnalyzer):
    def __init__(self):
        super().__init__()
        # Keep variables for each hand
        self.tsumogiri = [0,0,0,0]
        self.first_discards = [0,0,0,0]
        self.dora = []
        self.dora_discarded = [0,0,0,0]
        self.discards_at_riichi = [[],[],[],[]]
        # Append it to a big dictionary at the end of each hand
        # Then print the dictionary at the end.
        self.counts = defaultdict(Counter)

    def RoundStarted(self, init):
        super().RoundStarted(init)
        self.tsumogiri = [0,0,0,0]
        self.first_discards = [0,0,0,0]
        self.dora_discarded = [0,0,0,0]
        self.discards_at_riichi = [[],[],[],[]]
        self.dora = [GetDora(convertTile(init.attrib["seed"].split(",")[5]))]

    def DoraRevealed(self, hai, element):
        super().DoraRevealed(hai, element)
        self.dora.append(GetDora(convertTile(hai)))

    def TileDiscarded(self, who, tile, tsumogiri, element):
        if self.discards_at_riichi[who]:
            return super().TileDiscarded(who, tile, tsumogiri, element)

        if tsumogiri:
            self.tsumogiri[who] += 1
        
        first = True

        for i in range(4):
            if tile in self.discards[i]:
                first = False
                break
            for call in self.calls[i]:
                if tile in call:
                    first = False
                    break

        if tile in self.dora:
            first = False

        if first:
            self.first_discards[who] += 1
        
        if tile in self.dora:
            self.dora_discarded[who] += 1

        super().TileDiscarded(who, tile, tsumogiri, element)

    def RiichiCalled(self, who, step, element):
        super().RiichiCalled(who, step, element)
        if step == 2: return

        self.discards_at_riichi[who] = self.discards[who].copy()

    def Win(self, element):
        super().Win(element)
        who = int(element.attrib["who"])
        if len(self.discards_at_riichi[who]) < 8: return

        yaku = []

        if "yaku" in element.attrib:
            yaku = [int(x) for x in element.attrib["yaku"].split(",")[0::2]]
        else:
            yaku = [int(x) for x in element.attrib["yakuman"].split(",")[0::2]]

        tile_counts = Counter(self.discards_at_riichi[who])

        terminals = 0
        two_eights = 0
        middles = 0
        honors = 0
        pairs = 0
        suits = [0, 0, 0]

        for tile in tile_counts:
            if tile > 30:
                honors += tile_counts[tile]
            else:
                suits[int(tile / 10)] += tile_counts[tile]

                if tile in terminal_tiles:
                    terminals += tile_counts[tile]
                elif tile in two_eight_tiles:
                    two_eights += tile_counts[tile]
                else:
                    middles += tile_counts[tile]
            
            if tile_counts[tile] > 1:
                pairs += 1

        suits.sort()
        
        for i in yaku:
            name = yaku_names[i]
            self.counts[name]["Discards"] += len(self.discards_at_riichi[who])
            self.counts[name]["Dora"] += self.dora_discarded[who]
            self.counts[name]["First"] += self.first_discards[who]
            self.counts[name]["Tsumogiri"] += self.tsumogiri[who]
            self.counts[name]["1/9"] += terminals
            self.counts[name]["2/8"] += two_eights
            self.counts[name]["Middle"] += middles
            self.counts[name]["Honors"] += honors
            self.counts[name]["Pairs"] += pairs
            self.counts[name]["Suit 1"] += suits[0]
            self.counts[name]["Suit 2"] += suits[1]
            self.counts[name]["Suit 3"] += suits[2]

    def PrintResults(self):
        with open("./results/PondTraits.csv", "w", encoding="utf8") as f:
            f.write("Yaku,Discards,1/9,2/8,Middle,Honors,Suit 1,Suit 2,Suit 3,Pairs,Dora,Live,Tsumogiri\n")

            for yaku in self.counts:
                f.write("%s," % yaku)
                f.write("%d," % self.counts[yaku]["Discards"])
                f.write("%d," % self.counts[yaku]["1/9"])
                f.write("%d," % self.counts[yaku]["2/8"])
                f.write("%d," % self.counts[yaku]["Middle"])
                f.write("%d," % self.counts[yaku]["Honors"])
                f.write("%d," % self.counts[yaku]["Suit 1"])
                f.write("%d," % self.counts[yaku]["Suit 2"])
                f.write("%d," % self.counts[yaku]["Suit 3"])
                f.write("%d," % self.counts[yaku]["Pairs"])
                f.write("%d," % self.counts[yaku]["Dora"])
                f.write("%d," % self.counts[yaku]["First"])
                f.write("%d," % self.counts[yaku]["Tsumogiri"])
                f.write("\n")