import imaplib
import email
from email.header import decode_header
import requests
from dotenv import load_dotenv  # type: ignore
import os
from get_pipeline_id import get_pipeline_id  # Import the function from get_pipeline_id.py

# Load environment variables from .env file
load_dotenv()

# Email account credentials
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("EMAIL_PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER")
IMAP_PORT = int(os.getenv("IMAP_PORT"))
SUPPORT_MAILBOX = os.getenv("SUPPORT_MAILBOX")

# Zenhub credentials
ZENHUB_API_KEY = os.getenv("ZENHUB_API_KEY")
WEB_REPO_ID = os.getenv("WEB_REPO_ID")
MOBILE2_REPO_ID = os.getenv("MOBILE2_REPO_ID")
ZEN_WEB = os.getenv("ZEN_WEB")
ZEN_MOBILE = os.getenv("ZEN_MOBILE")

# GitHub credentials
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Connect to the email server
mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
mail.login(EMAIL, PASSWORD)


# Select the support mailbox
mailbox = f"user/{SUPPORT_MAILBOX}" if SUPPORT_MAILBOX else "inbox"
mail.select(mailbox)

# Search for all emails
status, messages = mail.search(None, "ALL")
email_ids = messages[0].split()

# Helper function to create GitHub issue
def create_github_issue(repo_id, title, body):
    url = f"https://api.github.com/repos/{repo_id}/issues"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "title": title,
        "body": body
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        issue_number = response.json()['number']
        print(f"Successfully created GitHub issue: {response.json()['html_url']}")
        return issue_number
    else:
        print(f"Failed to create GitHub issue: {response.status_code}")
        return None

# Helper function to query ZenHub GraphQL API
def query_zenhub_graphql(query, variables):
    url = "https://api.zenhub.com/public/graphql"
    headers = {
        "Authorization": f"Bearer {ZENHUB_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json={'query': query, 'variables': variables}, headers=headers)
    
    # Check if the connection to ZenHub is successful
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to query ZenHub API: {response.status_code}")
        print(f"Response: {response.text}")
        return None

# Helper function to move Zenhub issue to the "New Issues" pipeline
def move_zenhub_issue(repo_id, issue_number, workspace_id):
    # Get the pipeline ID for "New Issues"
    new_issues_pipeline_id = get_pipeline_id(repo_id, workspace_id)
    if not new_issues_pipeline_id:
        print("Failed to get 'New Issues' pipeline ID, skipping issue movement.")
        return

    # GraphQL mutation to move the issue to the "New Issues" pipeline
    mutation = """
    mutation MoveIssueToPipeline($issueId: ID!, $pipelineId: ID!, $position: String!) {
      moveIssueToPipeline(input: {issueId: $issueId, pipelineId: $pipelineId, position: $position}) {
        issue {
          id
          title
        }
      }
    }
    """
    variables = {
        "issueId": issue_number,
        "pipelineId": new_issues_pipeline_id,
        "position": "top"
    }
    result = query_zenhub_graphql(mutation, variables)
    
    if result and 'data' in result and 'moveIssueToPipeline' in result['data']:
        print(f"Successfully moved issue #{issue_number} to 'New Issues' pipeline in workspace {workspace_id}")
    else:
        print("Failed to move issue to 'New Issues' pipeline.")


# Process emails
for email_id in email_ids:
    status, msg_data = mail.fetch(email_id, "(RFC822)")
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            subject = decode_header(msg["Subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()

            # Check if the subject contains "ISSUE"
            if "ISSUE" in subject.upper():
                from_ = msg.get("From")
                print(f"Subject: {subject}")
                print(f"From: {from_}")

                # Extract email body
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        try:
                            body = part.get_payload(decode=True).decode()
                        except:
                            pass
                else:
                    body = msg.get_payload(decode=True).decode()

                print(f"Body: {body}\n")

                # Determine which repository and workspace to use
                if "WEB" in subject.upper():
                    repo_id = WEB_REPO_ID
                    workspace_id = ZEN_WEB
                elif "MOBILE" in subject.upper():
                    repo_id = MOBILE2_REPO_ID
                    workspace_id = ZEN_MOBILE
                else:
                    print("Unknown issue type, skipping.")
                    continue

                # Create GitHub issue and move to Zenhub workspace
                issue_number = create_github_issue(repo_id, subject, body)
                if issue_number:
                    move_zenhub_issue(repo_id, issue_number, workspace_id)

# Close the connection and logout
mail.close()
mail.logout()

