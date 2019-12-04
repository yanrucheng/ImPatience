import collections

class Card:
    __slots__ = ['type', 'num']

    def __init__(self, card_type, num=None):
        self.type = card_type
        self.num = num

    def __str__(self):
        return '{}{}'.format(self.card_type, self.num) if self.num else self.type


class GameState:
    '''Game state stores all the information required to reproduce a game state'''
    __slots__ = ['buffer_area', 'buffer_size', 'goal_area', 'hands']

    def __init__(self, buffer_size=3, goal_size=3, deck_column=8):
        self.buffer_area = []
        self.buffer_size = buffer_size

        self.goal_buffer = [0]*goal_size

        self.hands = [collections.deque() for _ in range(deck_column)]

    def visualize(self):
        raise NotImplementedError

    def __hash__(self):
        raise NotImplementedError

    def __eq__(self):
        raise NotImplementedError



class Game:
    '''This class control the game flow'''

    def __init__(self, **kw):
        self.start_state = self.get_start_state(**kw)

    def get_start_state(self, **kw):
        state = GameState(**kw)
        # add code to init the deck of the state
        raise NotImplementedError

    def is_goal_state(self, state):
        # check whether is goal state
        return all(x == 9 for x in state.goal_buffer)

    def get_successors(self, state):
        # add code to return list of successor states
        raise NotImplementedError

    def auto_proceed(self, state):
        # return the original state if no auto proceed is required
        # otherwise perform the auto proceed and return the result
        raise NotImplementedError

