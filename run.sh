for num_agent in 4
do
    echo $num_agent
    for maze in {1..1}
    do
        python run_maze.py \
        --rows 10 \
        --columns 10 \
        --agent_type llm \
        --agent_lm_id gpt-35-turbo-1106 \
        --maze_seed $maze \
        --num_agents $num_agent \
        --communication optional \
        --random_initial_position \
        --num_items 4 \
        --item_type regular \
        --item_phase 1 \
        --total_steps 800 \
        --seed $maze \
        --remember_dead_end \
        --prompt_template_path agents/prompt_opt_regular.csv \
        --visual \
        --save_result
    done
    echo '--------'
done