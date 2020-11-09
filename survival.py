from logic import *
from houses import *
from map import Map

class Wave():
    def __init__(self, name: str, delay: int, units: [(int,str)], waypoints: [], script, owner=houses.House.PlayerE()):
        self.taskforce = TaskForce({"Name": name + "-tf", "Group": -1})
        for amount, unit in units:
            self.taskforce.add_units(unit, amount)

        self.delay = delay
        self.script = script

        # Team - initialize with empty dict
        self.team = Team()
        self.team.set_taskforce(self.taskforce)
        self.team.set_name(name + "-tm")
        self.team.set_house(owner)
        self.team.set_script(script)

        # Trigger & Tag
        self.trigger = Trigger()
        self.trigger.set_name(name + "-tr")
        self.tag = Tag()
        # TODO if false, no wave will appear at all!
        self.tag.set_repeating(False)
        self.trigger.add_tag(self.tag)
        self.tag.set_trigger(self.trigger)
        self.trigger.add_event(Event.create_ElapsedTime(delay))

        # Actions
        self.trigger.add_action(Action.create_TextTrigger(name))
        for waypoint in waypoints:
            self.trigger.add_action(Action.create_ReinforceByChrono(self.team, waypoint))
    def get_script(self):
        return self.script
    def get_team(self):
        return self.team
    def get_name(self):
        return self.name
    def get_tag(self):
        return self.tag
    def get_delay(self):
        return self.delay
    def get_taskforce(self):
        return self.taskforce
    def get_team(self):
        return self.team
    def get_trigger(self):
        return self.trigger

class SurvivalMap(Map):

    def __init__(self, attacker: int=5):
        super(SurvivalMap, self).__init__()
        self.attacker = houses.House.from_position(attacker)
        self.waves = []

    def set_attacker(self, house):
        self.attacker = attacker
        # TODO set end trigger, iron curtain, countdown timer
        iron_curtain_trigger = Trigger()
        iron_curtain_event = Event.create_ElapsedTime(15)
        iron_curtain_tag = Tag()
        iron_curtain_tag.set_repeating(True)
        # Is this correct? maybe auto link cycle
        iron_curtain_tag.set_trigger(iron_curtain_trigger)
        iron_curtain_trigger.add_tag(iron_curtain_tag)
        iron_curtain_action = Action.create_IronCurtainAt(self.map_obj.get_header().get_player_start_E())
        iron_curtain_trigger.add_action(iron_curtain_action)
        self.map_obj.add_trigger(iron_curtain_trigger)

        win_countdown_trigger = Trigger()
        win_countdown_event = Event.create_MissionTimerExpired()
        win_countdown_action = Action.create_DisableTrigger(iron_curtain_trigger)
        win_countdown_trigger.add_action(win_countdown_action)
        self.map_obj.add_trigger(win_countdown_trigger)

        set_countdown_trigger = Trigger()
        set_countdown_event = Event.create_AnyEvent()
        set_countdown_trigger.add_event(set_countdown_event)
        set_countdown_action = Action.create_TimerSet(3600)
        set_countdown_action_text = Action.create_TimerText("SURVIVE")
        set_countdown_trigger.add_actions([set_countdown_action, set_countdown_action_text])
        self.map_obj.add_trigger(set_countdown_trigger)


    def add_wave(self, wave: Wave):
        self.waves.append(wave)


    def remove_wave(self, wave: Wave):
        self.waves.remove(wave)

    def serialize(self):
        """
            Here we actually assemble the map to prevent inconsistencies
        """
        for wave in self.waves:
            self.add_taskforce(wave.get_taskforce())
            team = wave.get_team()
            team.set_house(self.attacker)
            self.add_team(team)
            self.add_trigger(wave.get_trigger())
            self.add_tag(wave.get_tag())

        return super().serialize()