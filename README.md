# Houou statistics analyses

Riichi Mahjong data analysis project to gather statistics for improving my play, by looking at thousands of tenhou replays. Forked from https://github.com/Euophrys/houou-analysis.

## Installation

Install requirements with `pip install -r requirements.txt`.

Download database of tenhou logs separately here, and merge together only 4-player hanchans: https://drive.google.com/drive/u/0/folders/1danHelDPYF2YP9Er2HhJCemlVQN25nb_. 

Place the merged database in the data folder. From 5 years there are 893,440 logs, but I rarely need more than 20,000 to get a large enough sample size.

The XML logs format is explained here: https://github.com/ApplySci/tenhou-log#log-format.

## Contents

All the results have been compiled into `Houou statistics compiled.xlsx`. Look at this file if you only want to see the statistics.

`app.py` is the entry point for the program, change the `Analyzer` in app.py to any analyzer in `/analyzers` to gather data. Raw data are printed into `/results`. Change `rowcount` to adjust the sample size.

Each analyzer inherits `log_hand_analyzer.py`, which includes common functions like decoding hands, calls, points, dora, riichis and turn. `log_hand_analyzer.py` includes empty functions that are called when a tile is drawn, discarded, called, riichi, etc. These empty functions are overrided when needed to analyse the game at any specific point.

+ `/util/analysis_utils.py` includes common functions that are used in every analysis
+ `/util/shanten.py` contains the algorithm used to calculate shanten and ukeire
+ `/util/placement_calculator.py` is a meta-analysis of score utility used to generate `CoinflipRatio.csv`.

## List of analyses

+ **Riichi Hand**: Properties of a riichi by turn, riichi tile, discards and tsumogiri riichi: good wait %, tanyao %, amount of dora
+ **Hand Score**: Average hand scores by yaku, turn, dealin tile, dora discarded and tsumo/ron.
+ **Betaori Cost**: Average points lost upon folding based on turn, number of riichis, and whether you're the dealer.
+ **Wait Distribution**: Distribution of waits for riichi and open hands.
+ **Riichi Tile**: Change in danger level by tile used to call riichi.
+ **Sotogawa**: Change in danger level by tiles discarded prior to riichi.
+ **Dora Danger**: Increase in danger level of dora and tiles close to dora.
+ **Riichi Winrate**: Win, draw and dealin rates for 1st, 2nd and 3rd riichi based on turn and hand shape.
+ **Dama Winrate**: Estimating dama winrate by counting tiles discarded without any seemingly dangerous players.
+ **Oikake Calculator**: EV calculator for chasing a riichi.
+ **1-shanten Calculator**: EV calculator for pushing in 1-shanten against a riichi.
+ **Keiten Calculator**: EV calculator for pushing a no yaku hand to keiten.
+ **Open Tenpai**: Tenpai chance by number of calls, turn, yaku, kan, type of call, tedashi/tsumogiri, dora discards and joint discards.
+ **Tedashi Reading**: Tedashi effect on hand shanten and shape, chance that final wait is around previous tedashi, and chance of dora pair given dorasoba tedashi.
+ **Shanten & Width**: Shanten and ukeire of hands based on turn and number of calls.
+ **Projected Winrate**: Projected chance of winning a hand based on shanten, shape, turn, and number of open opponents. Includes EV calculator for opening your hand.
+ **Wall Reading**: Average number of a tile or a suit in the wall, depending on the amount that opponents discarded.
+ **Skipping Yakuhai**: Rate of Houou players calling yakuhai pairs, based on hand speed and value.
+ **Atozuke**: Chance to complete a yakuhai pair into a triplet depending on the type fo yakuhai and whether you atozuke.
+ **Hand Outcome**: Distribution of hand outcomes (Win by how much, call rate, riichi rate, whether tenpai at draw, deal in %, lateral movement, opponent tsumo) based on round and player's position.
+ **Score Variance**: Standard deviation of final score given current score and rounds left.
+ **Coinflips**: Utility of taking a coinflip (50% to gain 8000, 50% to lose 8000) on rating points based on round and point situation.