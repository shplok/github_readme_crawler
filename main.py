import os
import requests
from dotenv import load_dotenv
import base64
import re

# Load environment variables from token.env
load_dotenv("token.env")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
KEYWORDS = os.getenv("KEYWORDS", "").split(", ") if os.getenv("KEYWORDS") else []

def search_repos(keyword, max_results=5):
    url = f"https://api.github.com/search/repositories?q={keyword}&per_page={max_results}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
    response.raise_for_status()
    return response.json()["items"]

def get_readme(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        content = response.json()["content"]
        decoded = base64.b64decode(content).decode("utf-8")
        return decoded.splitlines()
    return []

def save_to_csv(text, filename="repos"): 
    with open(f"{filename}_{KEYWORDS[0]}.csv", "a", encoding="utf-8") as file:
        if not os.path.exists(f"{filename}_{KEYWORDS[0]}.csv"):
            file.write("Repository,Keyword\n")
        file.write(text + "\n")

def extract_keywords_from_line(line, keywords):
    return [kw for kw in keywords if re.search(rf"\b{re.escape(kw)}\b", line)]

def main():
    all_repos = []
    keywords = KEYWORDS
    for word in keywords:
        try:
            all_repos.extend(search_repos(word))
        except requests.exceptions.HTTPError as e:
            print(f"Failed to search for keyword '{word}': {e}")

    for repo in all_repos:
        owner = repo["owner"]["login"]
        name = repo["name"]
        print(f"Scanning README from {owner}/{name}...")
        readme_lines = get_readme(owner, name)

        if readme_lines:
            found_keywords = set()
            for line in readme_lines:
                matches = extract_keywords_from_line(line, keywords)
                found_keywords.update(matches)

            if found_keywords:
                save_to_csv(f"# {owner}/{name} ({repo['html_url']})")
                for match in found_keywords:
                    save_to_csv(match)
        else:
            print(f"No README found for {owner}/{name}")

if __name__ == "__main__":
    main()
