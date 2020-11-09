from logic import *
from houses import *


class GlobalTriggers():
    """ Creates and manages instances of common triggers """
    triggers = {}

    @staticmethod
    def GivePlayerAt(position: int):
        identifier = "give_{}".format(position)

        if identifier not in triggers:
            event = Event.create_AnyEvent()
            action = Action.create_ChangeHouse(House.from_position(position))
            tr = Trigger()
            tr.add_event(event)
            tr.add_action(action)
            triggers[identifier] = tr
        return triggers[identifier]