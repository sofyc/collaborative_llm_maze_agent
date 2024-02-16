import random

import openai
# import torch
import json
import os
import pandas as pd
from openai import OpenAIError
from openai import RateLimitError
import backoff

from openai import AzureOpenAI
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),  
    api_version="2023-12-01-preview",
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
)

class LLM:
	def __init__(self,
				 lm_id,
				 communication,
				 agent_id
				 ):
		
		self.agent_id = agent_id

		self.communication = communication
		self.lm_id = lm_id
		self.total_cost = 0
		# self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

	@backoff.on_exception(backoff.expo, RateLimitError)
	def generate(self, prompt, sampling_params):
		usage = 0
		response = client.chat.completions.create(
			model=self.lm_id, messages=prompt, **sampling_params
		)

		generated_samples = [response.choices[i].message.content for i in
								range(sampling_params['n'])]
		if 'gpt-4' in self.lm_id:
			usage = response.usage.prompt_tokens * 0.01 / 1000 + response.usage.completion_tokens * 0.03 / 1000
		elif ('gpt-3.5' in self.lm_id) or ('gpt-35' in self.lm_id):
			usage = response.usage.prompt_tokens * 0.0005 / 1000 + response.usage.completion_tokens * 0.0015 / 1000

		return generated_samples, usage