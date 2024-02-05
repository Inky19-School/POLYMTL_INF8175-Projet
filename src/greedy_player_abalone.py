from player_abalone import PlayerAbalone
from seahorse.game.action import Action
from game_state_abalone import GameStateAbalone
from seahorse.utils.custom_exceptions import MethodNotImplementedError


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
        Return the action with the best score for the player.

        Args:
            current_state (GameState): Current game state representation
            **kwargs: Additional keyword arguments

        Returns:
            Action: selected feasible action
        """
        possible_actions = list(current_state.get_possible_actions())
        other_id = possible_actions[0].get_next_game_state().next_player.get_id()
        best_action = None
        best_score = -7
        for a in possible_actions:
            score = a.get_next_game_state().scores[self.id] - a.get_next_game_state().scores[other_id]
            if score > best_score:
                best_action = a
                best_score = score

        return best_action
