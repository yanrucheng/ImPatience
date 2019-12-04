from solitaire import Game
import collections, argparse
import heapq

def dfs(game):
    dp = [game.start_state]
    met = set()

    while dp:
        state = dp.pop()
        #state.visualize()
        #print(hash(state))

        if game.is_goal_state(state):
            return state.solution

        states = game.get_successors(state)
        for s in states:
            if s not in met:
                dp.append(s)
            met.add(s)

def star(game):
    dp = [(40,0,game.start_state)]
    met = set()

    def heuristic(state):
        goal = 29 - sum(state.goal_buffer.values())
        collected = 3 - sum(state.collected.values())
        height = 13 - max(len(c) for c in state.deck)
        vacancy = 3+8-1 - sum(1 for c in state.deck if not c) + 3 - len(state.buffer_area)

        type,v = min(state.goal_buffer.items(),key=lambda x:x[1])
        n = type+str(v+1)
        for c in state.deck:
            for i,x in enumerate(c):
                if x == n:
                    next_step = len(c) - i - 1
        if n in state.buffer_area:
            next_step = 0

        return goal + next_step

    while dp:
        _, cost, state = heapq.heappop(dp)
        state.visualize()
        #print(hash(state))

        if game.is_goal_state(state):
            return state.solution

        for s in game.get_successors(state):
            if s not in met:
                heapq.heappush(dp, (cost+1+heuristic(s), cost+1, s))
            met.add(s)


def arg_parser_setup():
    parser = argparse.ArgumentParser(description='Test Game logic.')
    parser.add_argument('-f', '--filename', default='test/case1.txt', help='Input test case filename.')
    return parser.parse_args()

if __name__ == '__main__':
    args = arg_parser_setup()
    game = Game(args.filename)
    state = game.start_state
    res = dfs(game)
    for i,x in enumerate(res):
        print(i,x)

