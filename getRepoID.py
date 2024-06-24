import requests
from dotenv import load_dotenv  # type: ignore
import os

# Load environment variables from .env file
load_dotenv()

# GitHub credentials
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Check if the token is loaded properly
if GITHUB_TOKEN is None:
    print("Error: GITHUB_TOKEN is not set. Please check your .env file.")
else:
    print(f"GITHUB_TOKEN is loaded: {GITHUB_TOKEN[:4]}****{GITHUB_TOKEN[-4:]}")  # Print a masked version of the token

# Function to get the repository ID
def get_repo_id(repo_url):
    # Extract the repo name from the URL
    repo_name = '/'.join(repo_url.split('/')[-2:])
    url = f"https://api.github.com/repos/{repo_name}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        repo_id = response.json().get("id")
        print(f"Repository ID for {repo_name} is {repo_id}")
        return repo_id
    else:
        print(f"Failed to get repository ID: {response.status_code}, {response.json()}")
        return None

# Prompt the user for a repository URL
repo_url = input("Enter the GitHub repository URL: ")
get_repo_id(repo_url)


