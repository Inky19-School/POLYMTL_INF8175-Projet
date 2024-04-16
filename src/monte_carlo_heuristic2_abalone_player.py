from player_abalone import PlayerAbalone
from game_state_abalone import GameStateAbalone
from seahorse.game.action import Action
from seahorse.game.game_state import GameState
from seahorse.utils.custom_exceptions import MethodNotImplementedError

import random
import time 
import math
from board_abalone import BoardAbalone
from utils.utils import DANGER, CLUSTER_STEP_FACTOR
from seahorse.game.game_layout.board import Piece
import itertools


class MyPlayer(PlayerAbalone):
    """
    Player class for Abalone game.

    Attributes:
        piece_type (str): piece type of the player
    """

    def __init__(self, piece_type: str, name: str = "bob", time_limit: float=60*15,*args) -> None:
        """
        Initialize the PlayerAbalone instance.

        Args:
            piece_type (str): Type of the player's game piece
            name (str, optional): Name of the player (default is "bob")
            time_limit (float, optional): the time limit in (s)
        """
        super().__init__(piece_type,name,time_limit,*args)

    def compute_action(self, current_state: GameStateAbalone, **kwargs) -> Action:
        """
        Function to implement the logic of the player.

        Args:
            current_state (GameState): Current game state representation
            **kwargs: Additional keyword arguments

        Returns:
            Action: selected feasible action
        """
        #Je teste git
        possible_actions = current_state.get_possible_actions()
        random.seed("seahorse")
        players = current_state.get_players()
        if players[0].get_id() == self.id:
            self.ennemy_index = 1
            self.index = 0
        else:
            self.ennemy_index = 0
            self.index = 1
        if kwargs:
            pass

        T = 12 * 60
        time_accorded = (1.5/65 if current_state.get_step() <= 30 else 1/65) * T * 2
        #print("Time accorded : ",time_accorded)

        return self.MCTS(current_state=current_state,time_accorded=time_accorded)


    def heuristic(self, state: GameStateAbalone) -> float:
        """
        Function to implement the heuristic of the player.

        Args:
            current_state (GameState): Current game state representation

        Returns:
            float: heuristic value
        """
        # idées: 
        # - distance de chaque bille au centre
        # - billes en danger
        # - bille adversaire en danger
        # notes: pour être admissible, entre -6 et 6. Préférable -2 et 2 (l'adversaire va forcèment marquer des points)
        board: BoardAbalone = state.get_rep()
        score = 0
        # current_player_pieces = board.get_pieces_player(state.get_next_player())
        next_player = self.id
        grid = board.get_grid()

        distance_score_ally:int = 0
        distance_score_ennemy:int = 0
        threat_score:int = 0
        cluster_score:int = 0

        step_factor:int = state.get_step() / state.max_step

        dim:list[int] = board.get_dimensions()
        nb_pieces_ally:int = 0
        nb_pieces_ennemy:int = 0
        
        for i, j in itertools.product(range(dim[0]), range(dim[1])):
            in_danger:bool = False
            on_edge:bool = False
            _piece = board.get_env().get((i, j), -1)
            if _piece == -1:
                continue
            piece:Piece = _piece
            is_ally = piece.get_owner_id() == self.id

            neighbours = board.get_neighbours(i, j)
            for _, (type, (nx, ny)) in neighbours.items():
                if type == "EMPTY":
                    continue
                elif type == "OUTSIDE":
                    on_edge = True
                elif board.get_env().get((nx, ny), piece).get_owner_id() != self.id:
                    in_danger = True
                else:
                    cluster_score += 0.5

            if (in_danger and on_edge):
                threat_score += 1

            if piece.get_owner_id() == next_player:
                distance_score_ally += DANGER.get((i,j))
                nb_pieces_ally += 1
            else:
                distance_score_ennemy += DANGER.get((i,j))
                nb_pieces_ennemy += 1
        
        center = board.get_env().get((8, 4), -1)
        center_score = 0
        if center != -1:
            center_score += 1 if center.get_owner_id() == self.id else -1
        # todo: REFACTOR NORMALISATION
        nb_pieces:int = nb_pieces_ally + nb_pieces_ennemy

        # Base score [-6, 6]
        player_score = state.get_player_score(state.get_players()[self.index])
        player_score = player_score/6 # [-1, 1]
        
        # Distance of the pieces to the center
        distance_score_ally_normalized = (distance_score_ally - 20) / 104
        distance_score_ennemy_normalized = (distance_score_ennemy - 20) / 104
        # [-1, 1]
        distance_score = (distance_score_ennemy_normalized - distance_score_ally_normalized) * (1-step_factor)
        
        # Threat score [-1, 0]
        threat_score = -threat_score/14 * step_factor

        # Center score [-1, 1]
        center_score = center_score if state.step < 45 else 0

        # Cluster score [0, 1]
        cluster_score = cluster_score/27 * CLUSTER_STEP_FACTOR[state.step]

        score = player_score + distance_score + threat_score + center_score + cluster_score*0.5 + nb_pieces_ally/14 - nb_pieces_ennemy/14
        return score

    def MCTS(self,current_state: GameStateAbalone, time_accorded : float) -> Action:
        """
        Cette méthode renvoie le meilleur coup en utilisant la méthode de monte Carlo avec une simulation aléatoire

        Args:
            current_state (GameStateAbalone): _description_
            time_accorded (float): _description_

        Returns:
            Action: _description_
        """
        n_leaf = Node(state = current_state, player = current_state.get_next_player().get_id())
        current_player = current_state.get_next_player().get_id()
        time_at_beginning = time.time()
        #print("The current player is ", current_player)
        iteration = 0
        while time.time() <= time_at_beginning + time_accorded:
            
            iteration += 1

            # Selection 
            while n_leaf.untriedMoves == [] and  n_leaf.childNodes != []:

                n_leaf = sorted(n_leaf.childNodes, key = lambda c: c.wins/c.visits + math.sqrt(2*math.log(n_leaf.visits)/c.visits))[-1]

            # Expansion
            if n_leaf.untriedMoves != []:
                move = random.choice(n_leaf.untriedMoves)
                n_child = n_leaf.addChild(move=move,state=move.get_next_game_state())

            # Simulation 
            c_state : GameStateAbalone = n_child.state
            depth = 10
            while not c_state.is_done() and depth >= 0:
                random_move = random.choice(list(c_state.get_possible_actions()))
                c_state = random_move.get_next_game_state()
                depth -= 1

            n_child.visits += 1
            if c_state.is_done():
                if c_state.get_scores()[n_leaf.playerJustMoved] == max(c_state.get_scores().values()):
                    n_child.wins += 1 
            else : 
                heur = self.heuristic(c_state)
                if heur >= 0.3:
                    n_child.wins += 1

            # Backpropagation
            while n_leaf.parentNode != None:
                n_leaf.visits += 1
                n_leaf.wins += n_child.wins
                n_leaf = n_leaf.parentNode
            n_leaf.visits += 1
            n_leaf.wins += n_child.wins
            
        #print(n_leaf.wins)
        w = 0
        for child in n_leaf.childNodes:
            #print(child.wins,child.visits)
            w += child.wins
        #print(w)
        return sorted(n_leaf.childNodes,key = lambda c : c.visits)[-1].move
            
            
class Node:
    """
    A node in the game tree.
    """

    def __init__(self, move : Action = None, parent = None, state : GameStateAbalone = None, player : PlayerAbalone = None):
        self.move = move # the move that got us to this node - "None" for the root node
        self.parentNode = parent # "None" for the root node
        self.childNodes = [] 
        self.wins = 0
        self.visits = 0
        self.playerJustMoved = player
        self.state = state
        self.untriedMoves : list[Action] = list(state.get_possible_actions())

    def addChild(self, move : Action, state : GameStateAbalone):
        n = Node(move = move, parent = self, state = state, player = self.playerJustMoved)
        self.untriedMoves.remove(move)
        self.childNodes.append(n)
        return n 