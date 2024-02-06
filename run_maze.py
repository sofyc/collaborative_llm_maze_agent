import argparse
from maze import maze, agent, COLOR, id2name
from agents.LLM_agent import llm_agent
from agents.base_agent import base_agent
import random
import time


parser = argparse.ArgumentParser()
parser.add_argument("--rows", type=int, default=10)
parser.add_argument("--columns", type=int, default=10)
parser.add_argument("--load_maze", type=str, default=None)
parser.add_argument("--num_agents", type=int, default=4)
parser.add_argument("--num_items", type=int, default=4)
parser.add_argument("--agent_lm_id", type=str, default="gpt-35-turbo-1106")
parser.add_argument('--agent_type', default='dfs', choices=['dfs', 'llm'], help='which type pf agent to use')
parser.add_argument('--communication', default='no', choices=['no', 'direct', 'monitor'], help='the ways agent communicate')
parser.add_argument('--prompt_template_path', default='agents/prompt_com.csv', help='path to prompt template file')
parser.add_argument('--visual', action="store_true", help='visualize the maze')
parser.add_argument('--cot', action="store_true", help='use cot')

parser.add_argument("--t", default=0, type=float)
parser.add_argument("--top_p", default=1.0, type=float)
parser.add_argument("--max_tokens", default=96, type=int)
parser.add_argument("--n", default=1, type=int)

args = parser.parse_args()

random.seed(2)
initial_position = [(random.randint(1, args.rows), random.randint(1, args.columns)) for _ in range(args.num_agents)]

m = maze(args.rows, args.columns, visual=args.visual)
m.CreateMaze(loadMaze=args.load_maze)
m.SetItems(args.num_items, initial_position)

agents = []
colors = [COLOR.blue, COLOR.cyan, COLOR.green, COLOR.yellow]
if args.agent_type == "llm":
    maze_agent = llm_agent
elif args.agent_type == "dfs":
    maze_agent = base_agent

for i in range(args.num_agents):
    a = agent(m, x=initial_position[i][0], y=initial_position[i][1], shape="arrow", color=colors[i])
    agents.append(maze_agent(a, i, args))

task_description = ""
if args.visual:
    # agents[0]._mazeAgent.move(str(initial_position[0]))
    m._canvas.update()
    time.sleep(0.5)

finish = False
for r in range(2000):
    for it, agent in enumerate(agents):
        action, info = agent.run()
        agent.step(action)
        # if args.visual:
        #     m._canvas.update()

        if agent._mazeAgent._parentMaze.finish:
            total_cost = sum([a.total_cost for a in agents])
            total_steps = sum([a.steps for a in agents])
            print(f"Finished.\nTotal steps: {total_steps}\nTotal cost: {total_cost}")
            finish = True
            break

    if args.visual:
        m._canvas.update()

        if args.agent_type == "dfs":
            time.sleep(0.1)
    
    if finish:
        break