for maze in {1..1}
do
    python run_maze.py \
    --rows 10 \
    --columns 10 \
    --agent_type llm \
    --agent_lm_id gpt-35-turbo-1106 \
    --load_maze maze-10-10-$maze.csv \
    --num_agents 4 \
    --num_items 4 \
    --visual \
    --communication direct \
    --prompt_template_path agents/prompt_com.csv \
    --debug \
    --remember_dead_end \
    --seed 1
done