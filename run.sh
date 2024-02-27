for num_agent in 1
do
    echo $num_agent
    for maze in {1..1}
    do
        python run_maze.py \
        --rows 10 \
        --columns 10 \
        --agent_type dfs \
        --maze_seed $maze \
        --num_agents $num_agent \
        --random_initial_position \
        --num_agents 4 \
        --remember_dead_end \
        --num_items 8 \
        --value_types 5 \
        --item_type valuable \
        --total_steps 80000 \
        --debug \
        --seed $maze \
        --visual

    done
    echo '--------'
done