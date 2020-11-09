from entities import *
from houses import *
from basic import *
from logic import *
from mapio import MapIO

class Map():
    def __init__(self):
        self.header = Header()
        self.building_types = BuildingTypes()
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
        self.ai_trigger_types = Serializable()
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
    def get_entities(self):
        return self.entities
    def get_structures(self):
        return self.structures
    def get_infantry(self):
        return self.infantry
    def add_entity(self, entity: Serializable):
        self.entities.append(entity)
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
            data += Script.get_list_string()

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

        data += TaskForce.get_list_string()

        data += Team.get_list_string()
        
        data += "[Waypoints]\n"
        for key, value in self.waypoints.items():
            data += "{}={}\n".format(key, value.get_encoded())
        data += '\n'

        data += self.digest.serialize()

        return data