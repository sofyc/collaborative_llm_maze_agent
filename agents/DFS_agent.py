import random
from agents.Base_agent import base_agent
import collections

class dfs_agent(base_agent):
	"""
	DFS agent class
	"""
	def __init__(self, maze_agent, agent_id):
		super().__init__(maze_agent, agent_id)
		self.history_locations = [maze_agent.position]

	def run(self):
		if not self.action_history[-1].startswith("[PICK UP]"):
			if self._mazeAgent.position in self._mazeAgent._parentMaze.item_positions:
				action = f"[PICK UP] {str({self._mazeAgent.position})}"
				info = {"action": action}
				self.step(action)
				return action, info

		available_positions = list(set(self._mazeAgent._look()[0]) - set(self._mazeAgent.dead_end))
		# available_positions = self._mazeAgent._look()[0]
		# print(self.agent_name)
		# print(self.history_locations)
		# print(self._mazeAgent.position)
		# print(available_positions)
		# print(self._mazeAgent._parentMaze.item_positions)
		# print('--------')
		random.shuffle(available_positions)

		others_dead_end = {}
		for agent in self._mazeAgent._parentMaze._agents:
			if agent != self._mazeAgent:
				# others_dead_end = others_dead_end.union(set(agent.dead_end))
				others_dead_end.update(agent.dead_end)

		if self.args.remember_dead_end:
			for position in available_positions:
				if position not in self.visited.union(set(others_dead_end)).union(set(self._mazeAgent.dead_end)):
					self.visited.add(position)
					self.history_locations.append(position)
					action = f"[MOVE] {str(position)}"
					info = {"action": action}
					self.step(action)
					return action, info
				
				if len(set(available_positions) - set(self._mazeAgent.dead_end) - set(others_dead_end)) == 0:
					for position in available_positions:
						if position not in self.visited.union(set(self._mazeAgent.dead_end)):
							self.visited.add(position)
							self.history_locations.append(position)
							action = f"[MOVE] {str(position)}"
							info = {"action": action}
							self.step(action)
							return action, info
			
			if len(self.history_locations) == 1:

				q = collections.deque()
				q.append(self._mazeAgent.position)

				while q:
					pos = q.popleft()
					for neighbor in self._mazeAgent._parentMaze.find_neighbors(pos)[0]:
						if neighbor in self._mazeAgent.dead_end:
							q.append(neighbor)
							self._mazeAgent.dead_end_agent[neighbor].kill()
							del self._mazeAgent.dead_end_agent[neighbor]
							del self._mazeAgent.dead_end[neighbor]

				self.visited = {self._mazeAgent.position}
				self.history_locations = [self._mazeAgent.position]

				return self.run()

			last_position = self.history_locations.pop()
			position = self.history_locations[-1]

			if position in self._mazeAgent.dead_end:
				q = collections.deque()
				q.append(self._mazeAgent.position)

				while q:
					pos = q.popleft()
					for neighbor in self._mazeAgent._parentMaze.find_neighbors(pos)[0]:
						if neighbor in self._mazeAgent.dead_end:
							q.append(neighbor)
							self._mazeAgent.dead_end_agent[neighbor].kill()
							del self._mazeAgent.dead_end_agent[neighbor]
							del self._mazeAgent.dead_end[neighbor]

				self.visited = {self._mazeAgent.position}
				self.history_locations = [self._mazeAgent.position]

				return self.run()

				return self.run()

			action = f"[MOVE] {str(position)}"
			info = {"action": action}
			self.step(action)
			return action, info

		else:
			for position in available_positions:
				if position not in self.visited:
					self.visited.add(position)
					self.history_locations.append(position)
					action = f"[MOVE] {str(position)}"
					info = {"action": action}
					self.step(action)
					return action, info
			
			last_position = self.history_locations.pop()
			position = self.history_locations[-1]
			info = {"position": position}
			action = f"[MOVE] {str(position)}"
			info = {"action": action}
			self.step(action)
			return action, info


	def step(self, action):
		
		self.action_history.append(action)
		if action.startswith("[PICK UP]"):
			self.steps += 1
			self._mazeAgent._parentMaze.total_step += 1
			position = action.split(']')[1].strip()
			self.obs = self._mazeAgent.pick()

		elif action.startswith("[MOVE]"):
			self.steps += 1
			self._mazeAgent._parentMaze.total_step += 1
			position = action.split(']')[1].strip()
			self.obs = self._mazeAgent.move(position)

		
		self._mazeAgent.check_dead_end()

	def reset(self):
		pass
