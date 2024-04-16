#!/bin/bash
echo "Running AB-MCTS"

for i in {1..3}
do
    echo "Match $i"
    python main_abalone.py -t local_repeat alphabeta_abalone_player_atk.py monte_carlo_heuristic2_abalone_player.py
done

echo "Done"