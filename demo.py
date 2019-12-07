from solitaire import Game
from search import dfs, arg_parser_setup

def demo():
    args = arg_parser_setup()
    game = Game()
    solution = dfs(game, args)
    game.print_actions(solution)

if __name__ == '__main__':
    demo()

