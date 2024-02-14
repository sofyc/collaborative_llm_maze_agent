import time
from maze import id2name

class base_agent:
	"""
	LLM agent class
	"""
	def __init__(self, maze_agent, agent_id):
		self._mazeAgent = maze_agent
		self.agent_id = agent_id
		self.agent_name = id2name[agent_id]
		self.args = self._mazeAgent.args
		self.steps = 0
		self.total_cost = 0
		self.visited = {maze_agent.position}
		self.history_locations = [maze_agent.position]

	def run(self):
		# available_positions = set(self._mazeAgent._look()[0]) - self._mazeAgent.dead_end
		available_positions = self._mazeAgent._look()[0]

		others_dead_end = set()
		for agent in self._mazeAgent._parentMaze._agents:
			if agent != self._mazeAgent:
				others_dead_end = others_dead_end.union(agent.dead_end)

		if self.args.remember_dead_end:
			for position in available_positions:
				if position not in self.visited.union(others_dead_end).union(self._mazeAgent.dead_end):
					self.visited.add(position)
					self.history_locations.append(position)
					info = {"position": position}
					self.step(str(position))
					return str(position), info
				
				if len(set(available_positions) - self._mazeAgent.dead_end - others_dead_end) == 0:
					for position in available_positions:
						if position not in self.visited.union(self._mazeAgent.dead_end):
							self.visited.add(position)
							self.history_locations.append(position)
							info = {"position": position}
							self.step(str(position))
							return str(position), info
			
			last_position = self.history_locations.pop()
			position = self.history_locations[-1]
			info = {"position": position}
			self.step(str(position))
			return str(position), info

		else:
			for position in available_positions:
				if position not in self.visited:
					self.visited.add(position)
					self.history_locations.append(position)
					info = {"position": position}
					self.step(str(position))
					return str(position), info
			
			last_position = self.history_locations.pop()
			position = self.history_locations[-1]
			info = {"position": position}
			self.step(str(position))
			return str(position), info



	def step(self, position):
		
		self.steps += 1
		self._mazeAgent.move(position)