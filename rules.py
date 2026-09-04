"""
    Baseline rules.ini stat lookups, used to derive custom units/buildings/
    infantry that inherit every field from an existing type and only
    override a few -- e.g. a Rhino Tank with more health but everything
    else left at its default.

    A baseline can come from a plain rules.ini file, or from a TibEd .tib
    preset's embedded Rules block (see tibed.py) -- either way it ends up
    as the same {section: {key: value}} shape.
"""
from tibed import parse_ini


class RulesBaseline():
    """ Full stat blocks to derive custom types from """
    def __init__(self, sections):
        self.sections = sections

    @classmethod
    def from_file(cls, path):
        """ Load a plain rules.ini file """
        with open(path, 'r', encoding='latin-1') as f:
            return cls(parse_ini(f.read()))

    @classmethod
    def from_tib_preset(cls, preset, block_label='Rules'):
        """ Load from an already-opened tibed.TibPreset """
        block = preset.get_block(block_label)
        return cls(block.sections if block else {})

    def get_attributes(self, identifier):
        """
            A copy of the complete attribute dict for an existing (base)
            unit/building/infantry identifier, e.g. "MTNK" for the Rhino
            Tank. Raises KeyError if this baseline has no such section.
        """
        if identifier not in self.sections:
            raise KeyError(
                "no baseline definition for '{}' -- check the identifier "
                "or try a different baseline source".format(identifier))
        return dict(self.sections[identifier])

    def sync_from_map(self, map_obj, *identifiers):
        """
            Patch this baseline's entries for `identifiers` with their
            CURRENT state from `map_obj`, in place. Use before deriving a
            new type (via from_base) from a base that's been customized
            directly on the live map since this baseline's own source
            (e.g. a .tib preset) was last touched -- without this,
            from_base() would silently derive from the stale preset
            version instead of what's actually live.

            Real case this fixes: this project's "Cowboy 2"/"Cowboy 3"
            needed to derive from CLNT's live, hand-customized hero stats
            (Strength/ElitePrimary/etc), not Dota2.tib's own CLNT, which
            was still the unmodified civilian placeholder it started as --
            the preset was never updated after CLNT got hero-ified
            directly on the map.

            Silently does nothing for an identifier map_obj has no entity
            for -- callers deriving from a genuinely vanilla-only base
            (never touched on the live map) don't need to special-case
            that.
        """
        live = {e.get_header(): e for e in map_obj.entities}
        for identifier in identifiers:
            if identifier in live:
                self.sections[identifier] = dict(live[identifier].attributes)


# Standard vanilla type counts (matches Building.index/Vehicle.index/
# InfantryType.index's starting values in entities.py). A [BuildingTypes]/
# [VehicleTypes]/[InfantryTypes] declaration list mixes standard and custom
# entries together, and only the *starting* class-level index reflects
# where "standard" ends -- by the time a Map has been loaded, those class
# attributes have already been incremented past it by every instance
# created, so the thresholds are hardcoded here rather than read live.
_CUSTOM_TYPE_THRESHOLD = {"building": 407, "vehicle": 200, "infantry": 66}

# The category name used here (map_obj.get_X_types()) and the attribute in
# a baseline's own [XTypes] declaration list share this suffix.
_TYPES_SECTION = {"building": "BuildingTypes", "vehicle": "VehicleTypes", "infantry": "InfantryTypes"}


def _custom_names_in_baseline(baseline, category):
    """ Names in baseline's own [XTypes] list whose index is past the standard-type threshold """
    section = baseline.sections.get(_TYPES_SECTION[category], {})
    threshold = _CUSTOM_TYPE_THRESHOLD[category]
    names = set()
    for idx_str, name in section.items():
        try:
            if int(idx_str) >= threshold:
                names.add(name)
        except ValueError:
            continue
    return names


def diff_declared_types(map_obj, baseline, categories=("building", "vehicle", "infantry")):
    """
        Compare a loaded Map's declared custom Building/Vehicle/InfantryType
        entries against a RulesBaseline (e.g. from a .tib preset) -- catches
        the single most common bug seen while developing this map: a custom
        type designed in a preset that never actually got wired into the
        live map (or the reverse -- wired into the map but no longer/never
        in the preset), plus any case where the same identifier's stats
        have drifted apart between the two.

        Returns {category: {"missing_from_map": [...], "missing_from_baseline": [...],
                             "stat_diffs": {name: {field: (map_value, baseline_value)}}}}
        An empty dict for a category means no drift found.
    """
    getters = {
        "building": map_obj.get_building_types,
        "vehicle": map_obj.get_vehicle_types,
        "infantry": map_obj.get_infantry_types,
    }
    result = {}
    for category in categories:
        registry = getters[category]()
        map_declared = set(registry.declarations)
        baseline_declared = _custom_names_in_baseline(baseline, category)

        missing_from_map = sorted(baseline_declared - map_declared)
        missing_from_baseline = sorted(map_declared - baseline_declared)

        stat_diffs = {}
        for name in sorted(map_declared & baseline_declared):
            map_attrs = registry.definitions[name].attributes
            baseline_attrs = baseline.sections.get(name, {})
            diff = {
                field: (map_attrs.get(field), baseline_attrs.get(field))
                for field in set(map_attrs) | set(baseline_attrs)
                if map_attrs.get(field) != baseline_attrs.get(field)
            }
            if diff:
                stat_diffs[name] = diff

        if missing_from_map or missing_from_baseline or stat_diffs:
            result[category] = {
                "missing_from_map": missing_from_map,
                "missing_from_baseline": missing_from_baseline,
                "stat_diffs": stat_diffs,
            }
    return result


def find_required_houses(map_obj, categories=("building", "vehicle", "infantry")):
    """
        Scan EVERY entity in map_obj for a RequiredHouses field -- both
        generic in-place overrides (map_obj.entities, e.g. a vanilla
        identifier like SNIPE/TANY/CLNT customized directly rather than
        declared as a new type) and declared custom Building/Vehicle/
        InfantryType entries.

        Checking only get_X_types().declarations (as an earlier survey on
        this project did) misses in-place overrides entirely -- that's
        exactly how three already-finished heroes (CLNT/ARND/TANY, all
        in-place overrides of vanilla identifiers, none of them a newly
        declared type) went undetected for a full session, wrongly
        concluding their houses had no hero yet.

        Returns {required_houses_value: [identifier, ...]}. Keyed by the
        raw RequiredHouses string as it appears (a single house, or a
        comma-separated list) -- split on "," yourself if you want
        per-house grouping for a multi-house value.
    """
    getters = {
        "building": map_obj.get_building_types,
        "vehicle": map_obj.get_vehicle_types,
        "infantry": map_obj.get_infantry_types,
    }

    by_house = {}

    def _record(identifier, attrs):
        required = attrs.get("RequiredHouses")
        if required:
            by_house.setdefault(required, []).append(identifier)

    for e in map_obj.entities:
        _record(e.get_header(), e.attributes)

    for category in categories:
        registry = getters[category]()
        for name, obj in registry.definitions.items():
            _record(name, obj.attributes)

    return by_house


# Attribute names commonly holding a reference to another section
# (a weapon, in practice) on a Building/Vehicle/InfantryType. Not
# exhaustive -- pass `fields=` to check others.
DEPENDENCY_FIELDS = ("Primary", "Secondary", "ElitePrimary", "EliteSecondary", "DeathWeapon")

# Attribute names on a WEAPON (not the unit) holding a reference to
# another section -- checked one level deeper than DEPENDENCY_FIELDS, see
# find_missing_dependencies.
WEAPON_DEPENDENCY_FIELDS = ("Warhead",)


def find_missing_dependencies(map_obj, baseline, control_baseline=None,
                               fields=DEPENDENCY_FIELDS, weapon_fields=WEAPON_DEPENDENCY_FIELDS):
    """
        For every declared custom Building/Vehicle/InfantryType in map_obj,
        walk `fields` and check whether each referenced identifier actually
        resolves to something -- either already present in the map (a
        generic entity, or another declared custom type), or present in
        `control_baseline` (meaning it's a standard/vanilla identifier the
        game engine already knows, safe to leave undefined in the map).

        Most weapon references are standard vanilla content and don't need
        a `control_baseline` hit to be "fine" -- but without one, this
        can't tell a legitimately-undefined vanilla weapon from a genuine
        gap, so it's strongly recommended: pass a RulesBaseline built from
        a generic, non-custom preset (anything that isn't specifically
        about the units you're checking) to filter that noise out, the
        same way a real AKMEE/AWPEE gap was found by checking it was
        absent even from an unrelated preset.

        Also walks one level deeper: for every weapon identifier reached
        via `fields` that DOES resolve, follows `weapon_fields` (its own
        Warhead reference, by default) and checks that too. The original
        AKMEE crash was a unit->weapon gap; a later investigation (Sammy
        Stallion/the original Boris crash, both traced to a shared
        EliteSecondary weapon's Warhead=NukeB -- the Nuclear Missile
        superweapon's own warhead, reused as a regular infantry attack)
        showed a weapon->warhead reference can be exactly as dangerous,
        one hop further down the chain than this function used to look.

        Returns {name: {field_path: {"identifier": str, "definition": dict_or_None}}}
        -- field_path is e.g. "Primary" for a unit->weapon gap, or
        "Primary.Warhead" for a weapon->warhead gap found one level down.
        "definition" is populated (from `baseline`) when the gap is
        fixable by pulling the identifier in verbatim, e.g. via
        Map.add_entity(Serializable(definition, identifier)).
    """
    getters = {
        "building": map_obj.get_building_types,
        "vehicle": map_obj.get_vehicle_types,
        "infantry": map_obj.get_infantry_types,
    }

    live_entities = {e.get_header(): e.attributes for e in map_obj.entities}
    known = set(live_entities)
    for registry in (map_obj.get_building_types(), map_obj.get_vehicle_types(), map_obj.get_infantry_types()):
        known.update(registry.declarations)

    def _is_missing(identifier):
        if not identifier or identifier.lower() == "none":
            return False
        if identifier in known:
            return False
        if control_baseline is not None and identifier in control_baseline.sections:
            return False
        return True

    problems = {}
    for category, getter in getters.items():
        registry = getter()
        for name, obj in registry.definitions.items():
            for field in fields:
                identifier = obj.attributes.get(field)
                if not identifier or identifier.lower() == "none":
                    continue
                if _is_missing(identifier):
                    problems.setdefault(name, {})[field] = {
                        "identifier": identifier,
                        "definition": baseline.sections.get(identifier),
                    }
                    continue

                # Resolves at the unit->weapon level -- now check
                # weapon->warhead. Its definition can come from the map
                # itself or from baseline (a vanilla weapon known only to
                # `known` via control_baseline has no attributes to walk
                # further, so there's nothing to check in that case).
                weapon_def = live_entities.get(identifier) or baseline.sections.get(identifier)
                if not weapon_def:
                    continue
                for wfield in weapon_fields:
                    wid = weapon_def.get(wfield)
                    if _is_missing(wid):
                        problems.setdefault(name, {})["{}.{}".format(field, wfield)] = {
                            "identifier": wid,
                            "definition": baseline.sections.get(wid),
                        }
    return problems
