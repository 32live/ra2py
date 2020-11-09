from houses import House
from basic import *

"""
    TODO: it appears that standard houses are referenced by some magic number values
          starting at 4475-4478 are players A,B,C,D probably E and F belong
          to 4479 and 4480 ...
"""
class Event():
    """ Events to activate triggers """
    def __init__(self, attributes=None):
        self.attributes = attributes if attributes is not None else {0:8,1:0,2:0}
    def create_AnyEvent():
        return Event({0:8, 1:0, 2:0})
    def create_ElapsedTime(seconds: int):
        return Event({0:13, 1:0, 2:seconds})
    def create_MissionTimerExpired():
        return Event({0:14, 1:0, 2:0})
    def create_DestroyedUnitsAll(house: int):
        return Event({0:9, 1:0, 2:house})

    def __str__(self):
        return "{},{},{}".format(*self.attributes.values())


class Trigger(BaseLogic):
    def __init__(self, attributes=None):
        self.attributes = attributes if attributes is not None else {"Owner":House.Americans(),
                                    "Name": "no-name",
                                    "Disabled": False,
                                    "Easy": True,
                                    "Medium": True,
                                    "Hard": True,
							 "attached_trigger": "<none>"}
        super(Trigger, self).__init__(self.attributes)
        self.actions = []
        self.events = []
        self.tags = []

    def create_by_id(identifier: int, attributes: dict):
        t = Trigger(attributes)
        t.set_identifier(identifier)
        Trigger.id_counter -= 1
        return t
    def add_event(self, event: Event):
        self.events.append(event)
    def add_events(self, events: list):
        self.events.extend(events)
    def add_actions(self, actions: list):
        self.actions.extend(actions)
    def add_tag(self, tag):
        self.tags.append(tag)
    def remove_tag(self, tag):
        self.tags.remove(tag)
    def get_tags(self):
        return self.tags
    def get_events(self):
        return self.events
    def get_name(self):
        return self.attributes["Name"]
    def set_name(self, name: str):
        self.attributes["Name"] = name
    def set_owner(self, owner: House):
        self.attributes["Owner"] = owner
    def disable(self):
        self.attributes["Disabled"] = True
    def enable(self):
        self.attributes["Disabled"] = False
    def set_enabled(self, state: bool):
        self.attributes["Disabled"] = state
    def set_difficulty_medium(self, state: bool):
        self.attributes["Medium"] = state
    def set_difficulty_easy(self, state: bool):
        self.attributes["Easy"] = state
    def set_difficulty_hard(self, state: bool):
        self.attributes["Hard"] = state
    def add_action(self, action):
        self.actions.append(action)
    def serialize_actions(self):
        string = "{}={}".format(self, len(self.actions))
        for action in self.actions:
            string += ',' + str(action)
        return string
    def serialize_events(self):
        string = "{}={}".format(self, len(self.events))
        for event in self.events:
            string += ',' + str(event)
        return string + '\n'

    # trigger or tag ...
    def get_tag(self):
        """
            This is wrong -> encapsulate in Tag object!!!
            Edit: Really? multiple tags -> single trigger possible
        """
        return "{},{} {},{}".format(0, self.get_name(), 1, self)

    def serialize(self):
        # None -> attached trigger
        return "{}={},{},{},{},{},{},{},{}".format(self, self.attributes["Owner"],
                                                    self.attributes["attached_trigger"],
                                                    self.get_name(),
                                                    int(self.attributes["Disabled"]),
                                                    int(self.attributes["Easy"]),
                                                    int(self.attributes["Medium"]),
                                                    int(self.attributes["Hard"]), 0)

class Action():
    #(numactions,)107(reinfchrono),1,team,0,0,0,0,Waypoint-> alphabetical
    def __init__(self, attributes: dict=None):
        self.attributes = attributes if attributes is not None else {}

    def create_ReinforceByChrono(team, waypoint: Waypoint):
        return Action({"Code": 107, "Arg0": 1, "Arg1": str(team),
            "Arg2": 0, "Arg3": 0, "Arg4": 0, "Arg5": 0, "Waypoint": waypoint.get_letter()})
    def create_ReinforceTeamAtWaypoint(team, waypoint: Waypoint):
        return Action({"Code": 80, "Arg0": 1, "Arg1": str(team),
            "Arg2": 0, "Arg3": 0, "Arg4": 0, "Arg5": 0, "Waypoint": waypoint.get_letter()})
    def create_IronCurtainAt(waypoint: Waypoint):
        return Action({"Code": 109, "Arg0": 0, "Arg1": 0,
            "Arg2": 0, "Arg3": 0, "Arg4": 0, "Arg5": 0, "Waypoint": waypoint.get_letter()})
    def create_ChangeHouse(house: House):
        return Action({"Code": 14, "Arg0": 0, "Arg1": str(house),
            "Arg2": 0, "Arg3": 0, "Arg4": 0, "Arg5": 0, "Waypoint": "A"})
    def create_TimerSet(time: int):
        return Action({"Code": 27, "Arg0": 0, "Arg1": str(time),
            "Arg2": 0, "Arg3": 0, "Arg4": 0, "Arg5": 0, "Waypoint": "A"})
    def create_TimerText(text: str):
        return Action({"Code": 103, "Arg0": 4, "Arg1": text,
            "Arg2": 0, "Arg3": 0, "Arg4": 0, "Arg5": 0, "Waypoint": "A"})
    def create_TextTrigger(text: str):
        return Action({"Code": 11, "Arg0": 4, "Arg1": text,
            "Arg2": 0, "Arg3": 0, "Arg4": 0, "Arg5": 0, "Waypoint": "A"})
    def create_DisableTrigger(trigger: Trigger):
        return Action({"Code": 54, "Arg0": 2, "Arg1": str(trigger),
            "Arg2": 0, "Arg3": 0, "Arg4": 0, "Arg5": 0, "Waypoint": "A"})
    def create_EnableTrigger(trigger: Trigger):
        return Action({"Code": 53, "Arg0": 2, "Arg1": str(trigger),
            "Arg2": 0, "Arg3": 0, "Arg4": 0, "Arg5": 0, "Waypoint": "A"})

    def __str__(self):
        return "{},{},{},{},{},{},{},{}".format(*self.attributes.values())


class Tag(BaseLogic):
    tags = []
    #=Description, P1 type, P2 type, TagNeeded, Obsolete,Desc2,UsedInTS,UsedInRA2,ID,[NeedsYR optional]

    def __init__(self, attributes=None):
        self.attributes = attributes if attributes is not None else {}
        super(Tag, self).__init__(attributes)
        Tag.tags.append(self)

    def get_list_string():
        string = "[Tags]\n"
        for tag in Tag.tags:
            string += str(tag) + '\n'
        return string

    def create_by_id(identifier: int, attributes: dict):
        t = Tag(attributes)
        t.set_identifier(identifier)
        t.header = str(identifier).zfill(8)
        Tag.id_counter -= 1
        return t

    def set_repeating(self, state: bool):
        self.attributes["Behavior"] = 2 if state else 0
    def set_trigger(self, trigger: Trigger):
        self.attributes["Trigger"] = trigger
		# TODO
        if self not in trigger.get_tags():
            trigger.add_tag(self)
        self.set_name(trigger.get_name() + ' ' + str(len(trigger.get_tags())))
    def get_trigger(self):
        return self.attributes["Trigger"]
    def get_behavior(self):
        return self.attributes["Behavior"]
    def set_name(self, name: str):
        """
            Overwrite name attribute (normally it's trigger name + number)
        """
        self.attributes["Name"] = name

    def serialize(self):
        return "{}={},{},{}".format(self.header, self.get_behavior(),
                self.attributes["Name"],
                self.attributes["Trigger"])


class ScriptItem():
    def __init__(self, action, parameter: int):
        self.parameter = parameter
        self.action = action

    def set_action(self, action: int):
        self.action = action
    def set_parameter(self, parameter):
        self.parameter = parameter

    """
        Factory methods
        TODO: actions are stored in different table -> [Actions]
    """
    def create_Attack(target):
        """
            Attack some general target
            1 - Not specified
            2 - Buildings
            3 - Harvesters
            4 - Infantry
            5 - Vehicles
            6 - Factories
            7 - Base defenses
            8 - Power plants
        """
        return ScriptItem(0, target)
    def create_Attack_Waypoint(waypoint: Waypoint):
        return ScriptItem(1, waypoint.get_id())
    def create_Go_Berzerk():
        return ScriptItem(1, 0)
    def create_Move_to_waypoint(waypoint: Waypoint):
        return ScriptItem(3, waypoint.get_id())
    def create_Move_to_Cell(cell):
        return ScriptItem(4, cell)
    def create_Guard_Area(time):
        """
            time - timer ticks (frames)
                   time units to guard
        """
        return ScriptItem(5, time)
    def create_Jump_to_line_number(action_number):
        return ScriptItem(6, action_number)
    def create_Player_wins():
        return ScriptItem(7, 0)
    def create_Unload(split_groups):
        """
            0 - Keep Transports, Keep Units
            1 - Keep Transports, Lose Units
            2 - Lose Transports, Keep Units
            3 - Lose Transports, Lose Untis
        """
        return ScriptItem(8, split_groups)
    def create_Deploy():
        return ScriptItem(9, 0)
    def create_Follow_Friendlies():
        return ScriptItem(10, "")
    # TODO:
    # TO BE CONTINUED...

    def __str__(self):
        return "{},{}".format(self.action, self.parameter)


class Script(BaseLogic):
    scripts = []

    def __init__(self, attributes=None):
        self.attributes = attributes if attributes is not None else {"Name": "no-name"}
        super(Script, self).__init__(self.attributes)
        self.actions = []
        Script.scripts.append(self)

    def get_list_string():
        string = "[ScriptTypes]\n"
        for c, tf in enumerate(Script.scripts):
            string += "{}={}\n".format(c, tf)
        return string + '\n'
    def set_name(self, name: str):
        self.attributes["Name"] = name
    def get_name(self):
        return self.attributes["Name"]
    def add_action(self, action: ScriptItem):
        self.actions.append(action)

    @staticmethod
    def create_by_id(identifier: int, _attributes: dict=None):
        attributes = _attributes if _attributes is not None else {}
        sc = Script(attributes)
        sc.set_identifier(identifier)
        Script.id_counter -= 1
        return sc

    def serialize(self):
        string = "[" + str(self) + "]\n"

        for c, action in enumerate(self.actions):
            string += "{}={}\n".format(c, action)

        string += "Name={}\n".format(self.attributes["Name"])

        return string


class TaskForce(BaseLogic):
    task_forces = []

    def __init__(self, attributes=None):
 
        self.attributes = attributes if attributes is not None else {
            "Name": "default",
            "Group": -1
        }
        super(TaskForce, self).__init__(self.attributes)
        self.units = []
        TaskForce.task_forces.append(self)

    def get_list_string():
        string = "[TaskForces]\n"
        for c, tf in enumerate(TaskForce.task_forces):
            string += "{}={}\n".format(c, tf)
        return string + '\n'

    def create_by_id(identifier: int, attributes: dict={}):
        tf = TaskForce(attributes)
        tf.set_identifier(identifier)
        TaskForce.id_counter -= 1
        return tf

    def add_units(self, unit, amount):
        self.units.append((unit, amount))

    def set_name(self, name):
        self.attributes["Name"] = name
    def get_name(self):
        return self.attributes["Name"]
    def set_group(self, group):
        self.attributes["Group"] = group

    def serialize(self):
        string = ""
        counter = 0
        string += "[" + str(self) + "]\n"
        for unit, amount in self.units:
            string += "{}={},{}\n".format(counter, unit, amount)
            counter += 1
        for key in self.attributes:
            string += "{}={}\n".format(key, self.attributes[key])
        return string


class Team(BaseLogic):
    teams = []

    def __init__(self, attributes=None):
        self.attributes = attributes if attributes is not None else {
                "Max": 5,
                "Full": True,
                "Name": "",
                "Group": -1,
                "House": House.Americans(),
                "Script": "",
                "Whiner": False,
                "Droppod": False,
                "Suicide": False,
                "Loadable": False,
                "Prebuild": False,
                "Priority": 5,
                "Waypoint": "A",
                "Annoyance": False,
                "IonImmune": False,
                "Recruiter": False,
                "Reinforce": False,
                "TaskForce": "01000005",
                "TechLevel": 0,
                "Aggressive": False,
                "Autocreate": True,
                "GuardSlower": False,
                "OnTransOnly": False,
                "AvoidThreats": False,
                "LooseRecruit": False,
                "VeteranLevel": 1,
                "IsBaseDefense": False,
                "UseTransportOrigin": False,
                "MindControlDecision": 0,
                "OnlyTargetHouseEnemy": False,
                "TransportsReturnOnUnload": False,
                "AreTeamMembersRecruitable": False
            }
        super(Team, self).__init__(self.attributes)
        Team.teams.append(self)

    def create_by_id(identifier: int, _attributes: dict=None):
        """
            Create a team with custom ID 
            CAUTION: does not increment global logic counter!
        """
        attributes = _attributes if _attributes is not None else {}
        te = Team(attributes)
        te.set_identifier(identifier)
        Team.id_counter -= 1
        return te
    def get_list_string():
        string = "[TeamTypes]\n"
        for c, t in enumerate(Team.teams):
            string += "{}={}\n".format(c, t)
        return string + '\n'

    def set_full(self, state: bool):
        self.attributes["Full"] = state
    def set_whiner(self, state: bool):
        self.attributes["Whiner"] = state
    def set_droppod(self, state: bool):
        self.attributes["Droppod"] = state
    def set_suicide(self, state: bool):
        self.attributes["Suicide"] = state
    def set_loadable(self, state: bool):
        self.attributes["Loadable"] = state
    def set_prebuild(self, state: bool):
        self.attributes["Prebuild"] = state
    def set_annoyance(self, state: bool):
        self.attributes["Annoyance"] = state
    def set_ion_immune(self, state: bool):
        self.attributes["IonImmune"] = state
    def set_recruiter(self, state: bool):
        self.attributes["Recruiter"] = state
    def set_reinforce(self, state: bool):
        self.attributes["Reinforce"] = state
    def set_aggressive(self, state: bool):
        self.attributes["Aggressive"] = state
    def set_autocreate(self, state: bool):
        self.attributes["Autocreate"] = state
    def set_guard_slower(self, state: bool):
        self.attributes["GuardSlower"] = state
    def set_on_trans_only(self, state: bool):
        self.attributes["OnTransOnly"] = state
    def set_avoid_threats(self, state: bool):
        self.attributes["AvoidThreats"] = state
    def set_loose_recruit(self, state: bool):
        self.attributes["LooseRecruit"] = state
    def set_is_base_defense(self, state: bool):
        self.attributes["IsBaseDefense"] = state
    def set_use_transport_origin(self, state: bool):
        self.attributes["UseTransportOrigin"] = state
    def set_only_target_house_enemy(self, state: bool):
        self.attributes["OnlyTargetHouseEnemy"] = state
    def set_transports_return_on_unload(self, state: bool):
        self.attributes["TransportsReturnOnUnload"] = state
    def set_are_team_members_recruitable(self, state: bool):
        self.attributes["AreTeamMembersRecruitable"] = state
    def set_max(self, max: int):
        self.attributes["Max"] = max
    def set_group(self, group: int):
        self.attributes["Group"] = max
    def set_tech_level(self, techlevel: int):
        self.attributes["TechLevel"] = techlevel
    def set_priority(self, priority: int):
        self.attributes["Priority"] = max
    def set_veteran_level(self, level: int):
        self.attributes["VeteranLevel"] = level
    def set_min_control_decision(self, decision: int):
        self.attributes["MindControlDecision"] = decision
    def set_house(self, house: House):
        self.attributes["House"] = house
    def set_script(self, script):
        self.attributes["Script"] = script
    def set_waypoint(self, waypoint: Waypoint):
        self.attributes["Waypoint"] = waypoint
    def set_taskforce(self, taskforce: TaskForce):
        self.attributes["TaskForce"] = taskforce
    def set_name(self, name: str):
        self.attributes["Name"] = name

    def serialize(self):
        string = "[" + str(self) + "]\n"
        for key, value in self.attributes.items():
            string += key + "=" + str(value).replace("False", "no").replace("True", "yes") + "\n"

        return string + '\n'
