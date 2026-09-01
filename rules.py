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


# Attribute names commonly holding a reference to another section
# (a weapon, in practice) on a Building/Vehicle/InfantryType. Not
# exhaustive -- pass `fields=` to check others.
DEPENDENCY_FIELDS = ("Primary", "Secondary", "ElitePrimary", "EliteSecondary", "DeathWeapon")


def find_missing_dependencies(map_obj, baseline, control_baseline=None, fields=DEPENDENCY_FIELDS):
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

        Returns {name: {field: {"identifier": str, "definition": dict_or_None}}}
        -- "definition" is populated (from `baseline`) when the gap is
        fixable by pulling the identifier in verbatim, e.g. via
        Map.add_entity(Serializable(definition, identifier)).
    """
    getters = {
        "building": map_obj.get_building_types,
        "vehicle": map_obj.get_vehicle_types,
        "infantry": map_obj.get_infantry_types,
    }

    known = {e.get_header() for e in map_obj.entities}
    for registry in (map_obj.get_building_types(), map_obj.get_vehicle_types(), map_obj.get_infantry_types()):
        known.update(registry.declarations)

    problems = {}
    for category, getter in getters.items():
        registry = getter()
        for name, obj in registry.definitions.items():
            for field in fields:
                identifier = obj.attributes.get(field)
                if not identifier or identifier.lower() == "none":
                    continue
                if identifier in known:
                    continue
                if control_baseline is not None and identifier in control_baseline.sections:
                    continue
                problems.setdefault(name, {})[field] = {
                    "identifier": identifier,
                    "definition": baseline.sections.get(identifier),
                }
    return problems
