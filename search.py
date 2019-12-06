from solitaire import Game
import collections, argparse
import heapq

def dfs(game):
    dp = collections.deque([game.start_state])
    met = set()

    while dp:
        state = dp.pop()
        #state.visualize()

        if game.is_goal_state(state):
            return state.solution

        for s in game.get_successors(state):
            if s not in met:
                dp.append(s)
            met.add(s)

def a_star(game):
    dp = [(27,0,game.start_state)]
    met = set()

    def heuristic(state):
        goal = 27 - sum(state.goal_buffer.values())
        return goal

    while dp:
        _, cost, state = heapq.heappop(dp)
        state.visualize()

        if game.is_goal_state(state):
            return state.solution

        for s in game.get_successors(state):
            if s not in met:
                heapq.heappush(dp, (cost+1+heuristic(s), cost+1, s))
            met.add(s)


def arg_parser_setup():
    parser = argparse.ArgumentParser(description='Test Game logic.')
    parser.add_argument('-f', '--filename', default='test/case1.txt', help='Input test case filename.')
    parser.add_argument('-m', '--method', default='dfs', help='Search method selection')
    parser.add_argument('-v', '--verbose', default=True, help='Whether to print out solution in console')
    return parser.parse_args()

def main():
    search_func_dict = { 'dfs': dfs, 'a_star': a_star, }
    args = arg_parser_setup()
    game = Game(args.filename)
    res = search_func_dict[args.method](game)

    if args.verbose:
        for i,x in enumerate(res): print('Step {}: {}'.format(i, x))


if __name__ == '__main__':
    main()

