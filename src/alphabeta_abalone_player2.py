import itertools
from board_abalone import BoardAbalone
from player_abalone import PlayerAbalone
from game_state_abalone import GameStateAbalone
from seahorse.game.action import Action
from seahorse.game.game_state import GameState
from seahorse.game.action import Action
from seahorse.utils.custom_exceptions import MethodNotImplementedError
import math
import typing

import random
from seahorse.game.game_layout.board import Piece

from utils.utils import DANGER, MAX_DANGER

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
        edge_score:int = 0
        threat_score:int = 0

        step_factor:int = state.get_step() / state.max_step

        dim:list[int] = board.get_dimensions()
        nb_pieces_ally:int = 0
        nb_pieces_ennemy:int = 0
        
        for i, j in itertools.product(range(dim[0]), range(dim[1])):
            in_danger:bool = False
            _piece = board.get_env().get((i, j), -1)
            if _piece == -1:
                continue
            piece:Piece = _piece
            is_ally = piece.get_owner_id() == next_player

            neighbours = board.get_neighbours(i, j)
            for _, (type, (nx, ny)) in neighbours.items():
                if type == "EMPTY":
                    continue
                elif type == "OUTSIDE":
                    edge_score += -1 if is_ally else 1
                    in_danger = True
                elif board.get_env().get((nx, ny), piece).get_owner_id() != self.id:
                    threat_score += 1
            if (in_danger):
                threat_score += 2

            if piece.get_owner_id() == next_player:
                distance_score_ally += (MAX_DANGER-DANGER.get((i,j)))
                nb_pieces_ally += 1
            else:
                distance_score_ennemy += DANGER.get((i,j))
                nb_pieces_ennemy += 1

        # todo: REFACTOR NORMALISATION
        nb_pieces:int = nb_pieces_ally + nb_pieces_ennemy
        player_score = state.get_player_score(state.get_players()[self.index])
        score = (distance_score_ally/(nb_pieces_ally*MAX_DANGER)) * (1-step_factor)
        score += (distance_score_ennemy/(nb_pieces_ally*MAX_DANGER))*0.5 * (1-step_factor)
        return score - (nb_pieces_ennemy/14)*step_factor + nb_pieces_ally/14 #+ edge_score + threat_score
    
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
