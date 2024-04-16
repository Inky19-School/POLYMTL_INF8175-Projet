import argparse
import asyncio
import os
from os.path import basename, splitext, dirname
import platform
import sys
from typing import List

from loguru import logger
from board_abalone import BoardAbalone
from player_abalone import PlayerAbalone
from master_abalone import MasterAbalone
from game_state_abalone import GameStateAbalone
from seahorse.player.proxies import InteractivePlayerProxy, LocalPlayerProxy, RemotePlayerProxy
from seahorse.utils.gui_client import GUIClient
from seahorse.utils.recorders import StateRecorder
from seahorse.game.game_layout.board import Piece
from seahorse.utils.custom_exceptions import PlayerDuplicateError
from argparse import RawTextHelpFormatter


def add_win(winner:PlayerAbalone, player1:PlayerAbalone, player2:PlayerAbalone, win:List[int]) -> List[int]:    
    if winner.get_id() == player1.get_id():
        win[0] += 1
    elif winner.get_id() == player2.get_id():
        win[1] += 1
    return win

def add_scores(total_score:List[int], scores:dict[int, float] , player1:PlayerAbalone, player2:PlayerAbalone) -> None:
    total_score[0] += scores[player1.get_id()]
    total_score[1] += scores[player2.get_id()]

def play(player1, player2, log_level, port, address, gui, record, gui_path, config) :
    list_players = [player1, player2]
    init_scores = {player1.get_id(): 0, player2.get_id(): 0}
    dim = [17, 9]
    env = {}
    # 0 case non accessible
    # 1 case player 1
    # 2 case player 2
    # 3 case vide accessible
    classic = [ # CLASSIQUE
        [0, 0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 1, 0, 0, 0],
        [0, 0, 1, 0, 1, 0, 3, 0, 0],
        [0, 1, 0, 1, 0, 3, 0, 3, 0],
        [1, 0, 1, 0, 1, 0, 3, 0, 3],
        [0, 1, 0, 1, 0, 3, 0, 3, 0],
        [1, 0, 1, 0, 3, 0, 3, 0, 3],
        [0, 3, 0, 3, 0, 3, 0, 3, 0],
        [3, 0, 3, 0, 3, 0, 3, 0, 3],
        [0, 3, 0, 3, 0, 3, 0, 3, 0],
        [3, 0, 3, 0, 3, 0, 2, 0, 2],
        [0, 3, 0, 3, 0, 2, 0, 2, 0],
        [3, 0, 3, 0, 2, 0, 2, 0, 2],
        [0, 3, 0, 3, 0, 2, 0, 2, 0],
        [0, 0, 3, 0, 2, 0, 2, 0, 0],
        [0, 0, 0, 2, 0, 2, 0, 0, 0],
        [0, 0, 0, 0, 2, 0, 0, 0, 0],
    ]
    alien = [ # ALIEN
            [0, 0, 0, 0, 2, 0, 0, 0, 0],
            [0, 0, 0, 3, 0, 3, 0, 0, 0],
            [0, 0, 2, 0, 2, 0, 3, 0, 0],
            [0, 3, 0, 1, 0, 2, 0, 3, 0],
            [2, 0, 1, 0, 1, 0, 3, 0, 3],
            [0, 2, 0, 2, 0, 3, 0, 3, 0],
            [3, 0, 1, 0, 2, 0, 3, 0, 3],
            [0, 2, 0, 2, 0, 3, 0, 3, 0],
            [3, 0, 3, 0, 3, 0, 3, 0, 3],
            [0, 3, 0, 3, 0, 1, 0, 1, 0],
            [3, 0, 3, 0, 1, 0, 2, 0, 3],
            [0, 3, 0, 3, 0, 1, 0, 1, 0],
            [3, 0, 3, 0, 2, 0, 2, 0, 1],
            [0, 3, 0, 1, 0, 2, 0, 3, 0],
            [0, 0, 3, 0, 1, 0, 1, 0, 0],
            [0, 0, 0, 3, 0, 3, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0, 0],
        ]
    
    initial_board = classic if config=='classic' else alien
    W = 1
    B = 2
    for i in range(dim[0]):
        for j in range(dim[1]):
            if initial_board[i][j] == W:
                env[(i, j)] = Piece(piece_type=player1.get_piece_type(), owner=player1)
            elif initial_board[i][j] == B:
                env[(i, j)] = Piece(piece_type=player2.get_piece_type(), owner=player2)

    init_rep = BoardAbalone(env=env, dim=dim)
    initial_game_state = GameStateAbalone(
        scores=init_scores, next_player=player1, players=list_players, rep=init_rep, step=0)
    try:
        master = MasterAbalone(
            name="Abalone", initial_game_state=initial_game_state, players_iterator=list_players, log_level=log_level, port=port,
            hostname=address
        )
    except PlayerDuplicateError:
        return

    listeners = [GUIClient(path=gui_path)]*gui
    if record :
        listeners.append(StateRecorder())
    master.record_game(listeners=listeners)
    return master

if __name__=="__main__":

    parser = argparse.ArgumentParser(
                        prog="main_abalone.py",
                        description="Description of the different execution modes:",
                        epilog='''
  ___           _                    
 / __| ___ __ _| |_  ___ _ _ ___ ___ 
 \__ \/ -_) _` | ' \/ _ \ '_(_-</ -_)
 |___/\___\__,_|_||_\___/_| /__/\___|
                                     ''',
                        formatter_class=RawTextHelpFormatter)
    parser.add_argument("-t","--type",
                        required=True,
                        type=str, 
                        choices=["local", "host_game", "connect", "human_vs_computer", "human_vs_human", "local_repeat"],
                        help="\nThe execution mode you want.\n" 
                             +" - local: Runs everything on you machine\n"
                             +" - host_game: Runs a single player on your machine and waits for an opponent to connect with the 'connect' node.\n\t      You must provide an external ip for the -a argument (use 'ipconfig').\n"
                             +" - connect: Runs a single player and connects to a distant game launched with the 'host' at the hostname specified with '-a'.\n"
                             +" - human_vs_computer: Launches a GUI locally for you to challenge your player.\n"
                             +" - human_vs_human: Launches a GUI locally for you to experiment the game's mechanics.\n"
                             +"\n"
                        )
    parser.add_argument("-c","--config",required=False,choices=["classic","alien"], default="classic",help="\nSets the starting board configuration.")
    parser.add_argument("-a","--address",required=False, default="localhost",help="\nThe external ip of the machine that hosts the GameMaster.\n\n")
    parser.add_argument("-p","--port",required=False,type=int, default=16001, help="The port of the machine that hosts the GameMaster.\n\n")
    parser.add_argument("-g","--no-gui",action='store_false',default=True, help="Headless mode\n\n")
    parser.add_argument("-r","--record",action="store_true",default=False, help="Stores the succesive game states in a json file.\n\n")
    parser.add_argument("-l","--log",required=False,choices=["DEBUG","INFO"], default="DEBUG",help="\nSets the logging level.")
    parser.add_argument("-n","--number",required=False,type=int, default=1, help="Number of loop for 'local_repeat'.\n\n")
    parser.add_argument("players_list",nargs="*", help='The players')
    args=parser.parse_args()

    type = vars(args).get("type")
    address = vars(args).get("address")
    port = vars(args).get("port")
    gui = vars(args).get("no_gui")
    record = vars(args).get("record")
    log_level = vars(args).get("log")
    list_players = vars(args).get("players_list")
    base_config = vars(args).get("config")
    n_loop = vars(args).get("number")
    time_limit = 15*60

    gui_path = os.path.join(dirname(os.path.abspath(__file__)),'GUI','index.html')

    if type == "local" :
        folder = dirname(list_players[0])
        sys.path.append(folder)
        player1_class = __import__(splitext(basename(list_players[0]))[0], fromlist=[None])
        folder = dirname(list_players[1])
        sys.path.append(folder)
        player2_class = __import__(splitext(basename(list_players[1]))[0], fromlist=[None])
        player1 = player1_class.MyPlayer("W", name=splitext(basename(list_players[0]))[0]+"_1", time_limit=time_limit)
        player2 = player2_class.MyPlayer("B", name=splitext(basename(list_players[1]))[0]+"_2", time_limit=time_limit)
        game = play(player1=player1, player2=player2, log_level=log_level, port=port, address=address, gui=gui, record=record, gui_path=gui_path, config=base_config)
        print("Scores are ", game.get_scores())
    elif type == "host_game" :
        folder = dirname(list_players[0])
        sys.path.append(folder)
        player1_class = __import__(splitext(basename(list_players[0]))[0], fromlist=[None])
        player1 = LocalPlayerProxy(player1_class.MyPlayer("W", name=splitext(basename(list_players[0]))[0]+"_local", time_limit=time_limit),gs=GameStateAbalone)
        player2 = RemotePlayerProxy(mimics=PlayerAbalone,piece_type="B",name="_remote", time_limit=time_limit)
        if address=='localhost':
            logger.warning('Using `localhost` with `host_game` mode, if both players are on different machines')
            logger.warning('use ipconfig/ifconfig to get your external ip and specity the ip with -a')
        play(player1=player1, player2=player2, log_level=log_level, port=port, address=address, gui=int(gui), record=record, gui_path=gui_path, config=base_config)
    elif type == "connect" :
        folder = dirname(list_players[0])
        sys.path.append(folder)
        player2_class = __import__(splitext(basename(list_players[0]))[0], fromlist=[None])
        player2 = LocalPlayerProxy(player2_class.MyPlayer("B", name="_remote", time_limit=time_limit),gs=GameStateAbalone)
        if address=='localhost':
            logger.warning('Using `localhost` with `connect` mode, if both players are on different machines')
            logger.warning('use ipconfig/ifconfig to get your external ip and specity the ip with -a')
        asyncio.new_event_loop().run_until_complete(player2.listen(keep_alive=True,master_address=f"http://{address}:{port}"))
    elif type == "human_vs_computer" :
        folder = dirname(list_players[0])
        sys.path.append(folder)
        player1_class = __import__(splitext(basename(list_players[0]))[0], fromlist=[None])
        player1 = InteractivePlayerProxy(PlayerAbalone("W", name="bob", time_limit=time_limit),gui_path=gui_path,gs=GameStateAbalone)
        player2 = LocalPlayerProxy(player1_class.MyPlayer("B", name=splitext(basename(list_players[0]))[0], time_limit=time_limit),gs=GameStateAbalone)
        play(player1=player1, player2=player2, log_level=log_level, port=port, address=address, gui=False, record=record, gui_path=gui_path, config=base_config)
    elif type == "human_vs_human" :
        player1 = InteractivePlayerProxy(PlayerAbalone("W", name="bob", time_limit=time_limit),gui_path=gui_path,gs=GameStateAbalone)
        player2 = InteractivePlayerProxy(PlayerAbalone("B", name="alice", time_limit=time_limit))
        player2.share_sid(player1)
        play(player1=player1, player2=player2, log_level=log_level, port=port, address=address, gui=False, record=record, gui_path=gui_path, config=base_config)
    elif type == "local_repeat" :
        folder = dirname(list_players[0])
        sys.path.append(folder)
        player1_class = __import__(splitext(basename(list_players[0]))[0], fromlist=[None])
        folder = dirname(list_players[1])
        sys.path.append(folder)
        player2_class = __import__(splitext(basename(list_players[1]))[0], fromlist=[None])
        classic_wb = [0,0]
        classic_bw = [0,0]
        alien_wb = [0,0]
        alien_bw = [0,0]

        classic_wb_scores = [0,0]
        classic_bw_scores = [0,0]
        alien_wb_scores = [0,0]
        alien_bw_scores = [0,0]

        for i in range(n_loop):
            player1 = player1_class.MyPlayer("W", name=splitext("r_"+basename(list_players[0]))[0]+"_1", time_limit=time_limit)
            player2 = player2_class.MyPlayer("B", name=splitext("r_"+basename(list_players[1]))[0]+"_2", time_limit=time_limit)
            current_round = play(player1=player1, player2=player2, log_level="CRITICAL", port=port, address=address, gui=False, record=record, gui_path=gui_path, config="classic")
            add_scores(classic_wb_scores, current_round.get_scores(), player1, player2)
            total_win = add_win(current_round.get_winner()[0], player1, player2, classic_wb)
        for i in range(n_loop):
            player1 = player1_class.MyPlayer("B", name=splitext("r_"+basename(list_players[0]))[0]+"_1", time_limit=time_limit)
            player2 = player2_class.MyPlayer("W", name=splitext("r_"+basename(list_players[1]))[0]+"_2", time_limit=time_limit)
            current_round = play(player1=player1, player2=player2, log_level="CRITICAL", port=port, address=address, gui=False, record=record, gui_path=gui_path, config="classic")
            add_scores(classic_bw_scores, current_round.get_scores(), player1, player2)
            total_win = add_win(current_round.get_winner()[0], player1, player2, classic_bw)
        for i in range(n_loop):
            player1 = player1_class.MyPlayer("W", name=splitext("r_"+basename(list_players[0]))[0]+"_1", time_limit=time_limit)
            player2 = player2_class.MyPlayer("B", name=splitext("r_"+basename(list_players[1]))[0]+"_2", time_limit=time_limit)
            current_round = play(player1=player1, player2=player2, log_level="CRITICAL", port=port, address=address, gui=False, record=record, gui_path=gui_path, config="alien")
            add_scores(alien_wb_scores, current_round.get_scores(), player1, player2)
            total_win = add_win(current_round.get_winner()[0], player1, player2, alien_bw)
        for i in range(n_loop):
            player1 = player1_class.MyPlayer("B", name=splitext("r_"+basename(list_players[0]))[0]+"_1", time_limit=time_limit)
            player2 = player2_class.MyPlayer("W", name=splitext("r_"+basename(list_players[1]))[0]+"_2", time_limit=time_limit)
            current_round = play(player1=player1, player2=player2, log_level="CRITICAL", port=port, address=address, gui=False, record=record, gui_path=gui_path, config="alien")
            add_scores(alien_bw_scores, current_round.get_scores(), player1, player2)
            total_win = add_win(current_round.get_winner()[0], player1, player2, alien_wb)


        total_classic = [classic_wb[0]+classic_bw[0], classic_wb[1]+classic_bw[1]]
        total_alien = [alien_wb[0]+alien_bw[0], alien_wb[1]+alien_bw[1]]
        total_win = [total_classic[0]+total_alien[0], total_classic[1]+total_alien[1]]
        print("Total wins: ", total_win)
        print(f"Classic wb  -  wins:{classic_wb}   scores:{classic_wb_scores}")
        print(f"Classic bw  -  wins:{classic_bw}   scores:{classic_bw_scores}")
        print(f"Alien wb    -  wins:{alien_wb}     scores:{alien_wb_scores}")
        print(f"Alien bw    -  wins:{alien_bw}     scores:{alien_bw_scores}")

        script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
        files=os.listdir(script_directory)
        for file in files:
            if file.startswith("r_"):
                os.remove(file)
