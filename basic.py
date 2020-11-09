"""
    Abstract classes that all the entities inherit from
"""
import houses

class Serializable():
    """ Basic set of attributes that can be serialized to a string """

    def __init__(self, attributes=None, header=""):
        """ Constructor forces a new dict to be initialized if none provided """
        self.attributes = attributes if attributes is not None else {}
        self.header = header

    def add_attribute(self, key, value):
        self.attributes[key] = value
    def get_attributes(self):
        return self.attributes
    def get_header(self):
        return self.header

    def serialize(self):
        """ Base form of the serialize method, more complex entities overwrite this """
        string = "[" + self.header + "]\n"

        for (key, value) in self.attributes.items():
            string += "{}={}\n".format(key, str(value).replace("False", "no").replace("True", "yes"))
        return string + '\n'


class Basic(Serializable):
    """ Basic map properties: title, game mode, free radar... """
    def __init__(self, attributes=None):
        self.attributes = attributes if attributes is not None else {}
        super(Basic, self).__init__(self.attributes)
        self.header = "Basic"

    def set_map_name(self, name: str):
        self.attributes["Name"] = name
    def set_percent(self, percent: int):
        self.attributes["Percent"] = percent
    def set_game_mode(self, mode: str):
        self.attributes["GameMode"] = name
    def set_home_cell(self, cell: int):
        self.attributes["HomeCell"] = name
    def set_alt_home_cell(self, cell: int):
        self.attributes["AltHomeCell"] = name
    def set_init_time(self, time: int):
        self.attributes["InitTime"] = name
    def set_official(self, official: bool):
        self.attributes["Official"] = official
    def set_end_of_game(self, state: bool):
        self.attributes["EndOfGame"] = state
    def set_free_radar(self, state: bool):
        self.attributes["FreeRadar"] = state
    def set_skip_score(self, state: bool):
        self.attributes["SkipScore"] = state
    def set_max_players(self, max_players: int):
        self.attributes["MaxPlayers"] = max_players
    def set_min_players(self, min_players: int):
        self.attributes["MinPlayers"] = min_players
    def set_train_crate(self, state: bool):
        self.attributes["TrainCrate"] = state
    def set_truck_crate(self, state: bool):
        self.attributes["TruckCrate"] = state
    def set_one_time_only(self, state: bool):
        self.attributes["OneTimeOnly"] = state
    def set_carry_over_cap(self, carry_over_cap: int):
        self.attributes["CarryOverCap"] = carry_over_cap
    def set_new_INI_format(self, ini_format: int):
        self.attributes["NewINIFormat"] = ini_format
    def set_next_scenario(self, scenario: str):
        self.attributes["NextScenario"] = scenario
    def set_required_addon(self, addon: str):
        self.attributes["RequiredAddon"] = addon
    def set_skip_map_select(self, state: bool):
        self.attributes["SkipMapSelect"] = state
    def set_carry_over_money(self, money: int):
        self.attributes["CarryOverMoney"] = money
    def set_alt_next_scenario(self, scenario: str):
        self.attributes["AltNextScenario"] = scenario
    def set_multiplayer_only(self, state: int):
        self.attributes["MultiplayerOnly"] = state
    def set_ice_growth_enabled(self, state: bool):
        self.attributes["IceGrowthEnabled"] = state
    def set_vein_growth_enabled(self, state: bool):
        self.attributes["VeinGrowthEnabled"] = state
    def set_tiberium_growth_enabled(self, state: bool):
        self.attributes["TiberiumGrowthEnabled"] = state
    def set_ignore_global_ai_triggers(self, state: bool):
        self.attributes["IgnoreGlobalAITriggers"] = state
    def set_tiberium_death_to_visceroid(self, state: bool):
        self.attributes["TiberiumDeathToVisceroid"] = state


class BaseLogic(Serializable):
    """ Base class for logic entities """
    id_counter = 1000000

    def __str__(self):
        """ Only return the identifier string """
        return str(self.id).zfill(8)

    def set_identifier(self, identifier: int):
        """
            DO NOT USE MANUALLY!
            Use create_by_id if you need to specify an ID!
        """
        self.id = identifier
    def get_identifier(self):
        """ Equals the string representation of this object as integer """
        return self.id
    def create_by_id(identifier: int, _attributes=None):
        """ Keeps consistency when specifying an ID """
        attributes = _attributes if _attributes is not None else {}
        logic = BaseLogic(attributes)
        logic.set_identifier(identifier)
        BaseLogic.id_counter -= 1
        return logic

    def __init__(self, attributes=None):
        self.attributes = attributes if attributes is not None else {}
        super(BaseLogic, self).__init__(self.attributes)
        self.id = BaseLogic.id_counter
        BaseLogic.id_counter += 1
        self.header = "0" + str(self.id)

class StringArray():
    """ Base class for a list of strings """
    def __init__(self, header: str, array: list=[], start_at_one=False):
        """ start_at_one: Start counting at 1 instead of 0 """
        self.header = header
        self.array = array
        self.start_at_one = start_at_one

    def get_array(self):
        return self.array

    def set_array(self, array: [str]):
        self.array = array

    def serialize(self):
        string = "[{}]\n".format(self.header)

        for counter, line in enumerate(self.array):
            if self.start_at_one:
                string += "{}={}\n".format(counter + 1, line)
            else:
                string += "{}={}\n".format(counter, line)

        return string + '\n'


class Waypoint():
    """ Waypoints have various purposes """
    # TODO keep consistent with parsed waypoints
    id_counter = 1
    waypoints = []

    def __init__(self, x, y, z=0, _id=-1):
        self.x = x
        self.y = y
        self.z = z
        if _id == -1:
            self.id = Waypoint.id_counter
        else:
            self.id = _id

        Waypoint.id_counter += 1
        Waypoint.waypoints.append(self)

    def get_id(self):
        return self.id
    def get_list():
        """
            Get global list of all existing waypoints.
        """
        return Waypoint.waypoints
    def from_letter(letter):
        """
            Returns the waypoint object that belongs to the specified letter.
        """
        for w in Waypoint.waypoints:
            if w.get_letter() == letter:
                return w
        print("WARNING: waypoint '" + letter + "' does not exist yet!")
    def get_encoded(self):
        return "{}{}{}".format(self.x, self.z, self.y)
    def get_letter(self):
        """
            Returns the alphabetical representation of ID
        """
        if self.id > 26:
            print("WARNING: Waypoint ID out of range: " + str(self.id))
        return chr(64 + self.id)

    def get_player_start(self):
        return "{},{}".format(self.x, self.y)

    """
        Keep track of player start points
    """
    def player_A():
        return 

    def __str__(self):
        return "Waypoint{}={},{}".format(self.id, self.x, self.y)

class Codes():
    @staticmethod
    def yuri_prime():
        return "YURIPR"
    @staticmethod
    def kirov():
        return "ZEP"
    @staticmethod
    def tesla_tank():
        return "TTNK"
    @staticmethod
    def gattling_tank():
        return "YTNK"
    @staticmethod
    def siege_chopper():
        return "SCHP"
    @staticmethod
    def chrono_seal():
        return "CCOMAND"
    @staticmethod
    def disc():
        return "DISK"
    @staticmethod
    def mastermind():
        return "MIND"
    @staticmethod
    def desolator():
        return "DESO"
    @staticmethod
    def apocalypse_tank():
        return "APOC"
    @staticmethod
    def terror_drone():
        return "DRON"
    @staticmethod
    def chaos_drone():
        return "CAOS"
    @staticmethod
    def rhino_tank():
        return "HTNK"
    @staticmethod
    def prism_tank():
        return "SREF"
    @staticmethod
    def chrono_legionaire():
        return "CLEG"
    @staticmethod
    def gi():
        return "E1"
    @staticmethod
    def conscript():
        return "E2"
    @staticmethod
    def yuri_clone():
        return "YURI"
    @staticmethod
    def initiate():
        return "INIT"
    @staticmethod
    def virus():
        return "VIRUS"
    @staticmethod
    def attack_dog():
        return "ADOG"
    @staticmethod
    def yuri_clones():
        return "YURI"
    @staticmethod
    def brutes():
        return "BRUTE"

