from maze import id2name

class base_agent:
	"""
	base agent class
	"""
	def __init__(self, maze_agent, agent_id):
		self._mazeAgent = maze_agent
		self.args = self._mazeAgent.args
		self.agent_id = agent_id
		self.agent_name = id2name[agent_id]
		self.other_agent_name = id2name[:agent_id] + id2name[agent_id+1:self.args.num_agents]
		self.steps = 0
		self.total_cost = 0
		self.visited = {maze_agent.position}
		self.history_locations = [maze_agent.position]
		self._mazeAgent.agent_name = self.agent_name
		self.action_history = ["[MOVE] " + str(self._mazeAgent.position)]

	def run(self):
		pass

	def step(self, action):
		pass
	
	def reset(self):
		pass