import collections
import argparse
from functools import lru_cache, total_ordering

@lru_cache()
def get_num(card):
    return int(card[1:]) if len(card) > 1 else None

@lru_cache()
def get_type(card):
    return card[0]

@total_ordering
class GameState:
    '''
    Game state stores all the information required to reproduce a game state.
    There are 3 buffer slots.
    There are 3 goal slots, namely slots for red, black and green.
    There are 8 columns on the deck. each start with 5 cards.
    '''
    __slots__ = ['buffer_area', 'buffer_size', 'goal_buffer', 'collected', 'deck', 'flower_in_deck',
            'solution', 'history', 'locked_to_keys', 'key_to_locked']

    ORIGINAL_BUFFER_SIZE = 3
    GOALS = ['r', 'g', 'b']
    DECK_COLUMN_NUM = 8

    def __init__(self):
        self.buffer_area = []
        self.buffer_size = self.ORIGINAL_BUFFER_SIZE
        self.goal_buffer = {x:0 for x in self.GOALS}
        self.collected = {x:False for x in self.GOALS}
        self.deck = [[] for _ in range(self.DECK_COLUMN_NUM)]
        self.flower_in_deck = True

        # solution is not calculated in hash
        self.solution = []
        self.history = set()
        self.locked_to_keys = {}
        self.key_to_locked = {}

    def __hash__(self):
        deck = ' '.join(sorted(''.join(l) for l in self.deck))
        buffer_area = ' '.join(sorted(x for x in self.buffer_area))
        goal = str(self.goal_buffer.values())
        flower = str(self.flower_in_deck)
        #print(deck, buffer_area, goal, flower)
        return hash(deck + buffer_area + goal + flower)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __gt__(self, other):
        return sum(self.goal_buffer.values()) > sum(other.goal_buffer.values())

    def copy(self):
        state = GameState()
        state.buffer_area = list(self.buffer_area)
        state.buffer_size = self.buffer_size
        state.goal_buffer = dict(self.goal_buffer)
        state.collected = dict(self.collected)
        state.deck = [list(l) for l in self.deck]
        state.flower_in_deck = self.flower_in_deck

        state.solution = list(self.solution)
        state.history = set(self.history)
        state.locked_to_keys = dict(self.locked_to_keys)
        state.key_to_locked = dict(self.key_to_locked)

        return state

    def record(self):
        self.history.add(hash(self))

    def visualize(self):
        print()
        print('Buffer area: {}'.format(', '.join([str(c) for c in self.buffer_area])))
        print('Goal area: {}'.format(', '.join([k+str(v) for k,v in self.goal_buffer.items()])))
        print('Deck:')
        row_fmt = '{:>7}' * self.DECK_COLUMN_NUM
        for i in range(max(len(c) for c in self.deck)):
            print(row_fmt.format(*[str(c[i]) if len(c)>i else '' for c in self.deck]))
        print()

MoveAction = collections.namedtuple('MoveAction', ['card', 'source', 'source_position', 'to', 'to_position'])
ScoreAction = collections.namedtuple('ScoreAction', ['card', 'source', 'source_position'])
CollectAction = collections.namedtuple('CollectAction', ['target'])

class Game:
    '''This class control the game flow'''
    def __init__(self, deck_filename='test/case1.txt'):
        self.start_state = self._get_start_state(deck_filename)

    def _get_start_state(self, deck_filename):
        state = GameState()
        with open(deck_filename, 'r') as f:
            lines = f.readlines()
            for column, line in zip(state.deck, lines):
                for x in line.strip().split():
                    column.append(x)
        state.record()
        assert self.is_valid_state(state), 'invalid state'
        return state

    def is_valid_state(self, state):
        cards = sum([list(c) for c in state.deck], []) + state.buffer_area # flatten all the cards in deck
        # check buffer size
        try:
            assert len(state.buffer_area) <= state.buffer_size, \
                'Buffer area overflow. Buffer: {}, collected: {}'.format(
                    state.buffer_area, [x for x,v in state.collected.items() if v])

            # check flower
            assert ('f' in cards) == state.flower_in_deck, 'Flower card is missing'

            # check collectables
            assert all(cards.count(x) == 4 or state.collected[x] for x in state.GOALS), \
                'Collectable card is missing'

            # check cards with numbers
            d = collections.defaultdict(list)
            _ = [ d[get_type(card)].append(get_num(card)) for column in state.deck for card in column if len(card)==2 ]
            _ = [ d[get_type(card)].append(get_num(card)) for card in state.buffer_area ]
            for x,nums in d.items():
                missing = set(range(state.goal_buffer[x]+1,10)) - set(nums)
                if missing:
                    raise AssertionError('{} is missing'.format('{}{}'.format(x, list(missing)[0])))

        except AssertionError as e:
            state.visualize()
            print(e)
            return False
        else:
            return True

    def is_goal_state(self, state):
        # check whether is goal state
        return all(x == 9 for x in state.goal_buffer.values())

    def _lock_state(self, state, action):
        '''Internal function for performance improvement.'''
        if isinstance(action, ScoreAction) or isinstance(action, CollectAction):
            return
        # put a lock to the destination position
        locked = (action.to, action.to_position)
        # action involving key positions will undo the lock on a position
        # locked positon itself is also a key position
        keys = [(action.source, action.source_position), locked]
        state.locked_to_keys[locked] = keys
        for k in keys:
            state.key_to_locked[k] = locked

    def _unlock_state(self, state, action):
        '''Internal function for performance improvement.'''
        def unlock(key):
            if key in state.key_to_locked:
                locked = state.key_to_locked[key]
                for locker in state.locked_to_keys[locked]:
                    del state.key_to_locked[locker]
                del state.locked_to_keys[locked]

        if isinstance(action, MoveAction):
            keys = [(action.source, action.source_position),
                    (action.to, action.to_position)]
        elif isinstance(action, ScoreAction):
            keys = [(action.source, action.source_position)]
        elif isinstance(action, CollectAction):
            # collect flower does not unlock anything
            if action.target == 'flower': return
            # collect color cards does unlock 4 positions at most
            keys = [('buffer', i) for i,card in enumerate(state.buffer_area) if card==action.target] +\
                   [('deck', i) for i, column in enumerate(state.deck) if column and column[-1]==action.target]

        for k in keys: unlock(k)

    def _is_action_locked(self, state, action):
        '''Internal function for performance improvement.'''
        if isinstance(action, ScoreAction) or isinstance(action, CollectAction):
            return False

        return (action.source, action.source_position) in state.locked_to_keys

    def take_actions(self, state, actions, visualize=False):
        for action in actions:
            state = self.take_action(state, action, auto_proceed=False)
            if visualize: state.visualize()
        return state

    def take_action( self, state, action, auto_proceed=True):
        '''Generate a new successor state based on the given action. Record the new hash'''

        if self._is_action_locked(state, action): return None

        new_state = state.copy()

        if isinstance(action, MoveAction):

            # handling card source
            if action.source == 'deck': new_state.deck[action.source_position].pop()
            elif action.source == 'buffer': new_state.buffer_area.pop(action.source_position)

            # handling card destination
            if action.to=='deck':
                new_state.deck[action.to_position].append(action.card)
            elif action.to=='buffer':
                new_state.buffer_area.append(action.card)

        elif isinstance(action, ScoreAction):
            if action.source == 'deck': new_state.deck[action.source_position].pop()
            elif action.source == 'buffer': new_state.buffer_area.pop(action.source_position)
            new_state.goal_buffer[get_type(action.card)] = get_num(action.card)

        elif isinstance(action, CollectAction):
            if action.target == 'flower':
                new_state.flower_in_deck = False
                for i in range(len(new_state.deck)):
                    if new_state.deck[i] and new_state.deck[i][-1] == 'f':
                        new_state.deck[i].pop(); break
            else:
                new_state.buffer_size -= 1
                new_state.buffer_area = [x for x in new_state.buffer_area if x != action.target]

                for i,c in enumerate(new_state.deck):
                    if c and c[-1] == action.target:
                        c.pop()
                new_state.collected[action.target] = True

        if hash(new_state) in new_state.history: return None

        self._lock_state(new_state, action)
        self._unlock_state(new_state, action)
        new_state.record()
        new_state.solution.append(action)

        if auto_proceed: new_state = self.auto_proceed(new_state)

        return new_state

    def print_actions(self, actions):
        def action_str(action):
            if isinstance(action, CollectAction):
                return 'collect {}'.format(action.target)
            elif isinstance(action, ScoreAction):
                return '{} at {} {} to goal'.format(*action)
            elif isinstance(action, MoveAction):
                return '{} at {} {} to {} {}'.format(*action)

        for i,action in enumerate(actions, 1):
            print('Step {}: {}'.format(i, action_str(action)))

    def auto_proceed(self, state):
        # get rid of the flower once met
        if state.flower_in_deck and 'f' in [c[-1] for c in state.deck if c]:
            state = self.take_action(state, CollectAction('flower'), auto_proceed=False)
            assert state, 'auto proceed failure'

        # put the smallest exposed card to goal
        def auto_put_to_goal(state):
            color, min_value = min(state.goal_buffer.items(), key=lambda x:x[1])
            target_card = color+str(min_value+1)
            for i,column in enumerate(state.deck):
                if column and column[-1] == target_card:
                    state = self.take_action(state, ScoreAction(target_card, 'deck', i), auto_proceed=False)
                    assert state, 'auto proceed failure'
                    return state

        while True:
            new_state = auto_put_to_goal(state)
            if not new_state: break
            state = new_state

        return state

    @lru_cache(maxsize=None)
    def get_successors(self, state):
        # add code to return list of successor states
        if self.is_goal_state(state): return []

        # if the successor is already visited, a None will be stored in states
        other_state = []
        important_states = []

        def try_collect_all_collectables(color):
            if not state.collected[color] and (len(state.buffer_area) - state.buffer_size or color in state.buffer_area) and\
                    sum(x[-1]==color for x in state.deck if x) + sum(x==color for x in state.buffer_area) == 4:
                important_states.append(self.take_action(state, CollectAction(color)))

        for color in state.GOALS:
            try_collect_all_collectables(color)

        for i,column in enumerate(state.deck):
            if not column: continue
            card = column[-1]

            if get_num(card) and state.goal_buffer[get_type(card)] == get_num(card) - 1:
                important_states.append(self.take_action(state, ScoreAction(card, 'deck', i)))

            for j, col in enumerate(state.deck):
                if (not col) or (get_num(card) and j != i and \
                        get_type(col[-1]) != get_type(card) and get_num(col[-1]) == get_num(card) + 1):
                    other_state.append(self.take_action(state, MoveAction(card, 'deck', i, 'deck', j)))

            if len(state.buffer_area) < state.buffer_size:
                other_state.append(self.take_action(state, MoveAction(card, 'deck', i, 'buffer', None)))

        for i,card in enumerate(state.buffer_area):
            if get_num(card) and state.goal_buffer[get_type(card)] == get_num(card) - 1:
                important_states.append(self.take_action(state, ScoreAction(card, 'buffer', i)))

            for j, col in enumerate(state.deck):
                if (not col) or (get_num(card) and j != i and \
                        get_type(col[-1]) != get_type(card) and get_num(col[-1]) == get_num(card) + 1):
                    other_state.append(self.take_action(state, MoveAction(card, 'buffer', i, 'deck', j)))

        other_state = list(set(state for state in other_state if state))
        return important_states, other_state

def arg_parser_setup():
    parser = argparse.ArgumentParser(description='Test Game logic.')
    parser.add_argument('-f', '--filename', default='test/case1.txt', help='Input test case filename.')
    return parser.parse_args()

if __name__ == '__main__':
    args = arg_parser_setup()
    g = Game(args.filename)
    g.is_valid_state(g.start_state)
