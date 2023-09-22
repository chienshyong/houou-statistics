from analyzers.log_hand_analyzer import LogHandAnalyzer
from collections import defaultdict, Counter
import util.analysis_utils as ut
import util.shanten as sh
from lxml import etree
import time

class ShantenBenchmark(LogHandAnalyzer):
    def __init__(self):
        super().__init__()
        self.calculations = 0
        self.mistakes = 0
        self.originalspeed = 0
        self.newspeed = 0

    def TileDiscarded(self, who, tile, tsumogiri, element):
        super().TileDiscarded(who, tile, tsumogiri, element)
        # print(f"\n New hand: {self.hands[who]}")
        t1 = time.perf_counter()
        shanten = sh.calculateStandardShanten(self.hands[who])
        self.originalspeed += time.perf_counter() - t1
        t1 = time.perf_counter()
        shanten2 = sh.calculateStandardShantenBacktrack(self.hands[who])
        self.newspeed += time.perf_counter() - t1
        self.calculations += 1
        if shanten != shanten2:
            self.mistakes += 1
            print(f"\n{self.hands[who]} does not match: correct {shanten} new {shanten2}")
            print(ut.parseAmberNotation(self.hands[who]))

    def PrintResults(self):
        super().PrintResults()
        print(f"{self.calculations} hands calculated with {self.mistakes} mistakes.")
        print(f"Old algorithm: {round(self.originalspeed,2)} seconds")
        print(f"New algorithm: {round(self.newspeed,2)} seconds")