from agents.LLM import *
from agents.Base_agent import base_agent
import pandas as pd

class llm_agent(base_agent):
	"""
	LLM agent class
	"""
	def __init__(self, maze_agent, agent_id):
		super().__init__(maze_agent, agent_id)
		self.lm_id = self.args.agent_lm_id
		self.communication = self.args.communication
		self.obs = self._mazeAgent.move(str(self._mazeAgent.position))
		self.last_action = None
		self.LLM = LLM(self.lm_id, self.communication, self.agent_id)
		self.prompt_template_path = self.args.prompt_template_path
		self.agent_info = {}
		
		df = pd.read_csv(self.prompt_template_path)
		self.goal = df['prompt'][1]
		self.action_prompt_template = df['prompt'][0].replace("$AGENT_NAME$", str(self.agent_name)).replace("$GOAL$", self.goal).replace("$ROW$", str(self.args.rows)).replace("$COL$", str(self.args.columns))
		if self.args.communication == "direct" or self.args.communication == "always":
			self.message_prompt_template = df['prompt'][2].replace("$AGENT_NAME$", str(self.agent_name)).replace("$GOAL$", self.goal).replace("$ROW$", str(self.args.rows)).replace("$COL$", str(self.args.columns))
			initial_dialogue = ""
			for i in range(self.args.num_agents):

				if i == 0:
					initial_dialogue += id2name[i] + ": Hello everyone, I'll tell you my position and dead end I found, please try to avoid dead end and explore new positions as much as possible.\n"
				else:
					initial_dialogue += id2name[i] + ": Thanks! I'll tell you my position and dead end I found, let's try to avoid dead end and explore new positions as much as possible.\n"

				# if i == 0:
				# 	initial_dialogue += id2name[i] + ": Hello everyone, I'll tell you my position and dead end I found.\n"
				# else:
				# 	initial_dialogue += id2name[i] + ": Thanks! I'll tell you my position and dead end I found.\n"

			self.action_prompt_template = self.action_prompt_template.replace("$INITIAL_DIALOGUE$", initial_dialogue[:-2]).replace("$OTHER_AGENT_NAME$", ", ".join(self.other_agent_name))
			self.message_prompt_template = self.message_prompt_template.replace("$INITIAL_DIALOGUE$", initial_dialogue[:-2]).replace("$OTHER_AGENT_NAME$", ", ".join(self.other_agent_name))

		self.sampling_params = {
			"max_tokens": self.args.max_tokens,
			"temperature": self.args.t,
			"top_p": self.args.top_p,
			"n": self.args.n,
		}

	def parse_answer(self, available_actions, text):
		for i in range(len(available_actions)):
			action = available_actions[i]
			if action in text:
				return action

		text = text.replace('\n', ' ')
		for i in range(len(available_actions)):
			action = available_actions[i]
			option = chr(ord('A') + i)
			# txt = text.lower()
			if f"option {option}" in text or f"{option}." in text.split(' ') or f"{option}," in text.split(' ') or f"Option {option}" in text or f"({option})" in text:
				return action
		if self.args.debug:
			print("WARNING! Fuzzy match!")
		for i in range(len(available_actions)):
			action = available_actions[i]
			if action.startswith("[SEND MESSAGE]"):
				return action
			pos = action.split(']')[1].strip()
			option = chr(ord('A') + i)
			if f"{option} " in text or pos in text:
				return action
		if self.args.debug:
			print("WARNING! No available action parsed!!! Random choose one")
		return random.choice(available_actions)

	def build_action_prompt(self, plans):

		prompt = self.action_prompt_template.replace("$OBSERVATION$", self.obs + str(self._mazeAgent.find_item()))
		prompt = prompt.replace("$MY_POSITION$", str(self._mazeAgent.position))
		
		your_dead_end = self._mazeAgent.dead_end
		others_dead_end = set()
		for agent in self._mazeAgent._parentMaze._agents:
			if agent != self._mazeAgent:
				others_dead_end = others_dead_end.union(agent.dead_end)

		if len(your_dead_end.intersection(set(self._mazeAgent._look()[0] + [self._mazeAgent.position]))) == 0:
			prompt = prompt.replace("$MY_DEAD_END$", "None")
		else:
			prompt = prompt.replace("$MY_DEAD_END$", ", ".join([str(i) for i in list(your_dead_end.intersection(set(self._mazeAgent._look()[0] + [self._mazeAgent.position])))]))
		
		# if len(others_dead_end.intersection(set(self._mazeAgent._look()[0] + [self._mazeAgent.position]))) == 0:
		# 	prompt = prompt.replace("$OTHER_DEAD_END$", "None")
		# else:
		# 	prompt = prompt.replace("$OTHER_DEAD_END$", ", ".join([str(i) for i in list(others_dead_end.intersection(set(self._mazeAgent._look()[0] + [self._mazeAgent.position])))]))
		
		prompt = prompt.replace("$PROGRESS$", f"{self._mazeAgent._parentMaze.score}/{self._mazeAgent._parentMaze.num_items} items found")
		prompt = prompt.replace("$ACTION_HISTORY$", ", ".join(self.action_history[-5:]))
		prompt = prompt.replace("$AVAILABLE_ACTIONS$", plans)

		if self.args.communication == "direct" or self.args.communication == "always":
			prompt = prompt.replace("$DIALOGUE_HISTORY$", "\n".join(self._mazeAgent._parentMaze.dialogue_history[-5:]))

		return prompt

	def build_message_prompt(self):
		
		prompt = self.message_prompt_template.replace("$OBSERVATION$", self.obs + str(self._mazeAgent.find_item()))
		prompt = prompt.replace("$MY_POSITION$", str(self._mazeAgent.position))
		your_dead_end = self._mazeAgent.dead_end

		if len(your_dead_end.intersection(set(self._mazeAgent._look()[0] + [self._mazeAgent.position]))) == 0:
			prompt = prompt.replace("$MY_DEAD_END$", "None")
		else:
			prompt = prompt.replace("$MY_DEAD_END$", ", ".join([str(i) for i in list(your_dead_end.intersection(set(self._mazeAgent._look()[0] + [self._mazeAgent.position])))]))
	

		prompt = prompt.replace("$PROGRESS$", f"{self._mazeAgent._parentMaze.score}/{self._mazeAgent._parentMaze.num_items} items found")
		prompt = prompt.replace("$DIALOGUE_HISTORY$", "\n".join(self._mazeAgent._parentMaze.dialogue_history[-5:]))
		prompt = prompt + f"\n{self.agent_name}:"

		return prompt

	def get_action(self, enable_message, enable_move):
		"""
		:param observation: {"edges":[{'from_id', 'to_id', 'relation_type'}],
		"nodes":[{'id', 'category', 'class_name', 'prefab_name', 'obj_transform':{'position', 'rotation', 'scale'}, 'bounding_box':{'center','size'}, 'properties', 'states'}],
		"messages": [None, None]
		}
		:param goal:{predicate:[count, True, 2]}
		:return:
		"""
		info = {}

		available_actions = []
		place_holder = 0
		if enable_message:
			message_prompt = self.build_message_prompt()
			chat_prompt = [{"role": "user", "content": message_prompt}]
			outputs, usage = self.LLM.generate(chat_prompt, self.sampling_params)
			self.total_cost += usage
			message = outputs[0]
			info['message_generator_prompt'] = message_prompt
			info['message_generator_outputs'] = outputs
			info['message_generator_usage'] = usage
			available_actions += ["[SEND MESSAGE] " + message]
			place_holder = 1

		if enable_move:
			available_actions += ["[MOVE] " + str(i) for i in self._mazeAgent._look()[0]]
		
		if len(available_actions) == 1:
			info.update({"action": available_actions[0], "total_cost": self.total_cost})
			if self.args.debug:
				for key, value in info.items():
					print(key)
					print(value)

			return available_actions[0], info

		others_dead_end = set()
		for agent in self._mazeAgent._parentMaze._agents:
			if agent != self._mazeAgent:
				others_dead_end = others_dead_end.union(agent.dead_end)

		plans = ""
		for i, plan in enumerate(available_actions):
			# plans += f"{chr(ord('A') + i)}. {plan}\n"

			plans += f"{chr(ord('A') + i)}. {plan}"
			if plan.startswith("[MOVE]"):
				if self._mazeAgent._look()[0][i-place_holder] in self._mazeAgent.dead_end:
					plans += f": This position leads to a dead end confirmed by myself."
				elif self._mazeAgent._look()[0][i-place_holder] in others_dead_end:
					plans += f": This position leads to a dead end confirmed by other agents."
				else:
					plans += f": This position does not lead to a dead end."
				
				if self._mazeAgent._look()[0][i-place_holder] not in self._mazeAgent.visited:
					plans += f" This position is unexplored.\n"
				else:
					plans += f" This position has been explored.\n"
			else:
				plans += f"\n"



		action_prompt = self.build_action_prompt(plans)

		if self.args.cot:
			cot_prompt = action_prompt + "\nLet's think step by step."
			chat_prompt = [{"role": "user", "content": cot_prompt}]
			outputs, usage = self.LLM.generate(chat_prompt, self.sampling_params)
			output = outputs[0]
			self.total_cost += usage
			info['cot_outputs'] = outputs
			info['cot_usage'] = usage

			chat_prompt = [{"role": "user", "content": cot_prompt},
						   {"role": "assistant", "content": output},
						   {"role": "user", "content": "Answer with only one best next action. So the answer is"}]

		else:
			chat_prompt = [{"role": "user", "content": action_prompt}]
		
		outputs, usage = self.LLM.generate(chat_prompt, self.sampling_params)
		self.total_cost += usage
		action = outputs[0]
		info['action_generator_prompt'] = action_prompt
		info['action_generator_outputs'] = outputs
		info['action_generator_usage'] = usage
		self.total_cost += usage

		action = self.parse_answer(available_actions, action)
		info.update({"action": action, "total_cost": self.total_cost})

		if self.args.debug:
			for key, value in info.items():
				print(key)
				print(value)
		
		return action, info

	def run(self):
		action = None
		info = {}
		if self.args.communication == "always":
			enable_message, enable_move = True, False
		elif self.args.communication == "no":
			enable_message, enable_move = False, True
		elif self.args.communication == "direct":
			enable_message, enable_move = True, True

		action, a_info = self.get_action(enable_message, enable_move)

		self.action = action
		# self.action_history.append('[SEND MESSAGE]' if action.startswith('[SEND MESSAGE]') else action)
		a_info.update({"steps": self.steps})

		self.step(action)
		if action.startswith('[SEND MESSAGE]'):
			info["message_action"] = a_info
			move_action, move_info = self.get_action(False, True)
			self.action_history.append(move_action)
			move_info.update({"steps": self.steps})
			info["move_action"] = move_info
			self.step(move_action)
		else:
			self.action_history.append(action)
			info["move_action"] = a_info

		return action, info

	# def reset(self, obs, containers_name, goal_objects_name, rooms_name, room_info, goal):
	# 	self.steps = 0

	# 	self.plan = None
	# 	self.action_history = [f"[goexplore] <{self.current_room['class_name']}> ({self.current_room['id']})"]
	# 	self.dialogue_history = []
	# 	self.LLM.reset(self.rooms_name, self.roomname2id, self.goal_location, self.unsatisfied)
	
	def step(self, action):

		if action.startswith("[SEND MESSAGE]"):
			message = action.split(']')[1].strip()
			self._mazeAgent._parentMaze.dialogue_history.append(f"{self.agent_name}: {message}")
		elif action.startswith("[MOVE]"):
			self.steps += 1
			location = action.split(']')[1].strip()
			self.obs = self._mazeAgent.move(location)
