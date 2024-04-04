import itertools
from board_abalone import BoardAbalone
from player_abalone import PlayerAbalone
from game_state_abalone import GameStateAbalone
from seahorse.game.action import Action
from seahorse.game.game_state import GameState
from seahorse.game.action import Action
from seahorse.utils.custom_exceptions import MethodNotImplementedError
import scipy.stats
import math
import typing

import random
from seahorse.game.game_layout.board import Piece

from utils import DANGER, MAX_DANGER

class MyPlayer(PlayerAbalone):
    """
    Player class for Abalone game.

    Attributes:
        piece_type (str): piece type of the player
    """

    def __init__(self, piece_type: str, name: str = "alphabeta", time_limit: float=60*15, max_depth:int=2, *args) -> None:
        """
        Initialize the PlayerAbalone instance.

        Args:
            piece_type (str): Type of the player's game piece
            name (str, optional): Name of the player (default is "minimax")
            time_limit (float, optional): the time limit in (s)
        """
        super().__init__(piece_type,name,time_limit,*args)
        self.max_depth = max_depth
        self.ennemy_index = None
        self.index = None
    
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
        cluster_score = cluster_score/27 * scipy.stats.norm(20, 5).pdf(state.step)*10

        score = player_score + distance_score + threat_score + center_score + cluster_score*0.5 + nb_pieces_ally/14 - nb_pieces_ennemy/14
        return score

        return score - (nb_pieces_ennemy/14)*step_factor*2 + nb_pieces_ally/14 + threat_score/10 + edge_score/14 + center_score + cluster_score/(nb_pieces_ally*6)*0.5
    
    def max_value(self, state:GameStateAbalone, depth:int, alpha, beta) -> typing.Tuple[float, Action]:
        if state.is_done() or depth >= self.max_depth:
            # print("=========")
            # print("JOUEUR")
            return (self.heuristic(state), None)
        moves = state.get_possible_actions()
        
        _alpha = alpha
        value = -math.inf
        move = None
        for m in moves:
            new_state = m.get_next_game_state()
            (new_value, _) = self.min_value(new_state, depth+1, _alpha, beta)
            if new_value > value:
                value = new_value
                _alpha = value
                move = m
                if value > beta:
                    return (value, move)
        return (value, move)
    
    def min_value(self, state:GameStateAbalone, depth:int, alpha, beta) -> typing.Tuple[float, Action]:
        if state.is_done() or depth >= self.max_depth:
            print("=========")
            print("ADVERSAIRE")
            return (self.heuristic(state), None)
        moves = state.get_possible_actions()
        
        _beta = beta
        value = math.inf
        move = None
        for m in moves:
            new_state = m.get_next_game_state()
            (new_value, _) = self.max_value(new_state, depth+1, alpha, _beta)
            if new_value < value:
                value = new_value
                _beta = value
                move = m
                if value < alpha:
                    return (value, move)
        return (value, move)


    def compute_action(self, current_state: GameStateAbalone, **kwargs) -> Action:
        """
        Function to implement the logic of the player.

        Args:
            current_state (GameState): Current game state representation
            **kwargs: Additional keyword arguments

        Returns:
            Action: selected feasible action
        """

        players = current_state.get_players()
        if players[0].get_id() == self.id:
            self.ennemy_index = 1
            self.index = 0
        else:
            self.ennemy_index = 0
            self.index = 1

        (_, action) = self.max_value(current_state, 0, -math.inf, math.inf)
        return action
