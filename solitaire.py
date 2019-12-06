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
            'solution', 'history', 'locked_to_locker', 'locker_to_locked']

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
        self.locked_to_locker = {}
        self.locker_to_locked = {}

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
        state.locked_to_locker = dict(self.locked_to_locker)
        state.locker_to_locked = dict(self.locker_to_locked)

        return state

    def record(self):
        self.history.add(hash(self))

    def visualize(self):
        print()
        print('Buffer area: {}'.format(', '.join([str(c) for c in self.buffer_area])))
        print('Goal area: {}'.format(', '.join([k+str(v) for k,v in self.goal_buffer.items() if v])))
        print('Deck:')
        row_fmt = '{:>7}' * self.DECK_COLUMN_NUM
        for i in range(max(len(c) for c in self.deck)):
            print(row_fmt.format(*[str(c[i]) if len(c)>i else '' for c in self.deck]))
        print()

class Game:
    '''This class control the game flow'''
    def __init__(self, deck_filename='test/case1.txt'):
        self.start_state = self.get_start_state(deck_filename)

    def get_start_state(self, deck_filename):
        state = GameState()
        with open(deck_filename, 'r') as f:
            lines = f.readlines()
            for column, line in zip(state.deck, lines):
                for x in line.strip().split():
                    column.append(x)
        state.record()
        self.is_valid_state(state)
        return state

    def is_valid_state(self, state):
        cards = sum([list(c) for c in state.deck], []) + state.buffer_area # flatten all the cards in deck
        # check buffer size
        try:
            assert len(state.buffer_area) <= state.buffer_size - sum(state.collected.values()), \
                'Buffer area overflow. Buffer: {}, collected: {}'.format(
                    state.buffer_area, [x for x,v in state.collected.items() if v])

            # check flower
            assert ('f' in cards) == state.flower_in_deck, 'Flower card is missing'

            # check collectables
            assert all(cards.count(x) == 4 or state.collected[x] for x in state.GOALS), \
                'Collectable card is missing'

            # check cards with numbers
            d = collections.defaultdict(list)
            _ = [ d[x[0]].append(x[1]) for x in state.GOALS if len(x)==2 ]
            assert all(list(range(state.goal_buffer[x]+1,10)) == sorted(nums) for x,nums in d.items()), \
                'Number card is missing'

        except AssertionError as e:
            state.visualize()
            raise e

    def is_goal_state(self, state):
        # check whether is goal state
        return all(x == 9 for x in state.goal_buffer.values())

    def take_action(
        self, state,
        source='deck', source_position='', to='goal', to_position='',
        collect_target=None, auto_proceed=True
    ):
        '''Generate a new successor state based on the given action. Record the new hash'''

        def unlock(state, inv):
            if inv in state.locker_to_locked:
                locked = state.locker_to_locked[inv]
                for locker in state.locked_to_locker[locked]:
                    del state.locker_to_locked[locker]
                del state.locked_to_locker[locked]

        # determine whether this action is locked
        if (source == 'deck' and source_position in state.locked_to_locker) or\
                (source == 'buffer' and source_position + state.DECK_COLUMN_NUM in state.locked_to_locker):
            return None

        target_map = {'goal':'', 'buffer':len(state.buffer_area)+state.DECK_COLUMN_NUM, 'deck':to_position}
        source_map = {'deck':source_position,
            'buffer':source_position+state.DECK_COLUMN_NUM if isinstance(source_position, int) else 0}

        new_state = state.copy()
        if not collect_target:
            card = new_state.deck[source_position].pop() if source == 'deck' else \
                    new_state.buffer_area.pop(source_position)

            # locking process
            if to != 'goal':
                locked = target_map[to]
                involved = [locked, source_map[source]]
                # if not put to goal, the destination is locked
                new_state.locked_to_locker[locked] = involved
                for l in involved:
                    new_state.locker_to_locked[l] = locked

            # unlocking process
            involved = [source_map[source], target_map[to]]
            for inv in involved:
                unlock(new_state, inv)

            # handling card destination
            if to=='goal':
                new_state.goal_buffer[get_type(card)] = get_num(card)
            elif to=='deck':
                new_state.deck[to_position].append(card)
            elif to=='buffer':
                new_state.buffer_area.append(card)


        elif  collect_target == 'flower':
            new_state.flower_in_deck = False
            for i in range(len(new_state.deck)):
                if new_state.deck[i] and new_state.deck[i][-1] == 'f':
                    new_state.deck[i].pop(); break

            # collect flower does not unlock anything

        else:
            involved = []
            if collect_target in new_state.buffer_area: involved.append('buffer')

            new_state.buffer_size -= 1
            new_state.buffer_area = [x for x in new_state.buffer_area if x != collect_target]

            for i,c in enumerate(new_state.deck):
                if c and c[-1] == collect_target:
                    c.pop()
                    involved.append(i)
            new_state.collected[collect_target] = True

            for inv in involved:
                unlock(new_state, inv)


        if hash(new_state) in new_state.history:
            return None

        new_state.record()
        if collect_target:
            new_state.solution.append('collect {}'.format(collect_target))
        else:
            if isinstance(source_position, int): source_position += 1
            if isinstance(to_position, int): to_position += 1
            new_state.solution.append('{} at {} {} to {} {}'.format(card, source, source_position, to, to_position))

        if auto_proceed:
            new_state = self.auto_proceed(new_state)

        return new_state

    def auto_proceed(self, state):
        # get rid of the flower once met
        if state.flower_in_deck and 'f' in [c[-1] for c in state.deck if c]:
            state = self.take_action(state, collect_target='flower', auto_proceed=False)
            assert state, 'auto proceed failure'

        # put the smallest exposed card to goal
        def auto_put_to_goal(state):
            type, target = min(state.goal_buffer.items(), key=lambda x:x[1])
            for i,c in enumerate(state.deck):
                if c and get_type(c[-1]) == type and get_num(c[-1]) == target+1:
                    state = self.take_action(state, source='deck', source_position=i, to='goal', auto_proceed=False)
                    assert state, 'auto proceed failure'
                    return state

        while True:
            tmp = auto_put_to_goal(state)
            if not tmp: break
            state = tmp

        return state

    @lru_cache(maxsize=None)
    def get_successors(self, state):
        # add code to return list of successor states
        if self.is_goal_state(state): return []

        res = [] # if the successor is already visited, a None will be stored in res
        def collect_all_collectables(state, type):
            if not state.collected[type] and (len(state.buffer_area) - state.buffer_size or type in state.buffer_area) and\
                    sum(x[-1]==type for x in state.deck if x) + sum(x==type for x in state.buffer_area) == 4:
                res.append(self.take_action(state, collect_target=type))

        for x in state.GOALS:
            collect_all_collectables(state, x)

        for i,c in enumerate(state.deck):
            if not c: continue
            card = c[-1]

            if get_num(card) and state.goal_buffer[get_type(card)] == get_num(card) - 1:
                res.append(self.take_action(state, source='deck', source_position=i, to='goal'))

            for j, col in enumerate(state.deck):
                if col and get_num(card) and j != i and \
                        get_type(col[-1]) != get_type(card) and get_num(col[-1]) == get_num(card) + 1:
                    res.append(self.take_action(state, source='deck', source_position=i, to='deck', to_position=j))
                elif not col:
                    res.append(self.take_action(state, source='deck', source_position=i, to='deck', to_position=j))

            if len(state.buffer_area) < state.buffer_size:
                res.append(self.take_action(state, source='deck', source_position=i, to='buffer'))

        for i,card in enumerate(state.buffer_area):
            if get_num(card) and state.goal_buffer[get_type(card)] == get_num(card) - 1:
                res.append(self.take_action(state, source='buffer', source_position=i, to='goal'))

            for j, col in enumerate(state.deck):
                if col and get_num(card) and j != i and \
                        get_type(col[-1]) != get_type(card) and get_num(col[-1]) == get_num(card) + 1:
                    res.append(self.take_action(state, source='buffer', source_position=i, to='deck', to_position=j))
                elif not col:
                    res.append(self.take_action(state, source='buffer', source_position=i, to='deck', to_position=j))

        states = []
        met = set()
        for x in res:
            if x and x not in met:
                met.add(x)
                states.append(x)

        return states

def arg_parser_setup():
    parser = argparse.ArgumentParser(description='Test Game logic.')
    parser.add_argument('-f', '--filename', default='test/case1.txt', help='Input test case filename.')
    return parser.parse_args()

if __name__ == '__main__':
    args = arg_parser_setup()
    g = Game(args.filename)
    g.is_valid_state(g.start_state)
