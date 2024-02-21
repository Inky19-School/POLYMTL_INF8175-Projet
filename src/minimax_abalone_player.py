from player_abalone import PlayerAbalone
from game_state_abalone import GameStateAbalone
from seahorse.game.action import Action
from seahorse.game.game_state import GameState
from seahorse.game.action import Action
from seahorse.utils.custom_exceptions import MethodNotImplementedError
import math
import typing

import random

class MyPlayer(PlayerAbalone):
    """
    Player class for Abalone game.

    Attributes:
        piece_type (str): piece type of the player
    """

    def __init__(self, piece_type: str, name: str = "minimax", time_limit: float=60*15, max_depth:int=2, *args) -> None:
        """
        Initialize the PlayerAbalone instance.

        Args:
            piece_type (str): Type of the player's game piece
            name (str, optional): Name of the player (default is "minimax")
            time_limit (float, optional): the time limit in (s)
        """
        super().__init__(piece_type,name,time_limit,*args)
        self.max_depth = max_depth
    
    def heuristic(self, state: GameStateAbalone) -> float:
        """
        Function to implement the heuristic of the player.

        Args:
            current_state (GameState): Current game state representation

        Returns:
            float: heuristic value
        """
        return state.scores[self.id]
    
    def max_value(self, state:GameStateAbalone, depth:int) -> typing.Tuple[float, Action]:
        if state.is_done() or depth >= self.max_depth:
            return (self.heuristic(state), None)
        moves = state.get_possible_actions()
        
        value = -math.inf
        move = None
        for m in moves:
            new_value = value
            new_state = m.get_next_game_state()
            (new_value, _) = self.min_value(new_state, depth+1)
            if new_value > value:
                value = new_value
                move = m
        return (value, move)
    
    def min_value(self, state:GameStateAbalone, depth:int) -> typing.Tuple[float, Action]:
        if state.is_done() or depth >= self.max_depth:
            return (self.heuristic(state), None)
        moves = state.get_possible_actions()
        
        value = math.inf
        move = None
        for m in moves:
            new_value = value
            new_state = m.get_next_game_state()
            (new_value, _) = self.max_value(new_state, depth+1)
            if new_value < value:
                value = new_value
                move = m
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
        (_, action) = self.max_value(current_state, 0)
        return action
