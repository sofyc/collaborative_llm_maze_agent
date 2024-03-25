class base_agent:
	"""
	base agent class
	"""
	def __init__(self, maze_agent, agent_id):
		self._mazeAgent = maze_agent
		self.args = self._mazeAgent.args
		self.agent_id = agent_id
		self.steps = 0
		self.total_cost = 0
		self.visited = {maze_agent.position}
		self.history_locations = [maze_agent.position]
		self.action_history = ["[MOVE] " + str(self._mazeAgent.position)]

	def run(self):
		pass

	def step(self, action):
		pass
	
	def reset(self):
		pass