from basic import Serializable

"""
    Singleton for each house
"""
class House(Serializable):

    houses = {}

    def __init__(self, header="Russians", attributes=None):
        self.attributes = attributes if attributes is not None else {
            "IQ": 0,
            "Edge": "North",
            "Color": "Gold",
            "Allies": "Russians",
            "Country": "Russians",
            "Credits": 0,
            "NodeCount": 0,
            "TechLevel": 1,
            "PercentBuilt": 0,
            "PlayerControl": False,
        }
        super(House, self).__init__(self.attributes)
        self.attributes = attributes
        self.header = header
        if House.is_house(header):
            House.houses[header] = self

    def get_house(header, attributes={}):
        if header in House.houses:
            return House.houses[header]
        else:
            return House(header, attributes)

    def get_list_string():
        string = "[Houses]\n"
        counter = 0
        for house in House.houses:
            string += "{}={}\n".format(counter, house)
            counter += 1
        return string + '\n'

    def __str__(self):
        return self.header

    def set_iq(self, iq: int):
        self.attributes["IQ"] = iq
    def set_edge(self, edge: str):
        self.attributes["Edge"] = iq
    def set_Color(self, color: str):
        self.attributes["Color"] = color
    def set_allies(self, allies: str):
        self.attributes["Allies"] = allies
    def set_country(self, country):
        self.attributes["Country"] = str(country)
    def set_credits(self, credits: int):
        self.attributes["Credits"] = credits
    def set_node_count(self, nodeCount: int):
        self.attributes["NodeCount"] = nodeCount
    def set_tech_level(self, techlevel: int):
        self.attributes["TechLevel"] = techlevel
    def set_percent_built(self, percent: int):
        self.attributes["PercentBuilt"] = percent
    def set_player_control(self, control: bool):
        self.attributes["PlayerControl"] = control

    @staticmethod
    def is_house(name):
        return name in [
        "Alliance",
        "French",
        "Germans",
        "British",
        "Africans",
        "British",
        "Arabs",
        "Confederation",
        "Russians",
        "Americans",
        "Neutral",
        "Special"]

        # TODO the following are players not houses..
        # "<Player @ A>",
        # "<Player @ B>",
        # "<Player @ C>",
        # "<Player @ D>",
        # "<Player @ E>",
        # "<Player @ F>",
        # "<Player @ G>",
        # "<Player @ H>"]

    def Alliance():
        if "Alliance" not in House.houses:
            House.houses["Alliance"] = House("Alliance")
        return House.houses["Alliance"]
    def French():
        if "French" not in House.houses:
            House.houses["French"] = House("French")
        return House.houses["French"]
    def Germans():
        if "Germans" not in House.houses:
            House.houses["Germans"] = House("Germans")
        return House.houses["Germans"]
    def British():
        if "British" not in House.houses:
            House.houses["British"] = House("British")
        return House.houses["British"]
    def Africans():
        if "Africans" not in House.houses:
            House.houses["Africans"] = House("Africans")
        return House.houses["Africans"]
    def YuriCountry():
        if "YuriCountry" not in House.houses:
            House.houses["YuriCountry"] = House("YuriCountry")
        return House.houses["YuriCountry"]
    def Arabs():
        if "Arabs" not in House.houses:
            House.houses["Arabs"] = House("Arabs")
        return House.houses["Arabs"]
    def Confederation():
        if "Confederation" not in House.houses:
            House.houses["Confederation"] = House("Confederation")
        return House.houses["Confederation"]
    def Russians():
        if "Russians" not in House.houses:
            House.houses["Russians"] = House("Russians")
        return House.houses["Russians"]
    def Americans():
        if "Americans" not in House.houses:
            House.houses["Americans"] = House("Americans")
        return House.houses["Americans"]
    def PlayerA():
        if "<Player @ A>" not in House.houses:
            House.houses["<Player @ A>"] = House("<Player @ A>")
        return House.houses["<Player @ A>"]
    def PlayerB():
        if "<Player @ B>" not in House.houses:
            House.houses["<Player @ B>"] = House("<Player @ B>")
        return House.houses["<Player @ B>"]
    def PlayerC():
        if "<Player @ C>" not in House.houses:
            House.houses["<Player @ C>"] = House("<Player @ C>")
        return House.houses["<Player @ C>"]
    def PlayerD():
        if "<Player @ D>" not in House.houses:
            House.houses["<Player @ D>"] = House("<Player @ D>")
        return House.houses["<Player @ D>"]
    def PlayerE():
        if "<Player @ E>" not in House.houses:
            House.houses["<Player @ E>"] = House("<Player @ E>")
        return House.houses["<Player @ E>"]
    def PlayerF():
        if "<Player @ F>" not in houses:
            House.houses["<Player @ F>"] = House("<Player @ F>")
        return House.houses["<Player @ F>"]
    def PlayerG():
        if "<Player @ G>" not in House.houses:
            House.houses["<Player @ G>"] = House("<Player @ G>")
        return House.houses["<Player @ G>"]
    def PlayerH():
        if "<Player @ H>" not in House.houses:
            House.houses["<Player @ H>"] = House("<Player @ H>")
        return House.houses["<Player @ H>"]
    def from_position(position: int):
        if position == 1:
            return House.PlayerA()
        elif position == 2:
            return House.PlayerB()
        elif position == 3:
            return House.PlayerC()
        elif position == 4:
            return House.PlayerD()
        elif position == 5:
            return House.PlayerE()
        elif position == 6:
            return House.PlayerF()
        elif position == 7:
            return House.PlayerG()
        elif position == 8:
            return House.PlayerH()
        else:
            print("ERROR: invalid player number: {}".format(position))
            return None