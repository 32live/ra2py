from entities import *
from logic import *
from basic import *
from os import path


"""
    TODO refactor
"""
class MapIO():
    """
        Simple map parser that iteratively adds layers of logic
        and abstraction -> connected entities are parsed as array of
        strings first, references are added in postprocessing.
    """

    def __init__(self, map_obj):
        self.data = []
        self.map_obj = map_obj
        self.index = 0
        self.line = ""
        self.eof = 0
        self.entity_list = []
        self.logic_list = []
        self.trigger_dict = {}
        self.tag_dict = {}
        self.action_dict = {}
        self.event_dict = {}
        self.house_list = []
        self.script_list = []
        self.task_force_ids = []

    def get_map_obj(self):
        return self.map_obj
    def set_map_obj(self, map_obj):
        self.map_obj = map_obj

    def read_mapfile(self, path):

        # Map files are legacy Windows text (FinalAlert2 writes whatever the
        # system ANSI codepage was), not necessarily UTF-8 -- e.g. accented
        # author names/descriptions can contain arbitrary high bytes that
        # aren't valid UTF-8. latin-1 maps every byte 0-255 to a unique code
        # point (and back), so it never fails to decode and round-trips the
        # original bytes exactly, unlike an explicit Windows codepage.
        with open(path, 'r', encoding='latin-1') as input_file:
            self.data = input_file.readlines()

        self.line = self.data[0]
        self.eof = len(self.data)

        self.index = 0

        # [BuildingTypes]/[VehicleTypes] can appear anywhere in the file
        # relative to the actual type definitions they declare (export order
        # is not guaranteed), so declare them upfront in one pass. Otherwise
        # a definition block parsed before its declaring section would be
        # missed and fall back to a generic, untyped entity.
        self.prescan_type_declarations()

        # Initial parsing
        print("initial parsing...")
        while(self.next_line()):
            while self.line[0] == '[':
                # parse_attributes()/parse_dict()/parse_array() (used by most
                # entity handlers) stop as soon as they see the line starting
                # the NEXT section, but leave that line unconsumed rather than
                # dispatching it -- so after parse_entity() returns, self.line
                # can already be sitting on a fresh, undispatched section
                # header. Dispatch it directly instead of calling next_line()
                # again, which would silently skip that header (and its
                # entire section) whenever it immediately follows one of
                # these entity types.
                pre_index = self.index
                self.parse_entity()
                if self.index == pre_index:
                    # This handler (e.g. "TeamTypes": pass) didn't advance at
                    # all, so fall through to next_line() below as before.
                    break

        # Postprocessing
        print("link teams and taskforces...")
        for ent in self.logic_list:
            attributes = ent.get_attributes()
            """
                TaskForces parsing here
            """
            if ent.get_identifier() in [int(x) for x in self.task_force_ids]:
                tf = TaskForce.create_by_id(ent.get_identifier(), {})

                for entry in attributes.items():
                    #print(entry)
                    if entry[0] == 'Name':
                        tf.set_name(entry[1])
                    elif entry[0] == 'Group':
                        tf.set_group(int(entry[1]))
                    else:
                        amount, unit = entry[1].split(',')
                        tf.add_units(int(amount), unit)

                self.map_obj.add_taskforce(tf)

            elif ent.get_identifier() in [int(x) for x in self.script_list]:
                # Parse all script rally points
                script = Script.create_by_id(ent.get_identifier())
                script_items = ent.get_attributes()
                script.set_name(script_items["Name"])

                for key, entry in script_items.items():
                    if key == "Name":
                        continue
                    tokens = entry.split(',')
                    item = ScriptItem(tokens[0], int(tokens[1]))
                    script.add_action(item)

                #print(script.get_attributes())
                self.map_obj.add_script(script)

            else:
                # TODO
                # TODO -> taskforce reference instead of string
                # TODO
                team = Team.create_by_id(ent.get_identifier(), attributes)
                self.map_obj.add_team(team)

        """
            Parse all custom entities / those that do not belong to the above categories.
        """
        print("parse houses...")
        for ent in self.entity_list:
            attributes = ent.get_attributes()
            name = ent.get_header()
            if name in self.house_list:
                print(name)
                self.map_obj.add_house(House.get_house(name, attributes))

            else:
                self.map_obj.add_entity(Serializable(attributes, name))

        """
            Link objects already parsed
        """
        print("tag structures...")
        for struct in self.map_obj.get_structures():
            # Link structure
            if struct.get_tag() != 'None':
                key = str(struct.get_tag())
                if key in self.tag_dict:
                    struct.set_tag(self.tag_dict[key])
                else:
                    # Dangling reference (e.g. the tag/trigger it once
                    # pointed to was deleted in the map editor without
                    # clearing this field) -- leave the bare, unlinked Tag
                    # in place rather than crashing; it still round-trips
                    # correctly since it still knows its own identifier.
                    print("WARNING: structure references unknown tag " + key)

        print("tag units...")
        for unit in self.map_obj.get_units():
            # Link unit
            if unit.get_tag() != 'None':
                key = str(unit.get_tag())
                if key in self.tag_dict:
                    unit.set_tag(self.tag_dict[key])
                else:
                    print("WARNING: unit references unknown tag " + key)

        """
            Scripts are logic entites containing a list of actions
            They are also declared within a separate list.
        """
        # print("parse scripts...")
        # for ent in self.logic_list:
            # # Go through logic entities
            # # parse script
            # # TODO first extract name, then itemize remaining entries
            # # TODO attributes are dict so keys are simply 0,1,2,3,4 ...
            # if ent.get_identifier() in [int(x) for x in self.script_list]:
                # # Parse all script rally points
                # script = Script()
                # script_items = ent.get_attributes()
                # script.set_name(script_items["Name"])
                # del script_items["Name"]
                # for key, entry in script_items.items():

                    # tokens = entry.split(',')
                    # item = ScriptItem(tokens[0], int(tokens[1]))
                    # script.add_action(item)

                # self.map_obj.add_script(script)

                # # unit.set_tag(self.tag_dict[str(unit.get_tag().get_identifier())])

        print("File read successful!")

        return self.map_obj

    def prescan_type_declarations(self):
        """
            Scan the whole file once for [BuildingTypes]/[VehicleTypes]/
            [InfantryTypes] and declare their entries immediately,
            independent of where those sections happen to sit relative to
            the definition blocks they declare (both orderings show up in
            real exports). declare_type() is idempotent, so the normal pass
            over these sections later on is still safe.
        """
        targets = {
            "[BuildingTypes]": self.map_obj.building_types,
            "[VehicleTypes]": self.map_obj.vehicle_types,
            "[InfantryTypes]": self.map_obj.infantry_types,
        }
        i = 0
        n = len(self.data)
        while i < n:
            header = self.data[i].rstrip('\r\n')
            registry = targets.get(header)
            i += 1
            if registry is None:
                continue
            while i < n:
                entry = self.data[i].rstrip('\r\n')
                if not entry or entry[0] == '[':
                    break
                _, name = entry.split('=', 1)
                registry.declare_type(name)
                i += 1

    def next_line(self):

        if self.index == self.eof:
            # Sentinel so any in-progress block-scanning loop (which checks
            # line[0] against '\n'/'[') terminates instead of re-reading
            # the last line forever.
            self.line = '\n'
            return False

        self.line = self.data[self.index]

        self.index = self.index + 1

        return True

    def parse_attribute(self, cast=str):
        key, value = self.line.replace('\n', '').split('=', 1)
        return key, cast(value)

    def parse_array(self):
        self.next_line()
        array = []

        while self.line[0] != '\n' and self.line[0] != '[':
            array.append(self.parse_attribute()[1])
            self.next_line()

        return array

    def parse_dict(self):
        self.next_line()
        dict = {}

        while self.line[0] != '\n' and self.line[0] != '[':
            key, value = self.parse_attribute()
            dict[key] = value
            self.next_line()

        return dict

    def parse_attributes(self, amount=-1, cast=str):
        self.next_line()
        attributes = {}

        while self.line[0] != '\n' and self.line[0] != '[' and amount != 0:

            key, value = self.parse_attribute(cast)

            attributes[key] = value

            amount = amount - 1
            self.next_line()

        return attributes

    def parse_waypoints(self):
        self.next_line()
        waypoints = {}

        while self.line[0] != '\n' and self.line[0] != '[':

            # Encoded as X*1000+Y (Y zero-padded to 3 digits), not a fixed
            # digit-width split -- breaks for X>=100 or Y>=100 otherwise.
            _id, coords = self.line.split('=')
            x, y = divmod(int(coords), 1000)
            waypoints[_id] = Waypoint(x, y, 0, int(_id))

            self.next_line()

        return waypoints

    def parse_waypoint_player(self):
        _id, coords = self.line.split('=')
        x, y = coords.split(',')
        self.next_line()
        return Waypoint(int(x), int(y), 0, _id)

    def parse_building_types(self):
        attributes = self.parse_attributes()

        for key in attributes:
            print("declared building type: " + attributes[key])
            self.map_obj.building_types.declare_type(attributes[key])

    def parse_vehicle_types(self):
        attributes = self.parse_attributes()

        for key in attributes:
            print("declared vehicle type: " + attributes[key])
            self.map_obj.vehicle_types.declare_type(attributes[key])

    def parse_infantry_types(self):
        attributes = self.parse_attributes()

        for key in attributes:
            print("declared infantry type: " + attributes[key])
            self.map_obj.infantry_types.declare_type(attributes[key])


    def parse_header(self):
        # Width/Height/StartX/StartY are always present, but campaign maps
        # can carry extra fields before the waypoints (e.g. "FreeUnit=none"),
        # so read attributes generically until the first "WaypointN" line
        # instead of assuming a fixed count of 4.
        self.next_line()
        attributes = {}
        while self.line[0] != '\n' and self.line[0] != '[' and not self.line.startswith('Waypoint'):
            key, value = self.parse_attribute()
            try:
                value = int(value)
            except ValueError:
                pass
            attributes[key] = value
            self.next_line()

        header = Header(attributes)

        header.set_player_start_A(self.parse_waypoint_player())
        header.set_player_start_B(self.parse_waypoint_player())
        header.set_player_start_C(self.parse_waypoint_player())
        header.set_player_start_D(self.parse_waypoint_player())
        header.set_player_start_E(self.parse_waypoint_player())
        header.set_player_start_F(self.parse_waypoint_player())
        header.set_player_start_G(self.parse_waypoint_player())
        header.set_player_start_H(self.parse_waypoint_player())

        # Trailing attributes after the 8 waypoints -- usually just
        # NumberStartingPoints, but campaign maps can add more (e.g.
        # SlavesNumber), so read generically rather than exactly one.
        while self.line[0] != '\n' and self.line[0] != '[':
            key, value = self.parse_attribute()
            try:
                value = int(value)
            except ValueError:
                pass
            header.add_attribute(key, value)
            self.next_line()

        return header

    def parse_trigger(self):
        id, values = self.line.split('=')
        # tr = Trigger()
        # tr.set_identifier = int(id)
        tr = Trigger.create_by_id(int(id), {})
        attributes = values.rstrip('\r\n').split(',')
        tr.set_owner(House.get_house(attributes[0]))
        tr.add_attribute("attached_trigger", attributes[1]) # TODO reference vs. ID?
        tr.set_name(attributes[2])
        tr.set_enabled(attributes[3] == '1')
        tr.set_difficulty_easy(attributes[4] == "1")
        tr.set_difficulty_medium(attributes[5] == "1")
        tr.set_difficulty_hard(attributes[6] == "1")
        tr.add_attribute("last_digit", int(attributes[7]))
        return tr

    def parse_triggers(self):
        self.next_line()
        while self.line[0] != '\n' and self.line[0] != '[':
            tr = self.parse_trigger()
            # Add actions and events if already parsed
            if tr.get_identifier() in self.event_dict:
                tr.add_events(self.event_dict[tr.get_identifier()])
            if tr.get_identifier() in self.action_dict:
                tr.add_actions(self.action_dict[tr.get_identifier()])

            self.trigger_dict[tr.get_identifier()] = tr
            self.map_obj.add_trigger(tr)
            self.next_line()
        # Attach triggers to tags:
        for tag in self.tag_dict.values():
            tag.set_trigger(self.trigger_dict[int(tag.get_trigger())])

    def parse_events(self):
        self.next_line()
        while self.line[0] != '\n' and self.line[0] != '[':
            id, values = self.line.split('=')
            values = values.rstrip('\r\n').split(',')
            amount = int(values[0])
            trigger_events = []
            i = 1
            for _ in range(0, amount):
                # Most events are (Type, P1, P2). P1/P2 aren't always numeric
                # (some event types stash an object-type string in there, e.g.
                # type 48 = "48,0,WINI"), so keep them as raw tokens rather
                # than forcing int(). Only Type needs to be an int, to decide
                # where the next event starts.
                attributes = {
                        0: int(values[i]),
                        1: values[i + 1],
                        2: values[i + 2],
                    }
                i += 3
                if i < len(values):
                    try:
                        int(values[i])
                    except ValueError:
                        attributes[3] = values[i]
                        i += 1
                event = Event(attributes)
                trigger_events.append(event)
            # tr = filter(lambda x: x.get_identifier() == id, self.map_obj.get_triggers())
            # tr = (x for x in self.map_obj.get_triggers() if x.get_identifier() == id)
            # tr = next((x for x in self.map_obj.get_triggers() if x.get_identifier() == id), None)
            if int(id) in self.trigger_dict:
                self.trigger_dict[int(id)].add_events(trigger_events)
            else:
                # event_list.append(event)
                self.event_dict[int(id)] = trigger_events
            self.next_line()

    def parse_tags(self):
        raw_tags = self.parse_attributes()
        for key in raw_tags:
            tag_attr = raw_tags[key].split(',')
            trigger = None
            if int(tag_attr[2]) in self.trigger_dict:
                trigger = self.trigger_dict[int(tag_attr[2])]
            t = Tag.create_by_id(int(key), { # TODO WTF???
                    "Behavior": int(tag_attr[0]),
                    "Name": tag_attr[1],
                    "Trigger": trigger if trigger else tag_attr[2]
                })
            self.map_obj.add_tag(t)
            self.tag_dict[key] = t
            print("@parse_tags " + tag_attr[1])

    def parse_actions(self):
        self.next_line()
        while self.line[0] != '\n' and self.line[0] != '[':
            id, values = self.line.split('=')
            values = values.rstrip('\r\n').split(',')
            amount = int(values[0])
            trigger_actions = []
            for i in range(0, amount):
                action = Action({
                        "Code": int(values[i*8 + 1]),
                        "Arg0": values[i*8 + 2],
                        "Arg1": values[i*8 + 3],
                        "Arg2": values[i*8 + 4],
                        "Arg3": values[i*8 + 5],
                        "Arg4": values[i*8 + 6],
                        "Arg5": values[i*8 + 7],
                        "Waypoint": values[i*8 + 8],
                    })
                trigger_actions.append(action)

            # tr = next((x for x in self.map_obj.get_triggers() if x.get_identifier() == id), None)
            if int(id) in self.trigger_dict:
                # tr.add_actions(trigger_actions)
                self.trigger_dict[int(id)].add_actions(trigger_actions)
                print("added actions to trigger")
            else:
                self.action_dict[int(id)] = trigger_actions
            self.next_line()
    def parse_houses(self):
        elements = self.parse_attributes()
        self.house_list = list(elements.values())

    def parse_infantry(self):
        # TODO
        # TODO
        # TODO  bugged AF!
        # TODO
        # TODO
        array = self.parse_array()
        for string in array:
            raw_attributes = string.split(',')
            tag = Tag()
            if raw_attributes[8] != 'None':
                tag.set_identifier(int(raw_attributes[8]))
            else:
                tag = 'None'
            self.map_obj.add_infantry(Infantry({
                    "House": House.get_house(raw_attributes[0]),
                    "Identifier": raw_attributes[1],
                    "Strength": int(raw_attributes[2]),
                    "X": int(raw_attributes[3]),
                    "Y": int(raw_attributes[4]),
                    "unknown": int(raw_attributes[5]),
                    "Mode": raw_attributes[6],
                    "Direction": int(raw_attributes[7]),
                    "Tag": tag,
                    "unknown2": int(raw_attributes[9]),
                    "unknown3": int(raw_attributes[10]),
                    "unknown4": int(raw_attributes[11]),
                    "unknown5": int(raw_attributes[12]),
                    "unknown6": int(raw_attributes[13])
                }))


    def parse_structures(self):
        array = self.parse_array()
        for string in array:
            raw_attributes = string.split(',')
            tag = Tag()
            if raw_attributes[6] != 'None':
                tag.set_identifier(int(raw_attributes[6]))
            else:
                tag = 'None'
            self.map_obj.add_structure(Structure({
                    "House": House.get_house(raw_attributes[0]),
                    "Identifier": raw_attributes[1],
                    "Strength": int(raw_attributes[2]),
                    "X": int(raw_attributes[3]),
                    "Y": int(raw_attributes[4]),
                    "Direction": int(raw_attributes[5]),
                    "Tag": tag,
                    "Sellable": int(raw_attributes[7]),
                    "Rebuild": int(raw_attributes[8]),
                    "Energysupport": int(raw_attributes[9]),
                    "unknown": int(raw_attributes[10]),
                    "Spotlight": int(raw_attributes[11]),
                    "unknown2": "None",
                    "unknown3": "None",
                    "unknown4": "None",
                    "AIrepairs": int(raw_attributes[8]),
                    "ShowName": int(raw_attributes[8])
                }))

    # TODO -> also for structures: tag.create_by_id ?! instead of set_identifier
    def parse_units(self):
        array = self.parse_array()
        for string in array:
            attributes = string.split(',')
            tag = Tag()
            if attributes[7] != 'None':
                tag.set_identifier(int(attributes[7]))
            else:
                tag = 'None'
            self.map_obj.add_unit(Unit({
                "House": attributes[0],
                "Identifier": attributes[1],
                "Strength": int(attributes[2]),
                "X": int(attributes[3]),
                "Y": int(attributes[4]),
                "Direction": int(attributes[5]),
                "Behavior": attributes[6],
                "Tag": tag,
                "unknown1": int(attributes[8]),
                "unknown2": int(attributes[9]),
                "unknown3": int(attributes[10]),
                "unknown4": int(attributes[11]),
                "unknown5": int(attributes[12]),
                "ShowName": int(attributes[13])
                }))

    def parse_entity(self):
        # Remove brackets and line break
        name = self.line[1:-2]

        if name == "SpecialFlags":
            attributes = self.parse_attributes()
            self.map_obj.set_special_flags(SpecialFlags(attributes))
        elif name == "Events":
            self.parse_events()
        elif name == "Actions":
            self.parse_actions()
        elif name == "Triggers":
            self.parse_triggers()
        elif name == "Tags":
            self.parse_tags()
            print("@parse_entity.name==tags: finished!")
        elif name == "TaskForces":
            # Remember IDs later and scan parsed dicts for taskforces
            self.task_force_ids = self.parse_array()
        elif name == "Preview":
            attributes = self.parse_attributes()
            self.map_obj.set_preview(Preview(attributes))
        elif name == "PreviewPack":
            array = self.parse_array()
            self.map_obj.set_preview_pack(PreviewPack(array))
        elif name == "BuildingTypes":
            self.parse_building_types()
        elif name == "VehicleTypes":
            self.parse_vehicle_types()
        elif name == "InfantryTypes":
            self.parse_infantry_types()
        elif self.map_obj.building_types.is_building(name):
            attributes = self.parse_attributes()
            building = Building(name, attributes)
            self.map_obj.building_types.define_type(building)
        elif self.map_obj.vehicle_types.is_vehicle(name):
            attributes = self.parse_attributes()
            vehicle = Vehicle(name, attributes)
            self.map_obj.vehicle_types.define_type(vehicle)
        elif self.map_obj.infantry_types.is_infantry(name):
            attributes = self.parse_attributes()
            infantry_type = InfantryType(name, attributes)
            self.map_obj.infantry_types.define_type(infantry_type)
        elif name == "Header":
            header = self.parse_header()
            self.map_obj.set_header(header)
        elif name[0] == '0':
            attributes = self.parse_attributes()
            logic_ent = BaseLogic.create_by_id(int(name), attributes)
            self.logic_list.append(logic_ent)
        elif name == "Basic":
            attributes = self.parse_attributes()
            basic = Basic(attributes)
            self.map_obj.set_basic(basic)
        elif name == "OverlayDataPack":
            array = self.parse_array()
            self.map_obj.set_overlay_data_pack(StringArray("OverlayDataPack", array))
        elif name == "OverlayPack":
            array = self.parse_array()
            self.map_obj.set_overlay_pack(StringArray("OverlayPack", array))
        elif name == "IsoMapPack5":
            array = self.parse_array()
            self.map_obj.set_iso_mappack(StringArray("IsoMapPack5", array, start_at_one=True))
        # elif name in ["Africans", "Alliance", "Americans", "Arabs", "Germans", "French",
                # "British", "Confederation", "YuriCountry"
        elif name == "Lighting":
            attributes = self.parse_attributes(cast=float)
            self.map_obj.set_lighting(Lighting(attributes))
        elif name == "Map":
            attribs = self.parse_attributes()
            self.map_obj.set_size([int(x) for x in attribs["Size"].split(',')])
            self.map_obj.set_theater(attribs["Theater"])
            self.map_obj.set_local_size([int(x) for x in attribs["LocalSize"].split(',')])
        elif name == "Houses":
            self.parse_houses()
        elif name == "Infantry":
            self.parse_infantry()
        elif name == "Structures":
            self.parse_structures()
        elif name == "ScriptTypes":
            # ScriptTypes are simply a list of IDs of scripts -> postprocessing
            array = self.parse_array()
            self.script_list = array
        elif name == "Waypoints":
            # Waypoints are coordinates in a single integer value
            wps = self.parse_waypoints()
            self.map_obj.set_waypoints(wps)
        elif name == "TeamTypes":
            # This is generated automatically when parsing teams
            # TODO can teams be mistaken for something else?
            pass
        elif name == "AITriggerTypesEnable":
            attributes = self.parse_dict()
            self.map_obj.set_ai_trigger_types(Serializable(attributes, name))
        elif name == "Digest":
            attr = self.parse_array()
            self.map_obj.set_digest(StringArray(name, attr, start_at_one=True))
        elif name == "Units":
            self.parse_units()
        else:
            # TODO parse buildings here -> [CAOILD] etc.
            attributes = self.parse_dict()
            self.entity_list.append(Serializable(attributes, name))
            # self.map_obj.add_entity(Serializable(attributes, name))

    def write_mapfile(self, path):
        with open(path, 'w+', encoding='latin-1') as out:
            out.write(self.map_obj.serialize())
