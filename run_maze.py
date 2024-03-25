import argparse
from maze import maze, agent, COLOR, id2name
from agents.LLM_agent import llm_agent
from agents.DFS_agent import dfs_agent
import random
import time
import datetime
import json


parser = argparse.ArgumentParser()
parser.add_argument("--rows", type=int, default=10)
parser.add_argument("--columns", type=int, default=10)
parser.add_argument("--maze_seed", type=int, default=1)
parser.add_argument("--num_agents", type=int, default=4)
parser.add_argument("--num_items", type=int, default=4)
parser.add_argument("--total_steps", type=int, default=100)
parser.add_argument("--save_result", action="store_true", help='whether to save result')
parser.add_argument("--random_initial_position", action="store_true")
parser.add_argument("--agent_lm_id", type=str, default=None)
parser.add_argument('--agent_type', default='dfs', choices=['dfs', 'llm'], help='which type pf agent to use')
parser.add_argument('--item_type', default='regular', choices=['regular', 'special', 'heavy', 'valuable'], help='which type pf agent to use')
parser.add_argument("--item_phase", type=int, default=1)
parser.add_argument('--value_types', type=int, default=1)
parser.add_argument("--agents_per_item", type=int, default=1)
parser.add_argument('--communication', default='no', choices=['no', 'optional', 'audit', 'always'], help='the ways agent communicate')
parser.add_argument('--cot', action="store_true", help='use cot')
parser.add_argument('--remember_dead_end', action="store_true", help='remember and share dead end in a maze')
parser.add_argument('--prompt_template_path', default=None, help='path to prompt template file')
parser.add_argument('--visual', action="store_true", help='whether visualize the maze')
parser.add_argument('--debug', action="store_true", help='whether to print prompt and output')
parser.add_argument('--seed', type=int, default=1)


parser.add_argument("--t", default=0, type=float)
parser.add_argument("--top_p", default=1.0, type=float)
parser.add_argument("--max_tokens", default=180, type=int)
parser.add_argument("--n", default=1, type=int)

args = parser.parse_args()

m = maze(args.rows, args.columns, visual=args.visual)
m.CreateMaze(loadMaze=f"maze-{args.rows}-{args.columns}/{args.maze_seed}.csv")

item_positions = m.SetItems(args)
initial_position = []
if args.random_initial_position:
    random.seed(args.seed)
    while len(initial_position) < args.num_agents:
        new_position = (random.randint(1, args.rows), random.randint(1, args.columns))
        if new_position in item_positions or new_position in initial_position:
            continue
        initial_position.append(new_position)
    
else:
    initial_position = [(1, 1) for _ in range(args.num_agents)]

agents = []
colors = [color for color in COLOR][5:]
if args.agent_type == "llm":
    maze_agent = llm_agent
elif args.agent_type == "dfs":
    maze_agent = dfs_agent

for i in range(args.num_agents):
    a = agent(m, x=initial_position[i][0], y=initial_position[i][1], shape="arrow", color=colors[i], args=args)
    # m._agents.append(a)
    a.move(str(initial_position[i]))
    a.check_dead_end()
    agents.append(maze_agent(a, i))

m._agents = agents

task_description = ""
if args.visual:
    m._canvas.update()
    time.sleep(0.5)

finish = False
agent_info = {}
save_info = {}
for r in range(args.total_steps // args.num_agents):
    for it, agent in enumerate(agents):
        action, info = agent.run()
        agent_info[agent.agent_name] = info

        if args.visual:
            m._canvas.update()

            if args.agent_type == "dfs":
                time.sleep(0.05)

        if agent._mazeAgent._parentMaze.finish:
            finish = True
            break
    
    save_info[r] = agent_info
    agent_info = {}

    if finish:
        break

total_cost = sum([a.total_cost for a in agents])
total_steps = sum([a.steps for a in agents])
# print(f"Finished.\nTotal steps: {total_steps}\nTotal cost: {total_cost}\nScore: {m.score}/{m.total_scores}")
# print(m.score)
print(total_steps)

if args.save_result:
    save_info['cost'] = total_cost
    save_info['steps'] = total_steps
    save_info['scores'] = m.score
    save_info['args'] = vars(args)

    current_time = datetime.datetime.now()
    year = current_time.year
    month = current_time.month
    day = current_time.day
    hour = current_time.hour
    minute = current_time.minute
    second = current_time.second
    formatted_time = f"{year}-{month:02d}-{day:02d}-{hour:02d}:{minute:02d}:{second:02d}"

    if args.agent_type == "dfs":
        result_file = f"results_{args.agent_type}/{args.num_agents}_{args.num_items}_{args.item_type}_{args.maze_seed}_{formatted_time}.json"
    else:
        result_file = f"results_{args.agent_type}/{args.agent_lm_id}_{args.communication}_{args.num_agents}_{args.num_items}_{args.item_type}_{args.maze_seed}_{formatted_time}.json"

    with open(result_file, "w") as f:
        f.write(json.dumps(save_info, indent=4))