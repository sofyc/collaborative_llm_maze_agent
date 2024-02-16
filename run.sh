for maze in {1..5}
do
    python run_maze.py \
    --rows 20 \
    --columns 20 \
    --agent_type llm \
    --agent_lm_id gpt-35-turbo-1106 \
    --load_maze maze-20-20-$maze.csv \
    --num_agents 4 \
    --num_items 20 \
    --visual \
    --communication direct \
    --prompt_template_path agents/prompt_com_score.csv \
    --debug \
    --remember_dead_end \
    --seed 1
done