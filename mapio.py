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

        with open(path, 'r') as input_file:
            self.data = input_file.readlines()

        self.line = self.data[0]
        self.eof = len(self.data)

        self.index = 0

        # Initial parsing
        print("initial parsing...")
        while(self.next_line()):
            if self.line[0] == '[':
                self.parse_entity()

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
                struct.set_tag(self.tag_dict[str(struct.get_tag())])

        print("tag units...")
        for unit in self.map_obj.get_units():
            # Link unit
            if unit.get_tag() != 'None':
                unit.set_tag(self.tag_dict[str(unit.get_tag().get_identifier())])

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


    def next_line(self):

        if self.index == self.eof:
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

            # NOTE: initially assumed only x and y coordinates, that's why z is in the middle now
            _id, coords = self.line.split('=')
            x = coords[0:2]
            z = coords[2]
            y = coords[3:5]
            waypoints[_id] = Waypoint(int(x), int(y), int(z), int(_id))

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


    def parse_header(self):
        map_format = self.parse_attributes(4, int)

        header = Header(map_format)

        header.set_player_start_A(self.parse_waypoint_player())
        header.set_player_start_B(self.parse_waypoint_player())
        header.set_player_start_C(self.parse_waypoint_player())
        header.set_player_start_D(self.parse_waypoint_player())
        header.set_player_start_E(self.parse_waypoint_player())
        header.set_player_start_F(self.parse_waypoint_player())
        header.set_player_start_G(self.parse_waypoint_player())
        header.set_player_start_H(self.parse_waypoint_player())

        key, val = self.parse_attribute(int)
        header.add_attribute(key, val)

        return header

    def parse_trigger(self):
        id, values = self.line.split('=')
        # tr = Trigger()
        # tr.set_identifier = int(id)
        tr = Trigger.create_by_id(int(id), {})
        attributes = values.split(',')
        tr.set_owner(House.get_house(attributes[0]))
        tr.add_attribute("attached_trigger", attributes[1]) # TODO reference vs. ID?
        tr.set_name(attributes[2])
        tr.set_enabled(attributes[3] == '1')
        tr.set_difficulty_easy(attributes[4] == "1")
        tr.set_difficulty_medium(attributes[5] == "1")
        tr.set_difficulty_hard(attributes[6] == "1")
        tr.add_attribute("last_digit", 0)
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
            values = values.split(',')
            amount = int(values[0])
            trigger_events = []
            for i in range(0, amount):
                event = Event({
                        # Start at +1 since 0 is amount
                        0: int(values[i*3 + 1]),
                        1: int(values[i*3 + 2]),
                        2: int(values[i*3 + 3])
                    })
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
            values = values.split(',')
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
            tag.set_identifier(int(raw_attributes[8]))
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
            tag.set_identifier(attributes[7])
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
        elif self.map_obj.building_types.is_building(name):
            attributes = self.parse_attributes()
            building = Building(name, attributes)
            self.map_obj.building_types.define_type(building)
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
        with open(path, 'w+') as out:
            out.write(self.map_obj.serialize())
