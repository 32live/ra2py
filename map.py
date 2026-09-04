import os
import tempfile

from entities import *
from houses import *
from basic import *
from logic import *
from mapio import MapIO


def _reset_global_registries():
    """
        Trigger/Tag/Script/TaskForce/Team/Waypoint/Building/Vehicle/
        InfantryType/House all track their auto-assigned IDs and/or their
        "every instance ever created" list on the class itself rather than
        on a Map, because objects like a Wave's Team/Trigger/Tag are built
        before there's a Map to attach them to. That means none of it
        resets on its own -- without this, loading or building more than
        one Map in the same process leaks IDs and objects between them
        (e.g. the second map's serialized output could include structures
        left over from the first, or garbled duplicate IDs).

        Called at the start of every Map() -- fine as long as maps are
        built/loaded one at a time, which is the common case; it does NOT
        support holding two Map objects open and editing both at once.
    """
    BaseLogic.id_counter = 1000000
    for cls in (Trigger, Tag, Script, TaskForce, Team):
        cls.id_counter = 1000000

    Waypoint.id_counter = 1
    Waypoint.waypoints = []

    Building.index = 407
    Building.buildings = []

    Vehicle.index = 200
    Vehicle.vehicles = []

    InfantryType.index = 66
    InfantryType.infantry_types = []

    Tag.tags = []
    Team.teams = []
    TaskForce.task_forces = []
    Script.scripts = []

    House.houses = {}


class Map():
    def __init__(self):
        _reset_global_registries()
        self.header = Header()
        self.building_types = BuildingTypes()
        self.vehicle_types = VehicleTypes()
        self.infantry_types = InfantryTypes()
        self.preview = Preview()
        self.preview_pack = PreviewPack()
        self.iso_map_pack = Serializable()
        self.scripts = []
        self.teams = []
        self.taskforces = []
        self.triggers = []
        self.actions = []
        self.scripts = {}
        self.houses = []
        self.basic = Basic()
        self.events = []
        self.lighting = Serializable()
        self.structures = []
        self.units = []
        self.infantry = []
        self.size = [0,0,50,100]
        self.theater = "TEMPERATE"
        self.local_size = [2,4,46,94]
        self.overlay_data_pack = Serializable()
        self.overlay_pack = Serializable()
        self.special_flags = SpecialFlags()
        # None (not an empty Serializable) so serialize() can tell "never
        # set" apart from "parsed/set to an actually-empty block" -- a
        # generic Serializable() is truthy either way, which previously
        # caused an always-emitted, unparseable bare "[]" section on any
        # map that never had an [AITriggerTypesEnable] section to begin
        # with (e.g. any SurvivalMap built from empty.yrm).
        self.ai_trigger_types = None
        self.tags = []
        self.entities = []
        self.waypoints = {}
        self.digest = StringArray("Digest", ["rmNjv2ehTG2oP9ACgfVaKPewAG4="])
        self.mapio = MapIO(self)

    def load_from_file(self, path: str):
        self.mapio.read_mapfile(path)
    def save_to_file(self, path: str):
        self.mapio.write_mapfile(path)
    def get_building_types(self):
        return self.building_types
    def get_vehicle_types(self):
        return self.vehicle_types
    def get_infantry_types(self):
        return self.infantry_types
    def add_vehicle_type(self, vehicle: Vehicle):
        """ Declare and define a custom vehicle type in one call (e.g. Vehicle.from_base(...)) """
        self.vehicle_types.declare_type(vehicle.get_identifier())
        self.vehicle_types.define_type(vehicle)
    def add_building_type(self, building: Building):
        """ Declare and define a custom building type in one call """
        self.building_types.declare_type(building.get_identifier())
        self.building_types.define_type(building)
    def add_infantry_type(self, infantry_type: InfantryType):
        """ Declare and define a custom infantry type in one call """
        self.infantry_types.declare_type(infantry_type.get_identifier())
        self.infantry_types.define_type(infantry_type)
    def get_entities(self):
        return self.entities
    def get_structures(self):
        return self.structures
    def get_infantry(self):
        return self.infantry
    def add_entity(self, entity: Serializable):
        self.entities.append(entity)
    def override_entity(self, identifier: str, **fields):
        """
            In-place-override a standard/vanilla identifier's section (a
            weapon, warhead, generic entity, OR a declared custom Building/
            Vehicle/InfantryType): merges `fields` onto whatever this map
            already has for `identifier`, rather than replacing the
            section outright. A field value of None deletes that field
            instead of setting it, same convention as *_type.from_base.

            Merging (not replacing) matters the moment `identifier` already
            has a hand-authored override with fields this call doesn't
            mention -- a wholesale replace would silently drop them. Real
            case this guards against: this project's own map had an
            existing [GAPILE] override (TechLevel=-1, Unsellable=yes,
            Capturable=no, ...); a naive replace-only helper used here
            first nearly wiped all of that while only meaning to fix its
            Factory field.

            Checks the declared-type registries (building_types/
            vehicle_types/infantry_types) FIRST, before generic entities --
            a declared custom type found there is mutated in place (its
            own .attributes dict updated directly, preserving its registry
            membership/index), never duplicated as a second, separate
            generic entity under the same header. Doing that (this
            method's own bug, now fixed) is exactly how this project
            earlier silently wiped three heroes' full stat blocks down to
            just the one field a fix touched: a second, near-empty
            "[Name]" section written to the file collided with the real
            declared type's own section on the next reload, and the
            re-parse let the later one win instead of merging.
        """
        for registry in (self.building_types, self.vehicle_types, self.infantry_types):
            if identifier in registry.definitions:
                obj = registry.definitions[identifier]
                for key, value in fields.items():
                    if value is None:
                        obj.attributes.pop(key, None)
                    else:
                        obj.attributes[key] = value
                return obj

        existing = next((e for e in self.entities if e.get_header() == identifier), None)
        attributes = dict(existing.attributes) if existing else {}
        for key, value in fields.items():
            if value is None:
                attributes.pop(key, None)
            else:
                attributes[key] = value
        self.entities = [e for e in self.entities if e.get_header() != identifier]
        self.add_entity(Serializable(attributes, identifier))
        return self.entities[-1]
    def add_trigger(self, trigger: Trigger):
        self.triggers.append(trigger)
    def remove_trigger(self, trigger: Trigger):
        self.triggers.remove(trigger)
    def add_team(self, team: Team):
        self.teams.append(team)
    def add_script(self, script: Script):
        """ Use create_script instead """
        self.scripts[script.get_name()] = script
    def create_script(self, name: str):
        """ Create a script and add it to this map """
        script = Script(attributes={"Name": name})
        self.scripts[name] = script
        return script
    def remove_team(self, team: Team):
        self.teams.remove(team)
    def add_tag(self, tag: Tag):
        self.tags.append(tag)
    def add_house(self, house: House):
        self.houses.append(house)
    def add_infantry(self, unit):
        self.infantry.append(unit)
    def add_structure(self, structure: Structure):
        self.structures.append(structure)
    def add_unit(self, unit: Unit):
        self.units.append(unit)
    def get_units(self):
        return self.units
    def get_header(self):
        return self.header
    def get_ai_trigger_types(self):
        return self.ai_trigger_types
    def set_header(self, header: Header):
        self.header = header
    def set_special_flags(self, flags: SpecialFlags):
        self.special_flags = flags
    def set_preview(self, preview: Preview):
        self.preview = preview
    def set_preview_pack(self, pack: PreviewPack):
        self.preview_pack = pack
    def set_size(self, size: [int]):
        """ TODO x_0, y_0, width, height """
        self.size = size
    def set_waypoints(self, waypoints: {}):
        self.waypoints = waypoints
    def get_waypoints(self):
        return self.waypoints
    def get_waypoint_by_id(self, id: int):
        return self.waypoints[str(id)]
    def add_waypoint_by_id(self, id: int, waypoint: Waypoint):
        if not self.waypoints[str(id)]:
            self.waypoints[str(id)] = waypoint
        else:
            print("WARNING: ID " + str(id) + " already in use!")
    def get_size(self):
        return self.size
    def set_theater(self, theater: str):
        self.theater = theater
    def set_local_size(self, size: [int]):
        """ TODO x_0, y_0, width, height """
        self.local_size = size
    def set_overlay_data_pack(self, pack):
        self.overlay_data_pack = pack
    def set_overlay_pack(self, pack):
        self.overlay_pack = pack
    def set_basic(self, basic: Basic):
        self.basic = basic
    def set_iso_mappack(self, pack: StringArray):
        self.iso_map_pack = pack
    def set_lighting(self, lighting: StringArray):
        self.lighting= lighting
    def set_ai_trigger_types(self, types: Serializable):
        self.ai_trigger_types = types
    def get_trigger_by_id(self, id: int):
        for t in self.triggers:
            if t.get_identifier() == id:
                return t
    def get_triggers(self):
        return self.triggers
    def set_digest(self, digest: StringArray):
        self.digest = digest
    def add_taskforce(self, tf: TaskForce):
        self.taskforces.append(tf)

    def remove_taskforce(self, tf: TaskForce):
        self.taskforces.remove(tf)
    def serialize_list(self, list, data: str, header=None):
        """
            Serialize a list of objects: list, data string, (optional) group header
        """
        if header:
            data += "[{}]\n".format(header)
        for obj in list:
            data += obj.serialize()
        data += '\n'

    def serialize(self):
        data = self.header.serialize()

        # Building types (declarations only)
        data += self.building_types.serialize()

        # Serialize custom / modified buildings
        for _, building in self.building_types.definitions.items():
            data += building.serialize()
            data += '\n'

        # Vehicle types (declarations only)
        data += self.vehicle_types.serialize()

        # Serialize custom / modified vehicles
        for _, vehicle in self.vehicle_types.definitions.items():
            data += vehicle.serialize()
            data += '\n'

        # Infantry types (declarations only)
        data += self.infantry_types.serialize()

        # Serialize custom / modified infantry types
        for _, infantry_type in self.infantry_types.definitions.items():
            data += infantry_type.serialize()
            data += '\n'

        # TODO building definitions here -> also modified standard buildings
        # TODO scripts, actions, buildings
        for ent in self.entities:
            data += ent.serialize()

        data += self.preview.serialize()
        data += self.preview_pack.serialize()

        # TODO: task force list as dictionary [TaskForces]
        data +="; task forces\n"
        for tf in self.taskforces:
            data += tf.serialize() + '\n'

        data += "; teams:\n"
        for team in self.teams:
            data += team.serialize()
        
        if self.ai_trigger_types:
            data += self.ai_trigger_types.serialize()

        data += "; scripts:\n"
        for _, script in self.scripts.items():
            data += script.serialize() + '\n'
        data += '\n'

        data += "[Actions]\n"
        for tr in self.triggers:
            data += tr.serialize_actions() + '\n'
        data += '\n'

        data += "; houses:\n"
        for house in self.houses:
            data += house.serialize()

        data += House.get_list_string()

        data += self.basic.serialize()

        # TODO what if no events?
        data += "[Events]\n"
        for tr in self.triggers:
            data += tr.serialize_events()
        data += '\n'

        # TODO: serialize [Houses] here -> just a dict containing the houses
        data += "; iso map pack:\n"
        data += self.iso_map_pack.serialize()

        data += self.lighting.serialize()

        data += "[Map]\n"
        data += "Size={},{},{},{}\n".format(*self.size)
        data += "Theater={}\n".format(self.theater)
        data += "LocalSize={},{},{},{}\n\n".format(*self.local_size)

        data +="; overlay data pack\n"
        data += self.overlay_data_pack.serialize()
        data +="; overlay pack\n"
        data += self.overlay_pack.serialize()

        # ScriptTypes
        if self.scripts:
            data += Script.get_list_string(self.scripts.values())

        data += self.special_flags.serialize()

        if self.structures:
            data += "[Structures]\n"
        for c, structure in enumerate(self.structures):
            data += "{}={}\n".format(c, structure)

        if self.units:
            data += "[Units]\n"
        for c, unit in enumerate(self.units):
            data += "{}={}\n".format(c, unit)
        data += '\n'

        if self.infantry:
            data += "[Infantry]\n"
        for c, infantry in enumerate(self.infantry):
            data += "{}={}\n".format(c, infantry)
        data += '\n'

        data += "[Tags]\n"
        for tag in self.tags:
            data += tag.serialize() + '\n'
        data += '\n'

        data += "[Triggers]\n"
        for trigger in self.triggers:
            data += trigger.serialize() + '\n'
        data += '\n'

        data += TaskForce.get_list_string(self.taskforces)

        data += Team.get_list_string(self.teams)
        
        data += "[Waypoints]\n"
        for key, value in self.waypoints.items():
            data += "{}={}\n".format(key, value.get_encoded())
        data += '\n'

        data += self.digest.serialize()

        return data


def verify_round_trip(m: 'Map'):
    """
        Save `m` to a scratch file, reload it fresh, and compare every
        trigger's action count before vs. after. Returns a dict of
        {trigger_identifier: (before_count, after_count)} for any trigger
        whose action count changed -- empty means the round trip was clean.

        This is stricter than just checking that save/reload doesn't raise:
        a real bug this project hit (a trigger's actions silently truncated
        on serialize) still parsed fine on reload and was only caught by
        this kind of structural comparison. Run this after any edit that
        touches triggers/actions, before trusting a save.

        Note: constructing the reloaded Map() resets several class-level ID
        registries (see _reset_global_registries), so `m` itself should be
        treated as done-with by the time this returns -- don't keep editing
        it afterward.
    """
    before = {t.get_identifier(): len(t.actions) for t in m.get_triggers()}

    fd, tmp_path = tempfile.mkstemp(suffix=".yrm")
    os.close(fd)
    try:
        m.save_to_file(tmp_path)
        reloaded = Map()
        reloaded.load_from_file(tmp_path)
    finally:
        os.remove(tmp_path)

    after = {t.get_identifier(): len(t.actions) for t in reloaded.get_triggers()}
    return {
        identifier: (before.get(identifier), after.get(identifier))
        for identifier in set(before) | set(after)
        if before.get(identifier) != after.get(identifier)
    }