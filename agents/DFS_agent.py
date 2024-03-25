import random
from agents.Base_agent import base_agent
import collections
from maze import id2name

class dfs_agent(base_agent):
	"""
	DFS agent class
	"""
	def __init__(self, maze_agent, agent_id):
		super().__init__(maze_agent, agent_id)
		self.id2name = id2name
		self.agent_name = self.id2name[agent_id]
		self.history_locations = [maze_agent.position]

	def run(self):
		if self._mazeAgent.position in self._mazeAgent._parentMaze.item_positions:
			item = self._mazeAgent._parentMaze.item_positions[self._mazeAgent.position]
			
			if item.item_type == 'regular':
				action = f"[PICK UP] item"
				info = {"action": action}
				self.step(action)
				return action, info

			elif item.item_type == 'special':
				if not self.action_history[-1].startswith("[PICK UP]") or (self.action_history[-1].startswith("[PICK UP]") and "success" in self.obs):
				# if self._mazeAgent.agent_name == item.agent_list[0]:
					action = f"[PICK UP] {str({self._mazeAgent.position})}"
					info = {"action": action}
					self.step(action)
					return action, info
			
			elif item.item_type == 'heavy':
				action = f"[PICK UP] {str({self._mazeAgent.position})}"
				info = {"action": action}
				self.step(action)
				return action, info
			
			elif item.item_type == 'valuable':
				action = f"[PICK UP] {str({self._mazeAgent.position})}"
				info = {"action": action}
				self.step(action)
				return action, info

		if self.args.remember_dead_end:
			available_positions = list(set(self._mazeAgent._look()[0]) - set(self._mazeAgent.dead_end))
			random.shuffle(available_positions)

			for position in available_positions:
				if position not in self.visited.union(set(self._mazeAgent.dead_end)):
					self.visited.add(position)
					self.history_locations.append(position)
					action = f"[MOVE] {str(position)}"
					info = {"action": action}
					self.step(action)
					return action, info

			
			if len(self.history_locations) == 1:

				self.visited = {self._mazeAgent.position}
				self.history_locations = [self._mazeAgent.position]
				for a in self._mazeAgent.dead_end_agent.values():
					a.kill()
				
				self._mazeAgent.dead_end = {}
				self._mazeAgent.dead_end_agent = {}
				self._mazeAgent.add_dead_end(self._mazeAgent.position)

				return self.run()

			last_position = self.history_locations.pop()
			position = self.history_locations[-1]

			# if position in self._mazeAgent.dead_end:
			# 	print(2)
			# 	self.visited = {self._mazeAgent.position}
			# 	self.history_locations = [self._mazeAgent.position]

			# 	return self.run()

			action = f"[MOVE] {str(position)}"
			info = {"action": action}
			self.step(action)
			return action, info

		else:
			available_positions = self._mazeAgent._look()[0]
			random.shuffle(available_positions)
			for position in available_positions:
				if position not in self.visited:
					self.visited.add(position)
					self.history_locations.append(position)
					action = f"[MOVE] {str(position)}"
					info = {"action": action}
					self.step(action)
					return action, info
			
			if len(self.history_locations) == 1:
				self.visited = {self._mazeAgent.position}
				self.history_locations = [self._mazeAgent.position]
				return self.run()

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
			self.obs = self._mazeAgent.pick()

		elif action.startswith("[MOVE]"):
			self.steps += 1
			self._mazeAgent._parentMaze.total_step += 1
			position = action.split(']')[1].strip()
			self.obs = self._mazeAgent.move(position)

		
		self._mazeAgent.check_dead_end()
		# print(self.obs)

	def reset(self):
		pass
