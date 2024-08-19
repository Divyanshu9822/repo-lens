import json
from groq import Groq
from components.repo import fetch_file_source_code
from config.config import TOOL_CALL_MODEL

class GroqClient:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        self.model = TOOL_CALL_MODEL
    
    def retrieve_source_code(self, user_prompt, repo_owner, repo_name, token):
        messages = [
            {
                "role": "system",
                "content": (
                        "You are an AI assistant specialized in retrieving source code from a GitHub repository. "
                        "Your task is to extract the file path from the user prompt and use the 'fetch_file_source_code' function "
                        "to retrieve the file contents. If the prompt mentions a file name, assume it is located in the root directory."
                    ),
            },
            {"role": "user", "content": user_prompt},
        ]

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "fetch_file_source_code",
                    "description": "Fetch the source code of a file in the GitHub repository",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "The path of the file to fetch",
                            }
                        },
                        "required": ["file_path"],
                    },
                },
            }
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=4096,
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            available_functions = {
                "fetch_file_source_code": lambda file_path: fetch_file_source_code(
                    file_path,
                    repo_owner,
                    repo_name,
                    {"Authorization": f"token {token}"},
                ),
            }
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                file_path = function_args.get("file_path")
                function_response = function_to_call(file_path=file_path)

                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(function_response),
                    }
                )

            second_response = self.client.chat.completions.create(
                model=self.model, messages=messages
            )
            return second_response.choices[0].message.content
        else:
            return "🚨 No tool calls found in the response."
