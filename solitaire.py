import collections
import argparse, copy
from functools import lru_cache, total_ordering


def get_num(card):
    return int(card[1:]) if len(card) > 1 else None

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
    __slots__ = ['buffer_area', 'buffer_size', 'goal_buffer', 'collected', 'deck', 'flower_in_deck', 'solution']

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

    def __hash__(self):
        deck = hash(tuple(set(tuple(x for x in c) for c in self.deck)))
        buffer_area = hash(tuple(set(x for x in self.buffer_area)))
        goal = hash(tuple(self.goal_buffer.values()))
        flower = hash(self.flower_in_deck)
        return hash((deck, buffer_area, goal, flower))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __gt__(self, other):
        return sum(self.goal_buffer.values()) > sum(other.goal_buffer.values())

    def copy(self):
        return copy.deepcopy(self)

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
            print(e)
            state.visualize()

    def is_goal_state(self, state):
        # check whether is goal state
        return all(x == 9 for x in state.goal_buffer.values())

    @lru_cache(maxsize=None)
    def get_successors(self, state):
        # add code to return list of successor states
        if self.is_goal_state(state): return []

        # get rid of the flower once met
        if 'f' in [c[-1] for c in state.deck if c]:
            state.flower_in_deck = False
            state.solution.append('remove flower')
            for i in range(len(state.deck)):
                if state.deck[i] and state.deck[i][-1] == 'f':
                    state.deck[i].pop()
        res = []

        def auto_put_to_goal(state):
            type, target = min(state.goal_buffer.items(), key=lambda x:x[1])
            for c in state.deck:
                if c and get_type(c[-1]) == type and get_num(c[-1]) == target+1:
                    tmp = c.pop()
                    state.goal_buffer[type] = get_num(tmp)
                    state.solution.append('{} to goal'.format(str(tmp)))
                    return True

        while auto_put_to_goal(state):
            pass

        def collect_all_collectables(state, type):
            if not state.collected[type] and sum(x[-1]==type for x in state.deck if x) + sum(x==type for x in state.buffer_area) == 4:
                new_state = state.copy()
                new_state.buffer_size -= 1
                new_state.buffer_area = [x for x in new_state.buffer_area if x != type]
                for c in new_state.deck:
                    if c and c[-1] == type:
                        c.pop()
                new_state.collected[type] = True
                new_state.solution.append('collect {}'.format(type))
                res.append(new_state)

        def put_to_buffer(state, i):
            new_state = state.copy()
            tmp = new_state.deck[i].pop()
            new_state.buffer_area.append(tmp)
            new_state.solution.append('{} at {} to buffer'.format(str(tmp),i+1))
            res.append(new_state)

        def put_to_goal(state, i, in_deck=True):
            new_state = state.copy()
            if in_deck:
                tmp = new_state.deck[i].pop()
                new_state.solution.append('{} at {} to goal'.format(str(tmp),i+1))
            else:
                tmp = new_state.buffer_area[i]
                new_state.solution.append('{} in buffer to goal'.format(str(tmp)))
                del new_state.buffer_area[i]
            new_state.goal_buffer[get_type(tmp)] = get_num(tmp)
            res.append(new_state)

        def put_to_deck(state, j, i, from_deck=True):
            new_state = state.copy()
            if from_deck:
                tmp = new_state.deck[i].pop()
                new_state.deck[j].append(tmp)
                new_state.solution.append('{} at {} to {}'.format(str(tmp), i+1, j+1))
            else:
                tmp = new_state.buffer_area[i]
                new_state.deck[j].append(tmp)
                new_state.solution.append('{} in buffer to deck {}'.format(str(tmp), j+1))
                del new_state.buffer_area[i]
            res.append(new_state)

        for x in state.GOALS:
            collect_all_collectables(state, x)

        for i,c in enumerate(state.deck):
            if not c: continue
            card = c[-1]
            if get_num(card) and state.goal_buffer[get_type(card)] == get_num(card) - 1:
                put_to_goal(state, i)

            for j, col in enumerate(state.deck):
                if col and get_num(card) and j != i and get_type(col[-1]) != get_type(card) and get_num(col[-1]) == get_num(card) + 1:
                    put_to_deck(state, j, i)
                elif not col:
                    put_to_deck(state, j, i)

            if len(state.buffer_area) < state.buffer_size:
                put_to_buffer(state, i)

        for i,card in enumerate(state.buffer_area):
            if get_num(card) and state.goal_buffer[get_type(card)] == get_num(card) - 1:
                put_to_goal(state, i, in_deck=False)

            for j, col in enumerate(state.deck):
                if col and get_num(card) and j != i and get_type(col[-1]) != get_type(card) and get_num(col[-1]) == get_num(card) + 1:
                    put_to_deck(state, j, i, from_deck=False)
                elif not col:
                    put_to_deck(state, j, i, from_deck=False)
        return set(res)

    def _auto_proceed(self, state):
        # return the original state if no auto proceed is required
        # otherwise perform the auto proceed and return the result
        ss = self.get_successors(state)
        return self._auto_proceed(ss[0]) if len(ss) == 1 else state

def arg_parser_setup():
    parser = argparse.ArgumentParser(description='Test Game logic.')
    parser.add_argument('-f', '--filename', default='test/case1.txt', help='Input test case filename.')
    return parser.parse_args()

if __name__ == '__main__':
    args = arg_parser_setup()
    g = Game(args.filename)
    g.is_valid_state(g.start_state)
