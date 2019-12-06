from solitaire import Game
import collections, argparse, random
import heapq

def dfs(game, args):
    dp = collections.deque([game.start_state])
    met = set()

    while dp:
        state = dp.pop()
        if args.verbose:
            state.visualize()

        if game.is_goal_state(state):
            return state.solution

        important_states, other_states = game.get_successors(state)
        for s in important_states + other_states:
            if s not in met:
                dp.append(s)
            met.add(s)

def a_star(game, args):
    seed = args.seed
    while True:
        solution = a_star_solver(game, verbose=args.verbose, max_depth=args.maxdepth)
        if solution: break
        print('Fail with seed {}'.format(seed))
        seed += 1
        random.seed(seed)
        break
    return solution

def a_star_solver(game, verbose=False, max_depth=None):

    def score(state):
        goal = 27 - sum(state.goal_buffer.values())
        return goal

    def dig_out_distance(state):
        # assume on average it tooks 100 steps to complete the game
        # assume the last 7 steps are all score step
        TOTAL_STEP = 100
        LAST_N_STEP = 7

        average_step = (TOTAL_STEP - LAST_N_STEP) / (27 - LAST_N_STEP)
        complete = sum(state.goal_buffer.values())

        if complete > 27 - LAST_N_STEP:
            padding = 27 - complete
        else:
            padding = complete * average_step

        targets = set(k+str(v+1) for k,v in state.goal_buffer.items())
        dig_out_distances = []
        dig_out_distances += [len(column)-column.index(card)-1 for column in state.deck for card in column if card in targets]
        dig_out_distances += [0 for card in state.goal_buffer if card in targets]
        dig_out_distance = min(dig_out_distances)

        return dig_out_distance + padding

    heuristic = dig_out_distance
    initial_h = 100
    dp = [(initial_h,0,game.start_state)]
    met = set()

    while dp:
        _, cost, state = heapq.heappop(dp)

        # give up
        if max_depth and cost > max_depth: return

        if verbose:
            state.visualize()

        if game.is_goal_state(state):
            return state.solution

        important_states, other_states = game.get_successors(state)
        if len(important_states) > 3:
            states = important_states
        elif len(important_states) + len(other_states) < 3:
            states = important_states + other_states
        else:
            states = important_states + random.sample(other_states, 3-len(important_states))

        for s in states:
            if s not in met:
                heapq.heappush(dp, (cost+1+heuristic(s), cost+1, s))
            met.add(s)


def arg_parser_setup():
    parser = argparse.ArgumentParser(description='Test Game logic.')
    parser.add_argument('-f', '--filename', default='test/case1.txt', help='Input test case filename.')
    parser.add_argument('-m', '--method', default='dfs', help='Search method selection')
    parser.add_argument('-d', '--maxdepth', default=200, type=int, help='Max searching depth for a_star algorithm')
    parser.add_argument('-s', '--seed', default=2019, type=int, help='Random seed')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='Whether to print out searching details')
    return parser.parse_args()

def main():
    search_func_dict = { 'dfs': dfs, 'a_star': a_star}
    args = arg_parser_setup()

    random.seed(args.seed)
    game = Game(args.filename)
    actions = search_func_dict[args.method](game, args)

    game.print_actions(actions)


if __name__ == '__main__':
    main()

