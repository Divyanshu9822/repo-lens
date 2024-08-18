import os
from dotenv import load_dotenv
from groq import Groq
import streamlit as st
import requests
from authlib.integrations.requests_client import OAuth2Session
from urllib.parse import urlparse
from langchain.chains import LLMChain
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import SystemMessage
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
import json
import base64

# Load environment variables
load_dotenv()

TOOL_CALL_MODEL = "llama3-groq-70b-8192-tool-use-preview"

# OAuth credentials
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

# OAuth redirect URI
REDIRECT_URI = "http://localhost:8501/"

# Create an OAuth2 session
oauth = OAuth2Session(
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
)


# Function to get file source code
def fetch_file_source_code(file_path, repo_owner, repo_name, headers):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        file_content = response.json().get("content", "")
        return base64.b64decode(file_content).decode("utf-8")
    else:
        return f"Failed to fetch file: {response.status_code} - {response.text}"


# Streamlit configuration
st.set_page_config(page_title="Repo Lens", layout="wide")

# Sidebar for about, guide, and repository structure
with st.sidebar:
    st.write("## 🔍 About")
    st.write(
        "🛠️ Repo Lens is a tool for exploring GitHub repositories and interacting with an AI chatbot specialized in repository queries."
    )
    st.write("## 📝 Guide")
    st.write(
        "1. **🔑 Login**: Click the login button to authenticate with GitHub.\n"
        "2. **🔑 Enter API Key**: Provide your Groq API key in the sidebar.\n"
        "3. **🛠️ Select Model**: Choose the Groq model you want to use.\n"
        "4. **🔗 Enter Repository URL**: Provide the full GitHub repository URL.\n"
        "5. **💬 Explore and Chat**: View the repository structure and interact with the AI chatbot for repository-related queries."
    )

    # Repo URL input and structure display
    if "token" in st.session_state:
        st.write("## GitHub Repository URL")
        repo_url_input = st.text_input("Enter the full GitHub repository URL:")

        if repo_url_input:
            token = st.session_state.token
            headers = {"Authorization": f"token {token['access_token']}"}
            parsed_url = urlparse(repo_url_input)
            path_parts = parsed_url.path.strip("/").split("/")

            if len(path_parts) == 2:
                repo_owner, repo_name = path_parts
                repo_api_url = (
                    f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/"
                )

                def fetch_directory_contents(url, headers):
                    response = requests.get(url, headers=headers)
                    if response.status_code == 200:
                        contents = response.json()
                        structure = []
                        for item in contents:
                            if item["type"] == "dir":
                                subdir_url = item["url"]
                                subdir_contents = fetch_directory_contents(
                                    subdir_url, headers
                                )
                                structure.append(
                                    {
                                        "type": "dir",
                                        "path": item["path"],
                                        "contents": subdir_contents,
                                    }
                                )
                            else:
                                structure.append({"type": "file", "path": item["path"]})
                        return structure
                    else:
                        st.error(
                            f"🚨 Failed to fetch contents: {response.status_code} - {response.text}"
                        )
                        return []

                repo_structure = fetch_directory_contents(repo_api_url, headers)

                def format_structure(structure, level=0):
                    result = ""
                    for item in structure:
                        if item["type"] == "dir":
                            result += f"{'│   ' * level}├── 📁 {item['path']}\n"
                            result += format_structure(item["contents"], level + 1)
                        else:
                            result += f"{'│   ' * level}├── 📄 {item['path']}\n"
                    return result

                formatted_structure = format_structure(repo_structure)
                st.write("### 📂 Repository Structure")
                st.text(formatted_structure)

            else:
                st.error(
                    "🚨 The URL must be in the format 'https://github.com/owner/repo'."
                )

# OAuth authentication
if "code" in st.query_params:
    if "token" not in st.session_state:
        code = st.query_params["code"]

        try:
            token = oauth.fetch_token(
                "https://github.com/login/oauth/access_token",
                authorization_response=st.query_params,
                code=code,
            )
            st.session_state.token = token
            st.toast("Login successful!", icon="✅")
        except Exception as e:
            st.error(f"🚨 An error occurred while fetching the token: {e}")

# Display login button if not logged in
if "token" not in st.session_state:
    auth_url, _ = oauth.create_authorization_url(
        "https://github.com/login/oauth/authorize"
    )
    st.write("## Welcome to Repo Lens 🕵️‍♂️")
    st.link_button("Log in with GitHub", auth_url)

# Main chat interface
if "token" in st.session_state:
    st.write("### 💬 Chat with Repo Lens")

    st.sidebar.header("Settings")

    api_key = st.sidebar.text_input("Enter your Groq API key:", type="password")

    selected_model = st.sidebar.selectbox(
        "Select a model:",
        [
            "gemma-7b-it",
            "gemma2-9b-it",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "llama-guard-3-8b",
            "llama3-70b-8192",
            "llama3-8b-8192",
            "mixtral-8x7b-32768",
        ],
        index=2,
    )

    st.sidebar.warning(
        "Note: Each model has its own limits on requests and tokens. If you exceed these limits, you may encounter runtime errors."
    )

    if api_key:
        os.environ["GROQ_API_KEY"] = api_key

        # Initialize Groq client
        client = Groq(api_key=api_key)

        # Function to retrieve source code using the AI assistant
        def retrieve_source_code(user_prompt, repo_owner, repo_name, token):
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

            response = client.chat.completions.create(
                model=TOOL_CALL_MODEL,
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

                second_response = client.chat.completions.create(
                    model=TOOL_CALL_MODEL, messages=messages
                )
                return second_response.choices[0].message.content
            else:
                return "🚨 No tool calls found in the response."

        if "groq_model" not in st.session_state:
            st.session_state["groq_model"] = selected_model

        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        memory = ConversationBufferWindowMemory(
            k=5, memory_key="chat_history", return_messages=True
        )

        for message in st.session_state.chat_history:
            memory.save_context({"input": message["human"]}, {"output": message["AI"]})

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask me anything about the repo or code..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            chat_prompt = ChatPromptTemplate.from_messages(
                [
                    SystemMessage(
                        content=f"You are an AI assistant specialized in answering questions and providing insights about GitHub repository '{repo_name}' owned by '{repo_owner}'. The structure of the repository is as follows: '{formatted_structure}'. Your role is to help users understand and navigate the codebase, offering explanations and insights about files, directories, and code within the repository."
                    ),
                    MessagesPlaceholder(variable_name="chat_history"),
                    HumanMessagePromptTemplate.from_template("{human_input}"),
                ]
            )

            groq_chat = ChatGroq(groq_api_key=api_key, model_name=selected_model)

            conversation = LLMChain(
                llm=groq_chat, prompt=chat_prompt, verbose=True, memory=memory
            )

            # Prompt to extract file path and retrieve source code
            extract_code_prompt = (
                f"Please extract the file path from the following user prompt. If the user is asking about code or requesting a brief about a file, retrieve the source code for the specified file. "
                f"Here is the user prompt from which you need to extract the file path: {prompt}. "
                f"Note: If the prompt only contains a file name, assume it is in the root directory and treat it as the file path."
            )

            # Retrieve source code using the extracted file path
            source_code = retrieve_source_code(
                prompt, repo_owner, repo_name, st.session_state.token["access_token"]
            )

            # Append the source code to the original prompt
            enhanced_prompt = (
                f"Prompt: {prompt}\n\n"
                f"Source Code/Brief fetched using another AI:\n{source_code}"
            )

            # Predict response using the updated prompt with source code
            response = conversation.predict(human_input=enhanced_prompt)

            with st.chat_message("assistant"):
                st.markdown(response)

            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.chat_history.append({"human": prompt, "AI": response})
    else:
        st.error("Please enter your API key in the sidebar to start chatting.")
else:
    st.write(
        "🔒 Please log in to view the repository structure and interact with an AI chatbot specialized in repository queries."
    )
