---
name: ra2py
description: Read, build, and edit Command & Conquer Red Alert 2 / Yuri's Revenge map files (.map/.yrm/.mpr) with this repo's Python toolkit -- loading/saving maps, building survival maps with scripted enemy waves, defining custom units (a buffed Rhino Tank, a renamed hero infantry, etc.) that inherit from a base unit's full stat block, and reading TibEd .tib preset files to see what a preset actually customizes. Use this whenever the user asks to inspect, generate, or modify a map in this project, add waves or custom units to a map, diff or list what a .tib preset changes, or debug a map that fails to load/save -- don't re-derive this from reading mapio.py/entities.py/logic.py cold, this skill has the parts that took real investigation to get right.
---

# ra2py

A from-scratch parser/serializer and object model for RA2/YR map files, plus
tooling built on top for scripted survival waves, custom units, and reading
TibEd `.tib` preset files. This skill exists so you don't have to re-read
`mapio.py`/`entities.py`/`logic.py` from scratch every session -- it's a
condensed map of what's actually load-bearing, verified against the current
code.

## Mental model

Three different kinds of things live in a map, and the class names encode
which:

- **Placed instances** -- an actual object sitting on the map. `Structure`,
  `Unit`, `Infantry` (entities.py). Has X/Y, House, Strength, etc.
- **Type definitions** -- a custom/modified *kind* of thing, referenced by
  identifier from placed instances. `Building`, `Vehicle`, `InfantryType`
  (entities.py), each with a matching `BuildingTypes`/`VehicleTypes`/
  `InfantryTypes` registry. A definition can either declare a brand-new
  identifier (`declare_type` + `define_type`, gets an auto-assigned index)
  or override an existing standard identifier in place (no declare needed --
  see "in-place overrides" below).
- **Logic/scripting** -- `Trigger`, `Event`, `Action`, `Tag`, `Team`,
  `TaskForce`, `Script`/`ScriptItem` (logic.py). This is RA2's trigger
  system: events fire triggers, triggers run actions, tags gate triggers,
  teams+taskforces define what gets reinforced/spawned.

`Map` (map.py) owns one of everything and knows how to parse
(`load_from_file`) and serialize (`save_to_file`) the whole thing.
`SurvivalMap`/`Wave` (survival.py) is a higher-level helper built on top of
`Map` for the specific case of "spawn timed waves of enemies."

## Loading and saving a map

```python
from map import Map
m = Map()
m.load_from_file("some.yrm")   # or .map / .mpr -- same INI-ish format
m.save_to_file("out.yrm")
```

File encoding is `latin-1`, not UTF-8 -- these are legacy Windows text files
and can contain arbitrary high bytes (accented author names, etc.). Don't
open them with plain `open(path)` in a script; go through `Map`/`MapIO`.

**Always verify a save by reloading it**, not just by checking `save_to_file`
didn't raise. Several real bugs this project had only showed up on the
*second* parse of generated output (a section silently dropped, an `[]`
header emitted where a field was never set) and were invisible if you only
checked that saving didn't crash:

```python
m.save_to_file(out)
Map().load_from_file(out)   # if THIS doesn't raise, you're actually done
```

That still isn't strict enough on its own -- a real bug this project hit (a
trigger's actions silently truncated on serialize) still parsed fine on
reload and only showed up as a structural comparison. Use `verify_round_trip`
after any edit that touches triggers/actions:

```python
from map import Map, verify_round_trip

m = Map()
m.load_from_file("some.yrm")
# ... edits ...
diff = verify_round_trip(m)   # {} means clean; otherwise {trigger_id: (before, after)}
```

It saves `m` to a scratch temp file, reloads it into a fresh `Map`, and diffs
each trigger's action count before vs. after. Because constructing that
fresh `Map` resets the class-level registries (see the "Only one `Map`
session" gotcha below), treat `m` as done-with once you've called this --
don't keep editing it afterward.

## Building a survival map with waves

This is the documented, working pattern (mirrors `test.py`):

```python
from map import Map
from survival import SurvivalMap, Wave
from logic import ScriptItem
from basic import Codes

m = SurvivalMap()                       # attacker=5 by default (House.from_position(5))
m.load_from_file("./empty.yrm")         # empty.yrm is the blank starting template
wps = m.get_waypoints()

attack_script = m.create_script("attack-script")
attack_script.add_action(ScriptItem.create_Attack(1))

spawns = [wps['10']]
wave = Wave("Wave_1_Conscript", 5 * 60, [(Codes.conscript(), 10)], spawns, attack_script)
m.add_wave(wave)

m.save_to_file("./survival.yrm")
```

`Wave(name, delay_seconds, units, waypoints, script, owner=...)` bundles a
`TaskForce` + `Team` + `Trigger`/`Tag` (elapsed-time event, reinforce-by-
chrono action per waypoint) into one call -- that's the "just define a wave"
ergonomics the rest of the custom-content tooling below follows.
`units` is `[(unit_code_or_identifier, amount), ...]` -- `Codes.*` gives
vanilla unit codes, but any declared custom identifier works too.

## Custom units ("a Rhino Tank but tankier")

Don't hand-write a full stat block. Derive a new type from an existing one
(vanilla or another custom type) and only specify what changes -- everything
else is copied from the base:

```python
from tibed import TibPreset
from rules import RulesBaseline
from entities import Vehicle   # or Building, or InfantryType -- same API

baseline = RulesBaseline.from_tib_preset(TibPreset("tibet sets/NukeArtillery.tib"))
# or: RulesBaseline.from_file("path/to/rules.ini")

super_rhino = Vehicle.from_base(baseline, "MTNK", "SUPRHINO", Strength=1000, Primary="APOCSplashBIG")
m.add_vehicle_type(super_rhino)         # declares + defines in one call
```

`Building.from_base`/`Vehicle.from_base`/`InfantryType.from_base` all take
`(baseline, base_identifier, new_identifier, **overrides)` and return a
ready-to-register object. `Map.add_vehicle_type`/`add_building_type`/
`add_infantry_type` each do `declare_type` + `define_type` in one call --
use these instead of calling the registry directly.

A `RulesBaseline` needs a source of *complete* stat blocks to copy from --
either a real `rules.ini` (`RulesBaseline.from_file`) or a TibEd `.tib`
preset's embedded ruleset (`RulesBaseline.from_tib_preset`, see below). If
`base_identifier` isn't in that source, `get_attributes` raises `KeyError`
with a clear message -- that usually means the wrong baseline was picked,
not that the identifier is wrong.

### In-place overrides vs. new custom types

There are two distinct ways a unit ends up "customized" in a map's rules,
and they behave very differently:

1. **A genuinely new identifier**, declared in `[VehicleTypes]`/
   `[BuildingTypes]`/`[InfantryTypes]` and defined in its own section (what
   `from_base` produces). This is what `VehicleTypes.is_vehicle(name)` /
   `.declarations` / `.definitions` actually track.
2. **A standard, always-present identifier's section edited in place**
   (e.g. a `[MTNK]` or `[RMNV]` block sitting in the map with just a few
   overridden fields, reusing the vanilla identifier). This is completely
   legal RA2 rules.ini and works fine in-game, but it is **not** registered
   in any `Types` registry -- `is_vehicle("MTNK")` is `False` even if
   `[MTNK]` has been overridden, because `MTNK` was never declared as a
   custom type; it's just a modification of a permanent one.

This distinction matters in practice: a "list custom units" query via
`get_vehicle_types()`/`get_infantry_types()`/`get_building_types()` will
silently miss type (2). If a user says a tool (TibEd or otherwise) "won't
let me remove" some unit, check whether it's actually in the declarations
list before assuming it's a normal custom entry -- it may be an in-place
override of a standard identifier instead, which most editors don't treat
as deletable the same way.

One more field to sanity-check on any custom/overridden unit: `UIName` must
be `Name:SOMEKEY` (a literal `Name:` prefix on a CSF string-table key), not
a bare value. `UIName=KIM` instead of `UIName=Name:KIM` is exactly the kind
of half-finished edit that shows up in-game as `Missing: 'KIM'`.

## Reading TibEd `.tib` presets

`.tib` files are TibEd's own container format, but the payload is plain:
each one embeds one or more complete, standard-format config files (`Rules`
== rules.ini, `Art` == art.ini, `Sound` == soundmd.ini), zlib-compressed.
`tibed.py` handles the container; the decompressed text is exactly the
`[Section]\nKey=Value\n` shape the rest of this codebase already speaks.

```python
from tibed import TibPreset, diff_presets

p = TibPreset("tibet sets/Dota2.tib")
p.blocks                      # {"Rules": TibBlock, "Art": TibBlock, "Sound": TibBlock}
p.get_block("Rules").sections # {"MTNK": {"Strength": "300", ...}, ...}
p.get_rules()                 # shortcut for get_block("Rules").sections
```

**To find out what a preset actually customizes**, don't diff a single
preset against a generic/external rules.ini -- RA2-vs-YR structural
differences and any unrelated community-mod deltas will swamp the real
signal (confirmed: ~2900 "differences" for one preset against a mismatched
baseline, only ~2 genuinely relevant). Diff presets against **each other**
instead -- it self-cancels all the shared baseline noise with no external
file needed:

```python
presets = [TibPreset(p) for p in glob.glob("tibet sets/*.tib")]
diffs = diff_presets(presets)   # {(section, key): {preset_path: value}}
```

Only `(section, key)` pairs that actually vary across the given presets show
up -- this is what "list custom units in preset X" should be built on. Note
a single `.yrm` map file and the `.tib` preset(s) that produced it can
diverge over time (each save is independent) -- if something's missing from
one, check the other before concluding it doesn't exist.

### Checking map/preset drift directly

Don't eyeball this by hand -- `rules.py` has two functions built from real
bugs found this way (a hero fully designed in a preset but never wired into
the live map; a hero's weapon that existed in the preset but was never
defined in the map, which crashed the game the moment it fired):

```python
from rules import diff_declared_types, find_missing_dependencies

baseline = RulesBaseline.from_tib_preset(TibPreset("tibet sets/Dota2.tib"))
control = RulesBaseline.from_tib_preset(TibPreset("tibet sets/NukeArtillery.tib"))  # any unrelated preset

diff_declared_types(m, baseline)
# {"infantry": {"missing_from_map": [...], "missing_from_baseline": [...],
#               "stat_diffs": {name: {field: (map_value, baseline_value)}}}, ...}

find_missing_dependencies(m, baseline, control_baseline=control)
# {name: {field: {"identifier": str, "definition": dict_or_None}}}
```

`find_missing_dependencies` walks each declared custom type's weapon-ish
fields (`Primary`/`Secondary`/`ElitePrimary`/`EliteSecondary`/`DeathWeapon`
by default) and flags any identifier that resolves nowhere -- **always pass
`control_baseline`** (any preset that isn't specifically about the units
you're checking): without it there's no way to tell a legitimately-missing
vanilla weapon (fine, the engine already knows it) from a genuine gap. When
`definition` comes back non-`None`, the fix is usually just
`Map.add_entity(Serializable(definition, identifier))`.

`diff_declared_types` treats the *map's own* declared list as ground truth
for what counts as "custom" per category (a baseline's `[InfantryTypes]`
etc. mixes vanilla and custom entries together in one list). A stat diff
doesn't always mean the map is wrong -- e.g. a `BuildTimeMultiplier` of
`"0,1"` (comma) in a preset vs `"0.1"` (decimal point) in the live map is
the map having already fixed a locale typo that was never back-ported to
the preset. Read the diff, don't auto-apply it.

### Why a `.tib` preset and the live ruleset can legitimately disagree

There are (at least) four layers a given unit's effective stats can come
from, in increasing priority: the base game's own `.mix` archives (vanilla),
an **installed expansion/mod `.mix`** (e.g. `expandmd01.mix` --
`strings -a` on it shows the real, currently-loaded custom ruleset, which
can be newer/dated later than any `.tib`), a `.tib` preset (a design-time
*snapshot*, edited independently and not automatically kept in sync with
what's installed), and finally the individual map's own embedded per-map
overrides (highest priority, a thin delta on top of whatever's installed).
Confirmed concretely this project: `Dota2.tib` and the actual installed
`expandmd01.mix` ruleset disagree on a few of `BORISWH`'s `Verses` values.
When a preset and the live map disagree and neither looks obviously wrong,
check the installed `.mix` (via `strings -a some.mix | grep -A20
'^\[SECTION\]'` -- there's no proper MIX parser here, but content is stored
largely uncompressed/readable) before assuming either the preset or the map
is the bug.

## File map

| File | What's in it |
|---|---|
| `map.py` | `Map`, `verify_round_trip(m)`, `_reset_global_registries()` (called every `Map()` -- see below) |
| `mapio.py` | `MapIO` -- the actual line-by-line parser/serializer |
| `entities.py` | `Structure`/`Unit`/`Infantry` (placed), `Building`/`Vehicle`/`InfantryType` + their `*Types` registries |
| `logic.py` | `Trigger`, `Event`, `Action`, `Tag`, `Team`, `TaskForce`, `Script`/`ScriptItem` |
| `basic.py` | `Serializable`/`BaseLogic` base classes, `Waypoint`, `StringArray`, `Codes` (vanilla unit code constants) |
| `houses.py` | `House` (per-faction singleton, e.g. `House.get_house("Americans")`, `House.PlayerE()`, `House.from_position(n)`) |
| `survival.py` | `SurvivalMap`, `Wave` |
| `tibed.py` | `TibPreset`, `TibBlock`, `parse_ini`, `diff_presets` -- `.tib` loader |
| `rules.py` | `RulesBaseline` -- stat-block lookup for `*.from_base(...)` |
| `factories.py` | `GlobalTriggers` -- a couple of reusable trigger factories (small, thin) |
| `actions.py` | `RA2Actions` -- static reference table of action-type IDs/args, documentation only |

## Gotchas worth knowing before you debug them yourself

- **Only one `Map` "session" at a time.** `Map.__init__` resets several
  class-level ID counters/registries (`Waypoint`, `Building`, `Vehicle`,
  `InfantryType`, `Tag`, `Team`, `TaskForce`, `Script`, `House`, and the
  shared `BaseLogic.id_counter`) so that loading/building maps back-to-back
  in one process doesn't leak IDs or objects between them. This means
  building/loading maps **sequentially** is safe, but holding two `Map`
  objects open and interleaving edits to both is not supported -- creating
  the second `Map()` resets state out from under the first.
- **Waypoints encode as `X*1000 + Y`** (Y zero-padded to 3 digits), not a
  fixed-width digit split. Don't hand-roll waypoint math; use `Waypoint`
  and `map.get_waypoints()`/`get_waypoint_by_id()`.
- **Events can have a variable number of fields.** Most trigger events are
  `(Type, P1, P2)`, but some carry a 4th field, and which position holds a
  non-numeric value (an object-type string) isn't fixed either. The parser
  handles this by peeking rather than assuming a fixed width -- if you're
  hand-constructing an `Event`, don't assume exactly 3 keys.
- **A `Tag == 'None'`/blank-reference check is required** wherever a parsed
  CSV row has an optional Tag/Owner/Prerequisite/RequiredHouses field --
  real-world maps routinely have dangling or blank references (a deleted
  trigger's tag ID still referenced by a structure, an empty `Owner=` on an
  unbuildable unit). Fail soft (log + leave unlinked), don't assume every
  reference resolves.
