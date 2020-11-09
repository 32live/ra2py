# ra2py - Red Alert 2 / Yuris Revenge mod python API
## Mapping API for Command & Conquer: Red Alert 2 / Yuris Revenge maps
This is a simple collection of wrappers and data classes to help create maps for the Command and Conquer RA2 games.
MapIO contains functionality for reading and writing .yrm or .map files.
The goal of this project was to easily add waves to survival maps.

Here is a code example from test.py:
```from mapio import MapIO
from entities import Infantry
from basic import StringArray, Codes
from map import Map
from logic import *
from survival import SurvivalMap, Wave
import sys
import houses

m = SurvivalMap()
m.load_from_file("./empty.yrm")
wps = m.get_waypoints()

attack_script = m.create_script("attack-script")
attack_script.add_action(ScriptItem.create_Attack(1))

spawns = [wps['10']]

waves = []
waves.append(Wave("Wave_1_Conscript", 5 * 60, [(Codes.conscript(), 10)], spawns, attack_script))
waves.append(Wave("wave_2_initiates", 8 * 60, [(Codes.initiate(), 10)], spawns, attack_script))
waves.append(Wave("wave_3_dogs+yuris", 11 * 60, [(Codes.attack_dog(), 10), (Codes.yuri_clone(), 10)], spawns, attack_script))
waves.append(Wave("wave_4_rhinos", 14 * 60, [(Codes.rhino_tank(), 10)], spawns, attack_script))
waves.append(Wave("wave_5_chaos&terror", 17 * 60, [(Codes.chaos_drone(), 10),(Codes.terror_drone(), 10)], spawns, attack_script))
for wave in waves:
    m.add_wave(wave)

m.save_to_file("./survival.yrm")
```

It will load the map 'empty.yrm' and create a survival map from it. It will then add 5 different waves to it and save it to 'survival.yrm' in the same directory.
Only a small amount of functionality was tested, save your map to a different file to prevent potential corruption.
