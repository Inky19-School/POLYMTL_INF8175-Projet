import argparse

import main_abalone
from os.path import basename, splitext, dirname
import sys
import os

def games_agents(args):

    list_players = vars(args).get("players_list")
    print(list_players)
    time_limit = 15*60
    folder = dirname(list_players[0])
    sys.path.append(folder)
    player1_class = __import__(splitext(basename(list_players[0]))[0], fromlist=[None])
    folder = dirname(list_players[1])
    sys.path.append(folder)
    player2_class = __import__(splitext(basename(list_players[1]))[0], fromlist=[None])
    player1 = player1_class.MyPlayer("W", name=splitext(basename(list_players[0]))[0]+"_1", time_limit=time_limit)
    player2 = player2_class.MyPlayer("B", name=splitext(basename(list_players[1]))[0]+"_2", time_limit=time_limit)

    nb_match = args.nb_match
    p1_win = 0
    p2_win = 0
    for i in range(nb_match):
        print("iteration : ",i)

        master = main_abalone.play(player1=player1, player2=player2, log_level="DEBUG", port=16001, address="localhost", gui=False, record=False, gui_path="", config="classic")
        print(player1 == master.get_winner()[0])
        if player1 == master.get_winner()[0]:
            p1_win += 1
        else:
            p2_win += 1

    print("Il y a ",p1_win," victoire de l'agent 1")
    print("Il y a ",p2_win," victoire de l'agent 2")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--players_list",nargs="*", help='The players')
    parser.add_argument('--nb_match',default=10,type=int,help="nombre de parties")

    args = parser.parse_args()
    games_agents(args)