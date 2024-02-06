from agents.LLM import *
from maze import id2name
import pandas as pd

class llm_agent:
	"""
	LLM agent class
	"""
	def __init__(self, maze_agent, agent_id, args):
		self._mazeAgent = maze_agent
		self.agent_id = agent_id
		self.agent_name = id2name[agent_id]
		self.other_agent_name = id2name[:agent_id] + id2name[agent_id+1:args.num_agents]
		self.lm_id = args.agent_lm_id
		self.communication = args.communication
		self.args = args
		self.total_cost = 0
		self.steps = 0
		self.obs = ""
		self.last_action = None
		self.LLM = LLM(self.lm_id, self.communication, self.agent_id)
		self.prompt_template_path = args.prompt_template_path
		self.action_history = ["[MOVE] " + str(self._mazeAgent.position)]
		
		df = pd.read_csv(self.prompt_template_path)
		self.goal = df['prompt'][1]
		self.action_prompt_template = df['prompt'][0].replace("$AGENT_NAME$", str(self.agent_name)).replace("$GOAL$", self.goal).replace("$ROW$", str(args.rows)).replace("$COL$", str(args.columns))
		if args.communication == "direct":
			self.message_prompt_template = df['prompt'][2].replace("$AGENT_NAME$", str(self.agent_name)).replace("$GOAL$", self.goal).replace("$ROW$", str(args.rows)).replace("$COL$", str(args.columns))
			initial_dialogue = ""
			for i in range(self.args.num_agents):

				if i == 0:
					initial_dialogue += id2name[i] + ": Hello everyone, I'll let you know if I find any goal objects and finish any subgoals, and ask for your help when necessary.\n"
				else:
					initial_dialogue += id2name[i] + ": Thanks! I'll let you know if I find any goal objects and finish any subgoals, and ask for your help when necessary.\n"

			self.action_prompt_template = self.action_prompt_template.replace("$INITIAL_DIALOGUE$", initial_dialogue[:-2]).replace("$OTHER_AGENT_NAME$", ", ".join(self.other_agent_name))
			self.message_prompt_template = self.message_prompt_template.replace("$INITIAL_DIALOGUE$", initial_dialogue[:-2]).replace("$OTHER_AGENT_NAME$", ", ".join(self.other_agent_name))

		self.sampling_params = {
			"max_tokens": args.max_tokens,
			"temperature": args.t,
			"top_p": args.top_p,
			"n": args.n,
		}

	def parse_answer(self, available_actions, text):
		for i in range(len(available_actions)):
			action = available_actions[i]
			if action in text:
				return action

		for i in range(len(available_actions)):
			action = available_actions[i]
			option = chr(ord('A') + i)
			# txt = text.lower()
			if f"option {option}" in text or f"{option}." in text.split(' ') or f"{option}," in text.split(' ') or f"Option {option}" in text or f"({option})" in text:
				return action
		print("WARNING! Fuzzy match!")
		for i in range(len(available_actions)):
			action = available_actions[i]
			if self.communication and i == 0:
				continue
			act, name, id = action.split(' ')
			option = chr(ord('A') + i)
			if f"{option} " in text or act in text or name in text or id in text:
				return action
		print("WARNING! No available action parsed!!! Random choose one")
		return random.choice(available_actions)

	def build_action_prompt(self, plans):

		prompt = self.action_prompt_template.replace("$CURRENT_POSITION$", str(self._mazeAgent.position))
		prompt = prompt.replace("$NEXT_POSSIBLE_POSITION$", str(self._mazeAgent._look()[0])[1:-1])
		prompt = prompt.replace("$PROGRESS$", f"{self._mazeAgent._parentMaze.score}/{self._mazeAgent._parentMaze.num_items} items found")
		prompt = prompt.replace("$AVAILABLE_ACTIONS$", plans)
		prompt = prompt.replace("$OBSERVATION$", self.obs + str(self._mazeAgent.find_item()))
		prompt = prompt.replace("$ACTION_HISTORY$", ", ".join(self.action_history[-10:]))

		if self.args.communication == "direct":
			prompt = prompt.replace("$DIALOGUE_HISTORY$", "\n".join(self._mazeAgent._parentMaze.dialogue_history))

		return prompt

	def build_message_prompt(self):

		prompt = self.message_prompt_template.replace("$CURRENT_POSITION$", str(self._mazeAgent.position))
		prompt = prompt.replace("$NEXT_POSSIBLE_POSITION$", str(self._mazeAgent._look()[0])[1:-1])
		prompt = prompt.replace("$PROGRESS$", f"{self._mazeAgent._parentMaze.score}/{self._mazeAgent._parentMaze.num_items} items found")
		prompt = prompt.replace("$OBSERVATION$", str(self._mazeAgent.find_item()))
		prompt = prompt.replace("$DIALOGUE_HISTORY$", ", ".join(self._mazeAgent._parentMaze.dialogue_history))
		prompt = prompt.replace("$ACTION_HISTORY$", "\n".join(self.action_history[-10:]))
		prompt = prompt + f"\n{self.agent_name}:"

		return prompt

	def get_action(self):
		"""
		:param observation: {"edges":[{'from_id', 'to_id', 'relation_type'}],
		"nodes":[{'id', 'category', 'class_name', 'prefab_name', 'obj_transform':{'position', 'rotation', 'scale'}, 'bounding_box':{'center','size'}, 'properties', 'states'}],
		"messages": [None, None]
		}
		:param goal:{predicate:[count, True, 2]}
		:return:
		"""
		# if self.communication:
		# 	for i in range(len(observation["messages"])):
		# 		if observation["messages"][i] is not None:
		# 			self.dialogue_history.append(f"{self.agent_names[i + 1]}: {observation['messages'][i]}")
		info = {}

		if self.args.communication == "direct":
			message_prompt = self.build_message_prompt()
			chat_prompt = [{"role": "user", "content": message_prompt}]
			outputs, usage = self.LLM.generate(chat_prompt, self.sampling_params)
			self.total_cost += usage
			message = outputs[0]
			info['message_generator_prompt'] = message_prompt
			info['message_generator_outputs'] = outputs
			info['message_generator_usage'] = usage

		if self.action_history[-1].startswith("[SEND MESSAGE]") or self.args.communication == "no":
			available_actions = ["[MOVE] " + str(i) for i in self._mazeAgent._look()[0]]
		else:
			available_actions = ["[SEND MESSAGE] " + message] + ["[MOVE] " + str(i) for i in self._mazeAgent._look()[0]]

		plans = ""
		for i, plan in enumerate(available_actions):
			plans += f"{chr(ord('A') + i)}. {plan}\n"

		action_prompt = self.build_action_prompt(plans)

		if self.args.cot:
			cot_prompt = action_prompt + " Let's think step by step."
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

		for key, value in info.items():
			print(key)
			print(value)
		
		return action, info

	def run(self):
		action = None
		LM_times = 0
		while action is None:
			if LM_times > 3:
				raise Exception(f"retrying LM_plan too many times")
			action, a_info = self.get_action()
			if action is None:
				print("No more things to do!")
				action = f"[wait]"

			self.action = action
			self.action_history.append('[SEND MESSAGE]' if action.startswith('[SEND MESSAGE]') else action)
			a_info.update({"steps": self.steps})
			LM_times += 1

		if action == self.last_action:
			self.stuck += 1
		else:
			self.stuck = 0
		self.last_action = action
	
		return action, a_info

	def reset(self, obs, containers_name, goal_objects_name, rooms_name, room_info, goal):
		self.steps = 0

		self.plan = None
		self.action_history = [f"[goexplore] <{self.current_room['class_name']}> ({self.current_room['id']})"]
		self.dialogue_history = []
		self.LLM.reset(self.rooms_name, self.roomname2id, self.goal_location, self.unsatisfied)
	
	def step(self, action):
		
		self.steps += 1

		if action.startswith("[SEND MESSAGE]"):
			message = action.split(']')[1].strip()
			self._mazeAgent._parentMaze.dialogue_history.append(f"{self.agent_name}: {message}")
		elif action.startswith("[MOVE]"):
			location = action.split(']')[1].strip()
			self.obs = self._mazeAgent.move(location)
