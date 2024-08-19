import requests
import base64

def fetch_file_source_code(file_path, repo_owner, repo_name, headers):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        file_content = response.json().get("content", "")
        return base64.b64decode(file_content).decode("utf-8")
    else:
        return f"Failed to fetch file: {response.status_code} - {response.text}"

def fetch_directory_contents(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        contents = response.json()
        structure = []
        for item in contents:
            if item["type"] == "dir":
                subdir_url = item["url"]
                subdir_contents = fetch_directory_contents(subdir_url, headers)
                structure.append({
                    "type": "dir",
                    "path": item["path"],
                    "contents": subdir_contents,
                })
            else:
                structure.append({"type": "file", "path": item["path"]})
        return structure, response.status_code
    else:
        return [], response.status_code
