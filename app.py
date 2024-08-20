import os
import streamlit as st
from langchain.chains import LLMChain
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import SystemMessage
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from components.repo import fetch_directory_contents
from utils.github_utils import format_structure, parse_repo_url
from components.auth import Auth
from utils.ai_tooling import GroqClient

# Create an OAuth2 session
oauth = Auth()

# Streamlit configuration
st.set_page_config(page_title="Repo Lens", layout="wide")

# Sidebar for about, guide, and repository structure
with st.sidebar:
    with st.expander("🔍 About", expanded=True):
        st.write(
            "🛠️ **Repo Lens** is a powerful tool for seamlessly exploring GitHub repositories. "
            "With an integrated AI chatbot, it specializes in answering queries related to the repository's structure, files, and code, "
            "making it easier to understand and navigate complex codebases."
        )

    with st.expander("📝 Guide", expanded=False):
        st.write(
            "1. **🔑 Login**: Click the **Log in with GitHub** button to authenticate with your GitHub account.\n"
            "2. **🔐 Enter API Key**: Input your Groq API key in the sidebar to enable AI functionalities.\n"
            "3. **🛠️ Select Model**: Choose your preferred Groq model for AI interactions.\n"
            "4. **🔗 Enter Repository URL**: Provide the complete GitHub repository URL to load its structure.\n"
            "5. **💬 Chat and Explore**: Use the chat interface to ask questions and get insights about the repository's code and structure."
        )

    # Repo URL input and structure display
    if "token" in st.session_state:
        st.write("## GitHub Repository URL")
        repo_url_input = st.text_input("Enter the full GitHub repository URL:")

        if repo_url_input:
            token = st.session_state.token
            headers = {"Authorization": f"token {token['access_token']}"}

            repo_owner, repo_name = parse_repo_url(repo_url_input)
            if repo_owner and repo_name:
                repo_api_url = (
                    f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/"
                )

                repo_structure, status_code = fetch_directory_contents(
                    repo_api_url, headers
                )
                if status_code != 200:
                    st.error(f"🚨 Failed to fetch repo content: {status_code}")

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
                authorization_response=st.query_params,
                code=code,
            )
            st.session_state.token = token
            st.toast("Login successful!", icon="✅")
        except Exception as e:
            st.error(f"🚨 An error occurred while fetching the token: {e}")

# Display login button if not logged in
if "token" not in st.session_state:
    auth_url, _ = oauth.get_auth_url()
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

    if api_key and repo_url_input:
        os.environ["GROQ_API_KEY"] = api_key

        # Initialize Groq client
        client = GroqClient(api_key=api_key)

        # Function to retrieve source code using the AI assistant
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
                        content=f"You are an AI assistant specialized in answering questions and providing insights about GitHub repository '{repo_name}' owned by '{repo_owner}'."
                        f"The structure of the repository is as follows:\n '{formatted_structure}'."
                        f"Your role is to help users understand and navigate the codebase, offering explanations and insights about files, directories, and code within the repository."
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
            source_code = client.retrieve_source_code(
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
        st.error("Enter your API key and repo link in the sidebar to start chatting.")
else:
    st.write(
        "🔒 Please log in to view the repository structure and interact with an AI chatbot specialized in repository queries."
    )
