import textwrap
import json

import google.generativeai as genai
from typing import Dict


def get_api_key() -> str:
    # Load API key from the config file
    with open("./key.json", "r") as config_file:
        config_data = json.load(config_file)

    api_key = config_data.get("api_key")

    if api_key is None:
        return None

    return api_key


class LLMChat:
    def __init__(self, api_key, security_settings, model_name="gemini-pro"):
        genai.configure(api_key=api_key)

        if security_settings is not None:
            # If security settings are provided, use them when initializing the model
            self.model = genai.GenerativeModel(
                model_name, safety_settings=security_settings
            )
        else:
            # If no security settings are provided, initialize the model without them
            self.model = genai.GenerativeModel(model_name)

        self.chat = self.model.start_chat(history=[])

    def send_message(self, message):
        response = self.chat.send_message(message)
        return response.text

    def get_chat_history(self):
        return self.chat.history

    def get_model_info(self):
        return self.chat.model
