import requests
import os

"""
Plan:
Authorisation via headers and bearer token for the get and post reqeusts

get_issue_comments
- end point for comments on issues : /repos/{REPO_OWNER}/{REPO_NAME}/issues/{issue_number}/comments
    - return data

add_heart_reaction
 - end point for adding reactions to comments: /repos/{REPO_OWNER}/{REPO_NAME}/issues/comments/{comment_id}/reactions
    - post payload  to the endpoint return r.json()

- main()
    - set the comments to the correct issue
    - loop through each comment and look at the body
        - if the body contains the word heart add the heart reaction to the id of that comment


IMPROVEMENTS:
- error handling
    - add timeouts to all calls
    - exponential backoff
- handle edge cases
    - empty body
    - we could look for different heart variants
        - heart emojis or variations <3, :heart:
    - hearts inside of code blocks
    - missing GITHUB_TOKEN
    - invalid REPO_NAME
    - invalid REPO_OWNER
- fetching comments with pagination if we had large amounts of comments
- implement a circuit breaker to fail fast
- implement rate limiting if necessary
- implement custom exceptions
"""
api_token = os.environ.get("GITHUB_API_TOKEN")
REPO_NAME = "FinancialQA"
REPO_OWNER = "joeyatesss"
GITHUB_API_URL = "https://api.github.com"

def get_issue_comments(issue_number: int):
    """Fetch comments for a specific GitHub issue."""

    url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/issues/{issue_number}/comments"

    headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {api_token}"
        }
    if not api_token:
        raise RuntimeError("GITHUB_API_TOKEN is not set in environment.")

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as req_e:
        # Network errors, timeouts, HTTP errors
        raise RuntimeError(f"Failed to fetch issue comments: {req_e}") from req_e
    except ValueError as e:
        # JSON decoding errors
        raise RuntimeError(f"Invalid JSON in response: {e}") from e

    try:
        for comment in data:
            body_preview = (comment.get("body") or "").strip()
            print(f"{comment['id']}: {body_preview}")
    except (KeyError, TypeError) as e:
        raise RuntimeError(f"Unexpected comment data structure: {e}") from e

    return data

def add_heart_reaction(comment_id: int):
    url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/issues/comments/{comment_id}/reactions"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {api_token}",
    }
    payload = {"content": "heart"}
    if not api_token:
        raise RuntimeError("GITHUB_API_TOKEN is not set in environment.")

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as req_err:
        raise RuntimeError(f"Failed to add heart reaction to comment {comment_id}: {req_err}") from req_err
    except ValueError as json_err:
        raise RuntimeError(f"Invalid JSON in reaction response: {json_err}") from json_err
 
def main():
    try:
        comments = get_issue_comments(1)
        for c in comments:
            body = (c.get("body") or "").lower()
            if ("heart" in body):
                add_heart_reaction(c["id"])
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()
