import time

class base_agent:
	"""
	LLM agent class
	"""
	def __init__(self, maze_agent, agent_id, args):
		self._mazeAgent = maze_agent
		self.agent_id = agent_id
		self.args = args
		self.steps = 0
		self.total_cost = 0
		self.visited = {maze_agent.position}
		self.history_locations = [maze_agent.position]

	def run(self):
		available_positions = self._mazeAgent._look()[0]

		for position in available_positions:
			if position not in self.visited and position not in self._mazeAgent._parentMaze.dead_end:
				self.visited.add(position)
				self.history_locations.append(position)
				info = {"position": position}

				return str(position), info
		
		self.history_locations.pop()
		position = self.history_locations[-1]
		info = {"position": position}

		return str(position), info

	def step(self, position):
		
		self.steps += 1
		self._mazeAgent.move(position)