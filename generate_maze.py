import argparse
from maze import maze, agent, COLOR, id2name
from agents.LLM_agent import llm_agent
from agents.base_agent import base_agent
import random
import random


parser = argparse.ArgumentParser()
parser.add_argument("--rows", type=int, default=10)
parser.add_argument("--columns", type=int, default=10)
parser.add_argument('--visual', action="store_true", help='whether visualize the maze')
parser.add_argument("--save_maze", type=str, default=None)
parser.add_argument("--seed", type=int, default=42)

args = parser.parse_args()

random.seed(args.seed)
x = random.randint(1, args.rows)
y = random.randint(1, args.columns)

m = maze(args.rows, args.columns, visual=args.visual)
m.CreateMaze(x=x, y=y, saveMaze=True, seed=args.seed)
m.run()