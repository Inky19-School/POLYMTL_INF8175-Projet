import itertools
from board_abalone import BoardAbalone
from player_abalone import PlayerAbalone
from game_state_abalone import GameStateAbalone
from seahorse.game.action import Action
from seahorse.game.action import Action
import math
import typing

from seahorse.game.game_layout.board import Piece

from utils.utils import CLUSTER_STEP_FACTOR, DANGER

class MyPlayer(PlayerAbalone):
    """
    Player class for Abalone game.

    Attributes:
        piece_type (str): piece type of the player
    """

    def __init__(self, piece_type: str, name: str = "alphabeta", time_limit: float=60*15, *args) -> None:
        """
        Initialize the PlayerAbalone instance.

        Args:
            piece_type (str): Type of the player's game piece
            name (str, optional): Name of the player (default is "minimax")
            time_limit (float, optional): the time limit in (s)
        """
        super().__init__(piece_type,name,time_limit,*args)
        self.max_depth = 3

        # Indexes of the players in GameState.get_players()
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
        board: BoardAbalone = state.get_rep()
        score = 0

        # Scores used to compute the global score
        distance_score_ally:int = 0 # Distance of the ally pieces to the center
        distance_score_ennemy:int = 0 # Distance of the ennemy pieces to the center
        threat_score:int = 0 # Represents the number of ally pieces in danger of being ejected
        cluster_score:int = 0 # Represents if the allied pieces are grouped or not

        # Normalized progress of the game
        step_factor:int = state.get_step() / state.max_step

        dim:list[int] = board.get_dimensions()

        # Number of pieces of each player
        nb_pieces_ally:int = 0
        nb_pieces_ennemy:int = 0
        
        # Analyze the board
        for i, j in itertools.product(range(dim[0]), range(dim[1])):
            in_danger:bool = False # True if an ennemy piece is in the neighborhood
            on_edge:bool = False
            _piece = board.get_env().get((i, j), -1)
            if _piece == -1:
                continue
            piece:Piece = _piece

            neighbours = board.get_neighbours(i, j)
            for _, (type, (nx, ny)) in neighbours.items():
                if type == "EMPTY":
                    continue
                elif type == "OUTSIDE":
                    on_edge = True
                elif piece.get_owner_id() == self.id:
                    if board.get_env().get((nx, ny), piece).get_owner_id() != self.id:
                        in_danger = True
                    else:
                        cluster_score += 0.5 # Another allied piece in the neighborhood, which indicates a possible cluster
            
            # Threat score: if an ally piece ce be ejected
            if (in_danger and on_edge):
                threat_score += 1

            if piece.get_owner_id() == self.id:
                distance_score_ally += DANGER.get((i,j))
                nb_pieces_ally += 1
            else:
                distance_score_ennemy += DANGER.get((i,j))
                nb_pieces_ennemy += 1
        
        # Center control
        center = board.get_env().get((8, 4), -1)
        center_score = 0
        if center != -1:
            center_score += 1 if center.get_owner_id() == self.id else -1

        # Base score
        player_score = state.get_player_score(state.get_players()[self.index])
        player_score = player_score/6 # [-1, 1]
        
        # Distance of the pieces to the center
        distance_score_ally_normalized = (distance_score_ally - 20) / 118
        distance_score_ennemy_normalized = (distance_score_ennemy - 20) / 118
        # [-1, 1]
        distance_score = distance_score_ennemy_normalized * (1-step_factor*0.25) - distance_score_ally_normalized * (1-step_factor)
        
        # Threat score [-1, 0]
        threat_score = -threat_score/14 * step_factor

        # Center score [-1, 1]
        center_score = center_score if state.step < 45 else 0

        # Cluster score [0, 1]
        cluster_score = cluster_score/27 * CLUSTER_STEP_FACTOR[state.step]

        # Pieces score [-1, 1]
        pieces_score = ((nb_pieces_ally - nb_pieces_ennemy)/14)*(1+step_factor)

        score = player_score + distance_score + threat_score*0.8 + center_score + cluster_score*0.4 + pieces_score
        return score

    # Alpha-Beta Pruning
    def max_value(self, state:GameStateAbalone, depth:int, alpha, beta) -> typing.Tuple[float, Action]:
        if state.is_done() or depth >= self.max_depth:
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
        # Save the indexes of the players
        players = current_state.get_players()
        if players[0].get_id() == self.id:
            self.ennemy_index = 1
            self.index = 0
        else:
            self.ennemy_index = 0
            self.index = 1

        # Set the max depth of the search.
        # The value is 3 for the first 20 steps as the agent is only focused on controlling the center.
        # After the 20th step, the depth is incremented to 4.
        # If the remaining time is less than 2min30, the depth falls to 3 to avoid timeout.
        self.max_depth = 2 if (current_state.step < 20 or current_state.get_players()[self.index].get_remaining_time() < 150) else 3
        if current_state.max_step - current_state.step < 4:
            self.max_depth = current_state.max_step - current_state.step

        (_, action) = self.max_value(current_state, 0, -math.inf, math.inf)
        return action
