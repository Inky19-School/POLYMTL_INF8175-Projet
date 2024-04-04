from player_abalone import PlayerAbalone
from game_state_abalone import GameStateAbalone
from seahorse.game.action import Action
from seahorse.game.game_state import GameState
from seahorse.utils.custom_exceptions import MethodNotImplementedError

import random
import time 
import math
from master_abalone import MasterAbalone

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
        print(len(list(possible_actions)))
        random.seed("seahorse")
        if kwargs:
            pass
        print("step : ",current_state.get_step())
        return self.MCTS(current_state=current_state,time_accorded=1.0)

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
        print("The current player is ", current_player)
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
            while not c_state.is_done():
                random_move = random.choice(list(c_state.get_possible_actions()))
                c_state = random_move.get_next_game_state()

            n_child.visits += 1
            if c_state.get_scores()[n_leaf.playerJustMoved] == max(c_state.get_scores().values()):
                n_child.wins += 1

            # Backpropagation
            while n_leaf.parentNode != None:
                n_leaf.visits += 1
                n_leaf.wins += n_child.wins
                n_leaf = n_leaf.parentNode
            n_leaf.visits += 1
            n_leaf.wins += n_child.wins
            
        print(n_leaf.wins)
        w = 0
        for child in n_leaf.childNodes:
            print(child.wins,child.visits)
            w += child.wins
        print(w)
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