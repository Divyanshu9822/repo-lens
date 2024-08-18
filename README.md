# Repo Lens

🔍 **Repo Lens** is a powerful tool for seamlessly exploring GitHub repositories. With an integrated AI chatbot that is context-aware and remembers all conversation history, it specializes in answering queries related to the repository's structure, files, and code. This feature makes it easier to understand and navigate codebases.

![image](https://github.com/user-attachments/assets/be421843-3d26-47dd-86ce-d781c1b44e86)

## Features

- **GitHub Integration**: Authenticate with GitHub to access and explore repository contents.
- **Context-Aware Chatbot**: Engage with an AI chatbot that retains conversational context, helping you navigate and understand the repository effectively.
- **Dynamic Repository Structure**: View the complete directory structure of the repository.
- **Source Code Retrieval**: Fetch source code from files within the repository based on your queries.
- **Customizable AI Models**: Select from various Groq models tailored for different types of interactions.

## Prerequisites

Before you start, ensure you have the following:

- **Python 3.8+**
- **Streamlit**: For building the web interface.
- **Groq API Key**: For AI functionalities.
- **GitHub Account**: For authentication to use GitHub APIs.

## Installation

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/your-username/repo-lens.git
    cd repo-lens
    ```

2. **Create and Activate a Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Set Up GitHub OAuth Application**:
    - Go to [GitHub OAuth applications](https://github.com/settings/applications/new).
    - **Homepage URL**: `http://localhost:8501`
    - **Authorization callback URL**: `http://localhost:8501/`
    - Save your **Client ID** and **Client Secret**.

5. **Set Up Environment Variables**:
    Create a `.env` file in the root directory and add the following variables:
    ```env
    GITHUB_CLIENT_ID=your_github_client_id
    GITHUB_CLIENT_SECRET=your_github_client_secret
    REDIRECT_URI=http://localhost:8501/
    ```

## Running the Application

1. **Start the Streamlit App**:
    ```bash
    streamlit run app.py
    ```

2. **Open Your Browser**: Navigate to `http://localhost:8501` to interact with Repo Lens.

## How to Use

1. **Log In**: Click the **Log in with GitHub** button to authenticate.
2. **Enter API Key**: Provide your Groq API key in the sidebar to enable AI features.
3. **Select Model**: Choose a Groq model from the dropdown menu.
4. **Enter Repository URL**: Input the full URL of the GitHub repository you wish to explore.
5. **Interact with Chatbot**: Use the chat interface to ask questions about the repository. The chatbot will retain the context of your conversation, making it easier to get relevant responses.

## Deployment

When deploying your application:

- Update the **Homepage URL** and **Authorization callback URL** in your GitHub OAuth settings to match your deployed URL.
- Ensure that your `.env` file or environment variables are correctly configured for production use.


## Contact

For any questions or issues, please contact [Divyanshu Prasad](https://divyanshuprasad.dev/).
