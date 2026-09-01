from houses import *
from basic import *
from logic import *

class Preview(Serializable):
    def __init__(self, attributes=None):
        self.attributes = attributes if attributes is not None else {"Size":"0,0,25,25"}
        super(Preview, self).__init__(self.attributes)
        self.header = "Preview"

class Infantry(Serializable):
    """ Prebuilt units on the map """
    def __init__(self, attributes=None):
        self.attributes = attributes if attributes is not None else {
                "House": House.get_house("Neutral"),
                "Unit": "BORIS",
                "Strength": 256,
                "X": 91,
                "Y": 97,
                "unknown": 0,
                "Mode": "Guard",
                "Direction": 64,
                "Tag": None,
                "unknown2": 0,
                "unknown3": -1,
                "unknown4": 0,
                "unknown5": 1,
                "unknown6": 0,
            }
        super(Infantry, self).__init__(self.attributes)
        self.header = "Infantry"

    def set_house(self, house: House):
        self.attributes["House"] = house
    def change_unit(self, unit: str):
        self.attributes["Unit"] = unit
    def set_strength(self, strength: int):
        self.attributes["Strength"] = strength
    def set_location(self, location: Waypoint):
        self.attributes["X"] = location.x
        self.attributes["Y"] = location.y
    def set_mode(self, mode: str):
        self.attributes["Mode"] = mode
    def set_direction(self, direction: int):
        self.attributes["Direction"] = direction
    def get_tag(self):
        return self.attributes["Tag"]
    def attach_tag(self, tag: Tag):
        self.attributes["Tag"] = tag
    def detach_tag(self):
        self.attributes["Tag"] = None

    def __str__(self):
        return "{},{},{},{},{},{},{},{},{},{},{},{},{},{}".format(*self.attributes.values())

class Lighting(Serializable):
    """ Lighting values for various cases like superweapons """
    def __init__(self, attributes=None):
        self.attributes = attributes if attributes is not None else {}
        super(Lighting, self).__init__(self.attributes)
        self.header = "Lighting"

    def set_red(self, red: float):
        self.attributes["Red"] = red
    def set_blue(self, blue: float):
        self.attributes["Blue"] = blue
    def set_green(self, green: float):
        self.attributes["Green"] = green
    def set_level(self, level: float):
        self.attributes["Level"] = level
    def set_ground(self, ground: float):
        self.attributes["Ground"] = ground
    def set_ion_red(self, ionred: float):
        self.attributes["IonRed"] = ionred
    def set_ambient(self, ambient: float):
        self.attributes["Ambient"] = ambient
    def set_ion_blue(self, ionblue: float):
        self.attributes["IonBlue"] = ionblue
    def set_ion_green(self, value: float):
        self.attributes["IonGreen"] = value
    def set_ion_level(self, value: float):
        self.attributes["IonLevel"] = value
    def set_ion_ground(self, value: float):
        self.attributes["IonGround"] = value
    def set_ion_ambient(self, value: float):
        self.attributes["IonAmbient"] = value
    def set_dominator_red(self, value: float):
        self.attributes["DominatorRed"] = value
    def set_dominator_blue(self, value: float):
        self.attributes["DominatorBlue"] = value
    def set_dominator_green(self, value: float):
        self.attributes["DominatorGreen"] = value
    def set_dominator_level(self, value: float):
        self.attributes["DominatorLevel"] = value
    def set_dominator_ground(self, value: float):
        self.attributes["DominatorGround"] = value
    def set_dominator_ambient(self, value: float):
        self.attributes["DominatorAmbient"] = value
    def set_dominator_ambient_change_rate(self, value: float):
        self.attributes["DominatorAmbientChangeRate"] = value

    def serialize(self):
        string = "[" + self.header + "]\n"

        for (key, value) in self.attributes.items():
            string += "{0}={1:.6f}\n".format(key, round(value, 6))
        return string + '\n'


class SpecialFlags(Serializable):
    """
        Special flags, such as:
        fog of war, fixed alliances or destroyable bridges...
    """
    def __init__(self, attributes=None):
        self.attributes = attributes if attributes is not None else {}
        super(SpecialFlags, self).__init__(self.attributes)
        self.header = "SpecialFlags"

    def set_inert(self, inert: bool):
        self.attributes["Inert"] = inert
    def set_fog_of_war(self, fog: bool):
        self.attributes["FogOfWar"] = fog
    def set_ion_storms(self, ionstorms: bool):
        self.attributes["IonStorms"] = ionstorms
    def set_mcv_deploy(self, deploy: bool):
        self.attributes["MCVDeploy"] = deploy
    def set_meteroites(self, meteroites: bool):
        self.attributes["Meteroites"] = meteroites
    def set_visceroids(self, Visceroids: bool):
        self.attributes["Visceroids"] = visceroids
    def set_fixed_alliance(self, fix: bool):
        self.attributes["FixedAlliance"] = fix
    def set_tiberium_grows(self, grows: bool):
        self.attributes["TiberiumGrows"] = grows
    def set_initial_veteran(self, initialveteran: bool):
        self.attributes["InitialVeteran"] = initialveteran
    def set_harvester_immune(self, immune: bool):
        self.attributes["HarvesterImmune"] = immune
    def set_tiberium_spreads(self, spreads: bool):
        self.attributes["TiberiumSpreads"] = spreads
    def set_tiberium_explosive(self, explosive: bool):
        self.attributes["TiberiumExplosive"] = explosive
    def set_destroyable_bridges(self, destroyable: bool):
        self.attributes["DestroyableBridges"] = destroyable


class PreviewPack(StringArray):
    """ Base64 encoded lzo file that represents an BGR image """
    def __init__(self, image_data=None):
        self.image_data = image_data if image_data is not None else {}
        super(PreviewPack, self).__init__("PreviewPack", self.image_data, start_at_one=True)


class Building():
    """
        Building definition, custom buildings possible
    TODO add a factory method for each default building with matching index
        -> set hardcoded index and decrement counter
    TODO if adding a completely new building, increment index counter
        ( starting at 407 )
    TODO the above also applies for new units
    """
    index = 407
    buildings = []

    def __init__(self, identifier, attributes):
        self.attributes = attributes if attributes is not None else {}
        self.identifier = identifier
        self.index = Building.index
        Building.index += 1
        Building.buildings.append(self)

    @classmethod
    def from_base(cls, baseline, base_identifier, new_identifier, **overrides):
        """
            Derive a new building type from an existing one (vanilla or
            another custom type already in `baseline`): start from
            base_identifier's complete stat block and apply only the given
            overrides, leaving every other field exactly as the base has it.

            baseline: a rules.RulesBaseline (e.g. RulesBaseline.from_tib_preset(...))
        """
        attributes = baseline.get_attributes(base_identifier)
        for key, value in overrides.items():
            attributes[key] = str(value)
        return cls(new_identifier, attributes)

    def get_buildings():
        return Building.buildings

    def standard_building(self, index: str, identifier: str, attributes={}):
        b = Building(identifier, attributes)
        b.set_index(index)
        Building.index -= 1
        return b
    def set_index(self, index: int):
        self.index = index
    def get_index(self):
        return self.index
    def get_identifier(self):
        return self.identifier
    def set_name(self, name: str):
        self.attributes["Name"] = name
    def set_armor(self, armor):
        self.attributes["Armor"] = armor
    def set_image(self, image: str):
        self.attributes["Image"] = image
    def set_owners(self, owners: list):
        self.attributes["Owner"] = owners
    def set_sight(self, sight: int):
        self.attributes["Sight"] = sight
    def set_points(self, points: int):
        self.attributes["Points"] = points
    def set_spysat(self, state: bool):
        self.attributes["SpySat"] = state
    def set_radar(self, state: bool):
        self.attributes["Radar"] = state
    def set_ui_name(self, ui_name: int):
        self.attributes["UIName"] = ui_name
    def set_nominal(self, state: bool):
        self.attributes["Nominal"] = state
    def set_explodes(self, state: bool):
        self.attributes["Explodes"] = state
    def set_strength(self, strength: int):
        self.attributes["Strength"] = strength
    def set_explosions(self, explosions: list):
        self.attributes["Explosion"] = explosions
    def set_max_debris(self, max_debris: int):
        self.attributes["MaxDebris"] = max_debris
    def set_min_debris(self, min_debris: int):
        self.attributes["MinDebris"] = min_debris
    def set_tech_level(self, tech_level: int):
        self.attributes["TechLevel"] = tech_level
    def set_min_debris(self, min_debris: int):
        self.attributes["MinDebris"] = min_debris
    def set_capturable(self, state: int):
        self.attributes["Capturable"] = state
    def set_unsellable(self, state: int):
        self.attributes["Unsellable"] = state
    def set_death_weapon(self, death_weapon: str):
        self.attributes["DeathWeapon"] = death_weapon
    def set_debris_anims(self, debris_anims: str):
        self.attributes["DebrisAnims"] = debris_anims
    def set_leave_rubble(self, state: bool):
        self.attributes["LeaveRubble"] = state
    def set_radar_invisible(self, state: bool):
        self.attributes["RadarInvisible"] = state
    def set_working_sound(self, working_sound: int):
        self.attributes["WorkingSound"] = working_sound
    def set_insignificant(self, state: bool):
        self.attributes["Insignificant"] = state
    def set_needs_engineer(self, state: bool):
        self.attributes["NeedsEngineer"] = state
    def set_capture_eva_event(self, eva_event: str):
        self.attributes["MinDebris"] = eva_event
    def set_produce_cash_delay(self, delay: int):
        self.attributes["ProduceCashDelay"] = delay
    def set_produce_cash_amount(self, amount: int):
        self.attributes["ProduceCashAmount"] = amount
    def set_produce_cash_startup(self, amount: int):
        self.attributes["ProduceCashStartup"] = amount
    def set_can_c4(self, state: bool):
        self.attributes["CanC4"] = state
    def set_power(self, power: int):
        self.attributes["Power"] = power
    def set_prerequisites(self, prerequisites: list):
        self.attributes["Prerequisites"] = prerequisites
    def set_build_limit(self, build_limit: int):
        self.attributes["BuildLimit"] = build_limit

    def get_value(self, key):
        return self.attributes[key]

    def __str__(self):
        return self.identifier

    def serialize(self):
        string = "[" + self.identifier + "]\n"

        for (key, value) in self.attributes.items():
            string += "{}={}\n".format(key, str(value).replace("False", "no").replace("True", "yes"))

        return string


class BuildingTypes():
    def __init__(self):
        self.definitions = {}
        self.declarations = []

    def declare_type(self, name):
        """
            Only necessary if declaring a new building type.
            If an existing type is modified, use define_type()
        """
        if name not in self.declarations:
            self.declarations.append(name)

    def define_type(self, building: Building):
        """
            Add a definition for a new type or an existing type.
            TODO: add definition table for default buildings (CAOILD, etc..)
        """
        self.definitions[building.get_identifier()] = building

    def is_building(self, name):
        return name in self.declarations

    def get_definitions(self):
        return self.definitions

    def serialize(self):
        string = ""

        if self.declarations:
            # TODO: this counter starts with all standard buildings, therefore its
            # initially 407
            id_counter = 407
            string += "[BuildingTypes]\n"
            for building_key in self.definitions:
                string += "{}={}\n".format(id_counter, self.definitions[building_key])
                id_counter += 1

        # if self.definitions:
            # for definition in self.definitions:
                # string += definition.serialize()

        return string + '\n'


class Vehicle():
    """
        Custom vehicle (unit) type definition, analogous to Building for
        structures. Declared in [VehicleTypes] and defined in its own
        [<identifier>] section, e.g. a modded tank.
    """
    index = 200
    vehicles = []

    def __init__(self, identifier, attributes):
        self.attributes = attributes if attributes is not None else {}
        self.identifier = identifier
        self.index = Vehicle.index
        Vehicle.index += 1
        Vehicle.vehicles.append(self)

    @classmethod
    def from_base(cls, baseline, base_identifier, new_identifier, **overrides):
        """
            Derive a new vehicle type from an existing one (vanilla or
            another custom type already in `baseline`): start from
            base_identifier's complete stat block and apply only the given
            overrides, leaving every other field exactly as the base has it.

            baseline: a rules.RulesBaseline (e.g. RulesBaseline.from_tib_preset(...))

            Example: a Rhino Tank with more health and stronger firepower,
            everything else left at its default:
                Vehicle.from_base(baseline, "MTNK", "SUPRHINO", Strength=1000, Primary="APOCSplashBIG")
        """
        attributes = baseline.get_attributes(base_identifier)
        for key, value in overrides.items():
            attributes[key] = str(value)
        return cls(new_identifier, attributes)

    def get_vehicles():
        return Vehicle.vehicles

    def set_index(self, index: int):
        self.index = index
    def get_index(self):
        return self.index
    def get_identifier(self):
        return self.identifier
    def set_name(self, name: str):
        self.attributes["Name"] = name
    def set_armor(self, armor):
        self.attributes["Armor"] = armor
    def set_image(self, image: str):
        self.attributes["Image"] = image
    def set_owners(self, owners: list):
        self.attributes["Owner"] = owners
    def set_sight(self, sight: int):
        self.attributes["Sight"] = sight
    def set_points(self, points: int):
        self.attributes["Points"] = points
    def set_cost(self, cost: int):
        self.attributes["Cost"] = cost
    def set_speed(self, speed: int):
        self.attributes["Speed"] = speed
    def set_strength(self, strength: int):
        self.attributes["Strength"] = strength
    def set_tech_level(self, tech_level: int):
        self.attributes["TechLevel"] = tech_level
    def set_crewed(self, state: bool):
        self.attributes["Crewed"] = state
    def set_explosion(self, explosion: str):
        self.attributes["Explosion"] = explosion
    def set_primary(self, weapon: str):
        self.attributes["Primary"] = weapon
    def set_secondary(self, weapon: str):
        self.attributes["Secondary"] = weapon
    def set_ui_name(self, ui_name: str):
        self.attributes["UIName"] = ui_name
    def set_prerequisites(self, prerequisites: list):
        self.attributes["Prerequisites"] = prerequisites
    def set_locomotor(self, locomotor: str):
        self.attributes["Locomotor"] = locomotor

    def get_value(self, key):
        return self.attributes[key]

    def __str__(self):
        return self.identifier

    def serialize(self):
        string = "[" + self.identifier + "]\n"

        for (key, value) in self.attributes.items():
            string += "{}={}\n".format(key, str(value).replace("False", "no").replace("True", "yes"))

        return string


class VehicleTypes():
    """
        Registry of custom vehicle type declarations/definitions, analogous
        to BuildingTypes.
    """
    def __init__(self):
        self.definitions = {}
        self.declarations = []

    def declare_type(self, name):
        """
            Only necessary if declaring a new vehicle type.
            If an existing type is modified, use define_type()
        """
        if name not in self.declarations:
            self.declarations.append(name)

    def define_type(self, vehicle: Vehicle):
        """
            Add a definition for a new type or an existing type.
        """
        self.definitions[vehicle.get_identifier()] = vehicle

    def is_vehicle(self, name):
        return name in self.declarations

    def get_definitions(self):
        return self.definitions

    def serialize(self):
        string = ""

        if self.declarations:
            # This counter starts with all standard vehicles, therefore
            # its initially 200 (matches real map exports).
            id_counter = 200
            string += "[VehicleTypes]\n"
            for vehicle_key in self.definitions:
                string += "{}={}\n".format(id_counter, self.definitions[vehicle_key])
                id_counter += 1

        return string + '\n'


class InfantryType():
    """
        Custom infantry type definition, analogous to Building/Vehicle.
        Declared in [InfantryTypes] and defined in its own [<identifier>]
        section. Identifiers seen in the wild can contain spaces (e.g. a
        renamed "Shock Trooper 2"), unlike typical 4-8 char building/vehicle
        codes.
    """
    index = 66
    infantry_types = []

    def __init__(self, identifier, attributes):
        self.attributes = attributes if attributes is not None else {}
        self.identifier = identifier
        self.index = InfantryType.index
        InfantryType.index += 1
        InfantryType.infantry_types.append(self)

    @classmethod
    def from_base(cls, baseline, base_identifier, new_identifier, **overrides):
        """
            Derive a new infantry type from an existing one (vanilla or
            another custom type already in `baseline`): start from
            base_identifier's complete stat block and apply only the given
            overrides, leaving every other field exactly as the base has it.

            baseline: a rules.RulesBaseline (e.g. RulesBaseline.from_tib_preset(...))
        """
        attributes = baseline.get_attributes(base_identifier)
        for key, value in overrides.items():
            attributes[key] = str(value)
        return cls(new_identifier, attributes)

    def get_infantry_types():
        return InfantryType.infantry_types

    def set_index(self, index: int):
        self.index = index
    def get_index(self):
        return self.index
    def get_identifier(self):
        return self.identifier
    def set_name(self, name: str):
        self.attributes["Name"] = name
    def set_armor(self, armor):
        self.attributes["Armor"] = armor
    def set_image(self, image: str):
        self.attributes["Image"] = image
    def set_owners(self, owners: list):
        self.attributes["Owner"] = owners
    def set_sight(self, sight: int):
        self.attributes["Sight"] = sight
    def set_points(self, points: int):
        self.attributes["Points"] = points
    def set_cost(self, cost: int):
        self.attributes["Cost"] = cost
    def set_speed(self, speed: int):
        self.attributes["Speed"] = speed
    def set_strength(self, strength: int):
        self.attributes["Strength"] = strength
    def set_tech_level(self, tech_level: int):
        self.attributes["TechLevel"] = tech_level
    def set_primary(self, weapon: str):
        self.attributes["Primary"] = weapon
    def set_secondary(self, weapon: str):
        self.attributes["Secondary"] = weapon
    def set_ui_name(self, ui_name: str):
        self.attributes["UIName"] = ui_name
    def set_prerequisites(self, prerequisites: list):
        self.attributes["Prerequisites"] = prerequisites

    def get_value(self, key):
        return self.attributes[key]

    def __str__(self):
        return self.identifier

    def serialize(self):
        string = "[" + self.identifier + "]\n"

        for (key, value) in self.attributes.items():
            string += "{}={}\n".format(key, str(value).replace("False", "no").replace("True", "yes"))

        return string


class InfantryTypes():
    """
        Registry of custom infantry type declarations/definitions,
        analogous to BuildingTypes/VehicleTypes.
    """
    def __init__(self):
        self.definitions = {}
        self.declarations = []

    def declare_type(self, name):
        """
            Only necessary if declaring a new infantry type.
            If an existing type is modified, use define_type()
        """
        if name not in self.declarations:
            self.declarations.append(name)

    def define_type(self, infantry_type: InfantryType):
        """
            Add a definition for a new type or an existing type.
        """
        self.definitions[infantry_type.get_identifier()] = infantry_type

    def is_infantry(self, name):
        return name in self.declarations

    def get_definitions(self):
        return self.definitions

    def serialize(self):
        string = ""

        if self.declarations:
            # This counter starts with all standard infantry, therefore
            # its initially 66 (matches real map exports).
            id_counter = 66
            string += "[InfantryTypes]\n"
            for infantry_key in self.definitions:
                string += "{}={}\n".format(id_counter, self.definitions[infantry_key])
                id_counter += 1

        return string + '\n'


class Header(Serializable):
    """
        Waypoints in this case are player starts
    """
    def __init__(self, attributes=None):
        self.attributes = attributes if attributes is not None else {
            "Width": 50,
            "Height": 50,
            "StartX": 50,
            "StartY": 50,
            "Waypoint1": Waypoint(25,25),
            "Waypoint2": Waypoint(25,26),
            "Waypoint3": Waypoint(25,27),
            "Waypoint4": Waypoint(26,25),
            "Waypoint5": Waypoint(26,26),
            "Waypoint6": Waypoint(0,0),
            "Waypoint7": Waypoint(0,0),
            "Waypoint8": Waypoint(0,0),
            "NumberStartingPoints": 5
            }
        super(Header, self).__init__(self.attributes)
        self.waypoints = []

    def set_height(self, height: int):
        self.attributes["Height"] = height
    def set_width(self, width: int):
        self.attributes["Width"] = width
    def set_start_x(self, start_x: int):
        self.attributes["StartX"] = start_x
    def set_start_y(self, start_y: int):
        self.attributes["StartY"] = start_y
    def set_num_starting_points(self, num_starting_points: int):
        self.attributes["NumberStartingPoints"] = num_starting_points
    def set_player_start_A(self, waypoint: Waypoint):
        self.attributes["Waypoint1"] = waypoint
    def set_player_start_B(self, waypoint: Waypoint):
        self.attributes["Waypoint2"] = waypoint
    def set_player_start_C(self, waypoint: Waypoint):
        self.attributes["Waypoint3"] = waypoint
    def set_player_start_D(self, waypoint: Waypoint):
        self.attributes["Waypoint4"] = waypoint
    def set_player_start_E(self, waypoint: Waypoint):
        self.attributes["Waypoint5"] = waypoint
    def set_player_start_F(self, waypoint: Waypoint):
        self.attributes["Waypoint6"] = waypoint
    def set_player_start_G(self, waypoint: Waypoint):
        self.attributes["Waypoint7"] = waypoint
    def set_player_start_H(self, waypoint: Waypoint):
        self.attributes["Waypoint8"] = waypoint
    def get_player_start_A(self):
        return self.attributes["Waypoint1"]
    def get_player_start_B(self):
        return self.attributes["Waypoint2"]
    def get_player_start_C(self):
        return self.attributes["Waypoint3"]
    def get_player_start_D(self):
        return self.attributes["Waypoint4"]
    def get_player_start_E(self):
        return self.attributes["Waypoint5"]
    def get_player_start_F(self):
        return self.attributes["Waypoint6"]
    def get_player_start_G(self):
        return self.attributes["Waypoint7"]
    def get_player_start_H(self):
        return self.attributes["Waypoint8"]

    def serialize(self):
        string = "[Header]\n"

        for (key, value) in self.attributes.items():
            if key.startswith("Way"):
                string += key + "=" + value.get_player_start() + "\n"
            else:
                string += key + "=" + str(value) + "\n"

        for wp in self.waypoints:
            print("@header.serialize: " + wp.get_player_start())
            string += wp.get_player_start() + "\n"

        return string + '\n'


class Structure(Serializable):
    """
        Buildings that are placed on the map. Standard or custom buildings.
        Identified by their identifier (CAOILD, CABHUT...)
    """
    def __init__(self, attributes=None):
        self.attributes = attributes if attributes is not None else {
            "House": House.get_house("Neutral"),
            "Identifier": "CAOILD",
            "Strength": 256,
            "X": 25,
            "Y": 25,
            "Direction": 64,
            "Tag": None,
            "Sellable": 1,
            "Rebuild": 0,
            "Energysupport": 1,
            "unknown": 0,
            "Spotlight": 0,
            "unknown2": None,
            "unknown3": None,
            "unknown4": None,
            "AIrepairs": 0,
            "ShowName": 0
        }
        super(Structure, self).__init__(self.attributes)

    def set_house(self, house: House):
        self.attributes["House"] = house
    def set_identifier(self, identifier: str):
        self.attributes["Identifier"] = identifier
    def set_strength(self, strength: int):
        self.attributes["Strength"] = strength
    def set_location(self, location: Waypoint):
        self.attributes["X"] = location.x
        self.attributes["Y"] = location.y
    def set_direction(self, direction: int):
        self.attributes["Direction"] = direction
    def set_tag(self, tag: Tag):
        self.attributes["Tag"] = tag
    def set_sellable(self, state: bool):
        self.attributes["Sellable"] = state
    def set_rebuild(self, rebuild: int):
        self.attributes["Rebuild"] = rebuild
    def set_energy_support(self, support: int):
        self.attributes["Energysupport"] = support
    def set_spotlight(self, spotlight: int):
        self.attributes["Spotlight"] = spotlight
    def set_AI_repairs(self, repairs: int):
        self.attributes["AIrepairs"] = repairs
    def set_show_name(self, show: int):
        self.attributes["ShowName"] = show
    def get_tag(self):
        return self.attributes["Tag"]
    def attach_tag(self, tag: Tag):
        self.attributes["Tag"] = tag
    def detach_tag(self):
        self.attributes["Tag"] = None

    def __str__(self):
        return "{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}".format(*self.attributes.values())


class Unit(Serializable):
    """
        Prebuilt unit, can be tanks, vehicles, infantry etc.
    """
    def __init__(self, attributes=None):
        self.attributes = attributes if attributes is not None else {
            "House": House.get_house("Neutral"),
            "Identifier": "FV",
            "Strength": 256,
            "X": 25,
            "Y": 25,
            "Direction": 64,
            "Behavior": "Guard",
            "Tag": None,
            "unknown1": 0,
            "unknown2": -1,
            "unknown3": 0,
            "unknown4": -1,
            "unknown5": 1,
            "ShowName": 0
            }
        super(Unit, self).__init__(self.attributes)

    def set_house(self, house: House):
        self.attributes["House"] = house
    def set_identifier(self, identifier: str):
        self.attributes["Identifier"] = identifier
    def set_strength(self, strength: int):
        self.attributes["Strength"] = strength
    def set_location(self, location: Waypoint):
        self.attributes["X"] = location.x
        self.attributes["Y"] = location.y
    def set_direction(self, direction: int):
        self.attributes["Direction"] = direction
    def set_behavior(self, behavior: str):
        self.attributes["Behavior"] = behavior
    def set_tag(self, tag: Tag):
        self.attributes["Tag"] = tag
    def set_show_name(self, show: int):
        self.attributes["ShowName"] = show
    def get_tag(self):
        return self.attributes["Tag"]
    def attach_tag(self, tag: Tag):
        self.attributes["Tag"] = tag
    def detach_tag(self):
        self.attributes["Tag"] = None

    def __str__(self):
        return "{},{},{},{},{},{},{},{},{},{},{},{},{},{}".format(*self.attributes.values())