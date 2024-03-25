# LLM-based Maze Agent

## Quick start
Install dependencies:

```bash
pip install -r requirements.txt
```

Set up environment variables:

```bash
export AZURE_OPENAI_KEY="your key"
export AZURE_OPENAI_ENDPOINT="your endpoint"
```

Run a dfs based maze agent on a randomly generated maze:

```bash
python run_maze.py \
--rows 10 \
--columns 10 \
--agent_type dfs \
--num_agents 1 \
--num_items 4 \
--visual \
```

Run an llm based maze agent on a randomly generated maze:

```bash
python run_maze.py \
--rows 10 \
--columns 10 \
--agent_type llm \
--num_agents 1 \
--num_items 4 \
--visual \
--communication no \
--prompt_template_path agents/prompt_single.csv \
--agent_lm_id  gpt-35-turbo-1106
```

Run llm based maze agents with communication on a given maze:

```bash
python run_maze.py \
--rows 10 \
--columns 10 \
--agent_type llm \
--num_agents 4 \
--num_items 4 \
--visual \
--communication always \
--prompt_template_path agents/prompt_com_regular.csv \
--agent_lm_id  gpt-35-turbo-1106 \
--random_initial_position \
--maze_seed 1
```