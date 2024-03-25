from agents.LLM import *
from agents.Base_agent import base_agent
import pandas as pd
from maze import id2name


class llm_agent(base_agent):
	"""
	LLM agent class
	"""
	def __init__(self, maze_agent, agent_id):
		super().__init__(maze_agent, agent_id)
		self.id2name = id2name
		self.agent_name = self.id2name[agent_id]
		self.other_agent_name = self.id2name[:agent_id] + self.id2name[agent_id+1:self.args.num_agents]
		self.all_agent_name = self.id2name[:self.args.num_agents]
		self._mazeAgent.agent_name = self.agent_name
		self.lm_id = self.args.agent_lm_id
		self.communication = self.args.communication
		self.obs = [self._mazeAgent.move(str(self._mazeAgent.position))]
		self.last_action = None
		self.LLM = LLM(self.lm_id, self.communication, self.agent_id)
		self.prompt_template_path = self.args.prompt_template_path
		self.agent_info = {}
		self.instruction_history[self.agent_name] = ["No instruction given."]

		df = pd.read_csv(self.prompt_template_path)
		# self.goal = df['prompt'][1]
		if self.args.item_type == "regular":
			self.goal = "Discover and pick up randomly generated items scattered throughout the maze to accumulate scores."
		elif self.args.item_type == "special":
			self.goal = "Discover and pick up randomly generated items scattered throughout the maze to accumulate scores. These items require a specific sequence of agents to pick them up successfully."
		
		self.action_prompt_template = df['prompt'][0].replace("$AGENT_NAME$", self.agent_name).replace("$GOAL$", self.goal).replace("$ROW$", str(self.args.rows)).replace("$COL$", str(self.args.columns))
		if self.args.communication == "optional" or self.args.communication == "always":
			self.message_prompt_template = df['prompt'][1].replace("$AGENT_NAME$", self.agent_name).replace("$GOAL$", self.goal).replace("$ROW$", str(self.args.rows)).replace("$COL$", str(self.args.columns))
			initial_dialogue = ""
			for i in range(self.args.num_agents):

				if i == 0:
					initial_dialogue += self.id2name[i] + ": Hello everyone, I'll tell you my position, dead end information, and item information.\n"
					
				else:
					initial_dialogue += self.id2name[i] + ": Thanks! I'll tell you my position, dead end information, and item information.\n"

			self.action_prompt_template = self.action_prompt_template.replace("$INITIAL_DIALOGUE$", initial_dialogue).replace("$OTHER_AGENT_NAME$", ", ".join(self.other_agent_name))
			self.message_prompt_template = self.message_prompt_template.replace("$INITIAL_DIALOGUE$", initial_dialogue).replace("$OTHER_AGENT_NAME$", ", ".join(self.other_agent_name))

		if self.args.communication == "optional":
			self.whether_message_prompt_template = df['prompt'][2].replace("$AGENT_NAME$", self.agent_name).replace("$GOAL$", self.goal).replace("$ROW$", str(self.args.rows)).replace("$COL$", str(self.args.columns))
			initial_dialogue = ""
			for i in range(self.args.num_agents):

				if i == 0:
					initial_dialogue += self.id2name[i] + ": Hello everyone, I'll tell you my position, dead end information, and item information.\n"
					
				else:
					initial_dialogue += self.id2name[i] + ": Thanks! I'll tell you my position, dead end information, and item information.\n"

			self.whether_message_prompt_template = self.whether_message_prompt_template.replace("$INITIAL_DIALOGUE$", initial_dialogue).replace("$OTHER_AGENT_NAME$", ", ".join(self.other_agent_name))

		if self.args.communication == "audit":
			self.audit_prompt_template = df['prompt'][1].replace("$GOAL$", self.goal).replace("$ROW$", str(self.args.rows)).replace("$COL$", str(self.args.columns))
			self.audit_prompt_template = self.audit_prompt_template.replace("$ALL_AGENT_NAME$", ", ".join(self.all_agent_name))
		
		self.sampling_params = {
			"max_tokens": self.args.max_tokens,
			"temperature": self.args.t,
			"top_p": self.args.top_p,
			"n": self.args.n,
		}

	@property
	def instruction_history(self):
		return self._mazeAgent._parentMaze.instruction_history

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

		prompt = self.action_prompt_template.replace("$OBSERVATION$", self.obs[-1])
		prompt = prompt.replace("$MY_POSITION$", str(self._mazeAgent.position))
		

		prompt = prompt.replace("$MY_DEAD_END$", self._mazeAgent.dead_end_in_vision())
		
		prompt = prompt.replace("$PROGRESS$", f"{self._mazeAgent._parentMaze.score}/{self._mazeAgent._parentMaze.num_items} items found")
		starting = max(1, len(self.action_history)+1-8)
		history = "; ".join([f"Step {starting+i}: {self.action_history[-8:][i]}" for i in range(len(self.action_history[-8:]))])

		prompt = prompt.replace("$ACTION_HISTORY$", history)
		prompt = prompt.replace("$AVAILABLE_ACTIONS$", f"Step {len(self.action_history)+1}:\n" + plans)

		if self.args.communication == "optional" or self.args.communication == "always":
			prompt = prompt.replace("$DIALOGUE_HISTORY$", "\n".join(self._mazeAgent._parentMaze.dialogue_history[-5:]))
		elif self.args.communication == "audit":
			prompt = prompt.replace("$INSTRUCTION$", self.instruction_history[self.agent_name][-1])

		return prompt

	def build_message_prompt(self):
		
		prompt = self.message_prompt_template.replace("$OBSERVATION$", self.obs[-1])
		prompt = prompt.replace("$MY_POSITION$", str(self._mazeAgent.position))
		prompt = prompt.replace("$MY_DEAD_END$", self._mazeAgent.dead_end_in_vision())
		prompt = prompt.replace("$PROGRESS$", f"{self._mazeAgent._parentMaze.score}/{self._mazeAgent._parentMaze.num_items} items found")
		prompt = prompt.replace("$DIALOGUE_HISTORY$", "\n".join(self._mazeAgent._parentMaze.dialogue_history[-5:]))
		prompt = prompt + f"\n{self.agent_name}:"

		return prompt
	
	def build_whether_message_prompt(self):
		
		prompt = self.whether_message_prompt_template.replace("$CURRENT_OBSERVATION$", self.obs[-1])
		prompt = self.whether_message_prompt_template.replace("$PREVIOUS_OBSERVATION$", self.obs[-2] if len(self.obs) > 1 else "None")
		prompt = prompt.replace("$MY_POSITION$", str(self._mazeAgent.position))
		prompt = prompt.replace("$MY_DEAD_END$", self._mazeAgent.dead_end_in_vision())
		prompt = prompt.replace("$PROGRESS$", f"{self._mazeAgent._parentMaze.score}/{self._mazeAgent._parentMaze.num_items} items found")
		prompt = prompt.replace("$DIALOGUE_HISTORY$", "\n".join(self._mazeAgent._parentMaze.dialogue_history[-5:]))

		return prompt
	
	def build_instruction_prompt(self):
		
		obs = ""
		dead_end = ""
		position = ""
		for a in self._mazeAgent._parentMaze._agents:
			obs += f"{a.agent_name}: {a.obs}\n"
			dead_end += f"{a.agent_name}: {a._mazeAgent.dead_end_in_vision()}\n"
			position += f"{a.agent_name}: {a._mazeAgent.position}\n"

		prompt = self.audit_prompt_template.replace("$OBSERVATIONS$", obs)
		prompt = prompt.replace("$POSITIONS$", position)
		prompt = prompt.replace("$DEAD_ENDS$", dead_end)
		prompt = prompt.replace("$PROGRESS$", f"{self._mazeAgent._parentMaze.score}/{self._mazeAgent._parentMaze.num_items} items found")
		
		prompt = prompt.replace("$INSTRUCTION_HISTORY$", ", ".join([f"{a}: {i[-1]}" for a, i in self.instruction_history.items()]))
		prompt = prompt.replace("$AGENT_NAME$", self._mazeAgent.agent_name)

		return prompt
	
	def get_message(self):
		message_prompt = self.build_message_prompt()
		message, message_info = self.run_LLM(message_prompt)
		message_info.update({"total_cost": self.total_cost})
		return message, message_info
	
	def get_whether_message(self):
		whether_message_prompt = self.build_whether_message_prompt()
		whether_message, whether_message_info = self.run_LLM(whether_message_prompt)
		whether_message_info.update({"total_cost": self.total_cost})
		return whether_message, whether_message_info
	
	def get_instruction(self):
		instruction_prompt = self.build_instruction_prompt()
		instruction, instruction_info = self.run_LLM(instruction_prompt)
		instruction_info.update({"total_cost": self.total_cost})
		return instruction, instruction_info


	def get_action(self):

		available_actions = ["[MOVE] " + str(i) for i in self._mazeAgent._look()[0]]

		if self._mazeAgent.position in self._mazeAgent._parentMaze.item_positions:
			item = self._mazeAgent._parentMaze.item_positions[self._mazeAgent.position]

			if item.item_type == 'regular':
				available_actions += ["[PICK UP] item"]

			elif item.item_type == 'special':
				if not self.action_history[-1].startswith("[PICK UP]") or (self.action_history[-1].startswith("[PICK UP]") and "success" in self.obs[-1]):
					available_actions += ["[PICK UP] item"]
			
		if len(available_actions) == 1:
			action_info = {"action": available_actions[0], "total_cost": self.total_cost}
			return available_actions[0], action_info

		
		plans = self.get_plans(available_actions)
		
		action_prompt = self.build_action_prompt(plans)
		action, action_info = self.run_LLM(action_prompt)
		action = self.parse_answer(available_actions, action)
		action_info.update({"action": action, "total_cost": self.total_cost})
		
		return action, action_info

	def get_plans(self, available_actions):
		plans = ""
		for i, plan in enumerate(available_actions):
			plans += f"{chr(ord('A') + i)}. {plan}"
			if plan.startswith("[MOVE]"):
				if self._mazeAgent._look()[0][i] in self._mazeAgent.dead_end:
					plans += f": This position leads to a dead end."
				else:
					plans += f": This position does not lead to a dead end."
				
				if self._mazeAgent._look()[0][i] not in self._mazeAgent.visited:
					plans += f" This position is unexplored.\n"
				else:
					plans += f" This position has been explored.\n"
			elif plan.startswith('[PICK UP]'):
				plans += f": {self._mazeAgent._parentMaze.item_positions[self._mazeAgent.position].info()}\n"

			else:
				plans += f"\n"
		
		return plans

	def run_LLM(self, prompt):
		info = {}
		chat_prompt = [{"role": "user", "content": prompt}]
		outputs, usage = self.LLM.generate(chat_prompt, self.sampling_params)
		self.total_cost += usage
		response = outputs[0]
		info['prompt'] = prompt
		info['outputs'] = outputs
		info['usage'] = usage
		return response, info

	def run(self):
		action = None
		info = {}
		if self.args.communication == "always":
			message, message_info = self.get_message()
			info['message'] = message_info
			self.step(f"[SEND MESSAGE]: {message}")

			action, action_info = self.get_action()
			info['action'] = action_info
			self.step(action)
		
		if self.args.communication == "optional":
			whether_message, whether_message_info = self.get_whether_message()
			info['whether_message'] = whether_message_info

			if 'yes' in whether_message or 'Yes' in whether_message:
				message, message_info = self.get_message()
				info['message'] = message_info
				self.step(f"[SEND MESSAGE]: {message}")
			
			action, action_info = self.get_action()
			info['action'] = action_info
			self.step(action)
			

		elif self.args.communication == "no":
			action, action_info = self.get_action()
			info['action'] = action_info
			self.step(action)
		
		elif self.args.communication == "audit":
			if self.agent_name == 'Alice' and self.steps % 4 == 1:
				instruction, instruction_info = self.get_instruction()
				info['instruction'] = instruction_info
				self.instruction_history[self.agent_name].append(instruction)

			action, action_info = self.get_action()
			info['action'] = action_info
			self.step(action)

		info["steps"] = self.steps

		if self.args.debug:
			for key, value in info.items():
				print(key)
				print(value)

		return action, info
	
	def step(self, action):


		if action.startswith("[SEND MESSAGE]"):
			# self.action_history.append("[SEND MESSAGE]")
			message = action.split(']')[1].strip()
			self._mazeAgent._parentMaze.dialogue_history.append(f"{self.agent_name}: {message}")
		elif action.startswith("[PICK UP]"):
			self.action_history.append(action)
			self.steps += 1
			self._mazeAgent._parentMaze.total_step += 1
			self.obs.append(self._mazeAgent.pick())
		elif action.startswith("[MOVE]"):
			self.action_history.append(action)
			self.steps += 1
			self._mazeAgent._parentMaze.total_step += 1
			position = action.split(']')[1].strip()
			self.obs.append(self._mazeAgent.move(position))

		self._mazeAgent.check_dead_end()
