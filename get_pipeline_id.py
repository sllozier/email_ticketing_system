import requests
from dotenv import load_dotenv  # type: ignore
import os

# Load environment variables from .env file
load_dotenv()

# Zenhub credentials
ZENHUB_API_KEY = os.getenv("ZENHUB_API_KEY")
WEB_REPO_ID = os.getenv("WEB_REPO_ID")
MOBILE2_REPO_ID = os.getenv("MOBILE2_REPO_ID")
ZEN_WEB = os.getenv("ZEN_WEB")
ZEN_MOBILE = os.getenv("ZEN_MOBILE")

# Check if the token is loaded properly
if ZENHUB_API_KEY is None:
    print("Error: ZENHUB_API_KEY is not set. Please check your .env file.")
else:
    print(f"ZENHUB_API_KEY is loaded: {ZENHUB_API_KEY[:4]}****{ZENHUB_API_KEY[-4:]}")  # Print a masked version of the token

# Helper function to query ZenHub GraphQL API
def query_zenhub_graphql(query):
    url = "https://api.zenhub.com/public/graphql"
    headers = {
        "Authorization": f"Bearer {ZENHUB_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json={'query': query}, headers=headers)
    
    # Check if the connection to ZenHub is successful
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to query ZenHub API: {response.status_code}")
        print(f"Response: {response.text}")
        return None

# Query to get the workspace details
def get_workspace_details(repo_id):
    query = f"""
    {{
        repositoryById(id: "{repo_id}") {{
            workspaces {{
                nodes {{
                    id
                    name
                }}
            }}
        }}
    }}
    """
    result = query_zenhub_graphql(query)
    if result:
        workspaces = result.get('data', {}).get('repositoryById', {}).get('workspaces', {}).get('nodes', [])
        for workspace in workspaces:
            print(f"Workspace Name: {workspace['name']}, ID: {workspace['id']}")
    else:
        print("No workspaces found or failed to retrieve workspaces.")

# Helper function to get pipeline ID for "New Issues"
def get_pipeline_id(repo_id, workspace_id, pipeline_name="New Issues"):
    print(f"Requesting pipelines for repo_id: {repo_id} and workspace_id: {workspace_id}")  # Debugging line
    query = f"""
    {{
        workspace(id: "{workspace_id}") {{
            pipelinesConnection {{
                nodes {{
                    id
                    name
                }}
            }}
        }}
    }}
    """
    result = query_zenhub_graphql(query)
   
    if result:
        pipelines = result.get('data', {}).get('workspace', {}).get('pipelinesConnection', {}).get('nodes', [])
        for pipeline in pipelines:
            if pipeline['name'] == pipeline_name:
                print(f"Pipeline ID for '{pipeline_name}' in workspace '{workspace_id}' is {pipeline['id']}")
                return pipeline['id']
        print(f"Pipeline '{pipeline_name}' not found.")
        return None
    else:
        print("Failed to get pipelines.")
        return None

# Interactive prompt to choose between WEB and MOBILE
choice = input("Choose the workspace to check (WEB/MOBILE): ").strip().upper()

if choice == "WEB":
    print(f"WEB_REPO_ID: {WEB_REPO_ID}")  # Debugging line
    print(f"ZEN_WEB: {ZEN_WEB}")  # Debugging line
    print("Web Workspace:")
    web_pipeline_id = get_pipeline_id(WEB_REPO_ID, ZEN_WEB)
    if web_pipeline_id:
        print(f"Web workspace 'New Issues' pipeline ID: {web_pipeline_id}")
    else:
        print("Failed to retrieve Web workspace pipeline ID.")
elif choice == "MOBILE":
    print(f"MOBILE2_REPO_ID: {MOBILE2_REPO_ID}")  # Debugging line
    print(f"ZEN_MOBILE: {ZEN_MOBILE}")  # Debugging line
    print("Mobile Workspace:")
    mobile_pipeline_id = get_pipeline_id(MOBILE2_REPO_ID, ZEN_MOBILE)
    if mobile_pipeline_id:
        print(f"Mobile workspace 'New Issues' pipeline ID: {mobile_pipeline_id}")
    else:
        print("Failed to retrieve Mobile workspace pipeline ID.")
else:
    print("Invalid choice. Please choose either 'WEB' or 'MOBILE'.")
