from urllib.parse import urlparse

def parse_repo_url(repo_url):
    parsed_url = urlparse(repo_url)
    path_parts = parsed_url.path.strip("/").split("/")
    if len(path_parts) == 2:
        return path_parts[0], path_parts[1]
    else:
        return None, None

def format_structure(structure, level=0):
    result = ""
    for item in structure:
        if item["type"] == "dir":
            result += f"{'│   ' * level}├── 📁 {item['path']}\n"
            result += format_structure(item["contents"], level + 1)
        else:
            result += f"{'│   ' * level}├── 📄 {item['path']}\n"
    return result
