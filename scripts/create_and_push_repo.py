import json
import urllib.request
import subprocess
import sys

def create_and_push():
    import os
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN environment variable is not set. Please run: $env:GITHUB_TOKEN='your_pat' before executing.")
        sys.exit(1)
    username = "rajaditya1186-ai"
    repo_name = "Research-Assistant-Swarm"
    
    print("==================================================")
    print("START: GitHub Repository Creation & Push Suite")
    print("==================================================")
    
    # 1. Create Repository via GitHub REST API
    url = "https://api.github.com/user/repos"
    payload = {
        "name": repo_name,
        "description": "Production-ready ScholarSwarm AI multi-agent literature synthesist assistant built with Google ADK, MCP, and Streamlit.",
        "private": False,
        "has_issues": True,
        "has_projects": True,
        "has_wiki": True
    }
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "ScholarSwarm-Agent"
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    try:
        print(f"Creating repository '{repo_name}' on GitHub under user '{username}'...")
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            print(f"SUCCESS: Repository created successfully! URL: {res_data.get('html_url')}")
    except urllib.error.HTTPError as he:
        if he.code == 422:
            print("INFO: Repository already exists on GitHub, proceeding to push...")
        elif he.code == 403 or he.code == 401:
            print(f"WARNING: GitHub API returned status {he.code} (Forbidden/Unauthorized).")
            print("Please ensure you have created a blank repository named 'Research-Assistant-Swarm' at https://github.com/new manually.")
            print("Continuing to push commits...")
        else:
            print(f"WARNING: GitHub API returned status {he.code} - {he.reason}. Continuing to push...")
    except Exception as e:
        print(f"WARNING: Failed to call GitHub API - {str(e)}. Continuing to push...")
        
    # 2. Push Code via Git using authenticated Remote URL
    auth_remote = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"
    clean_remote = f"https://github.com/{username}/{repo_name}.git"
    
    try:
        print("Configuring remote URL with token authentication...")
        # Remove origin if it exists
        subprocess.run(["git", "remote", "remove", "origin"], stderr=subprocess.DEVNULL)
        # Add authenticated remote
        subprocess.run(["git", "remote", "add", "origin", auth_remote], check=True)
        
        print("Pushing commits to remote main branch...")
        push_res = subprocess.run(
            ["git", "push", "-u", "origin", "main"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60
        )
        
        if push_res.returncode == 0:
            print("SUCCESS: Code pushed successfully to GitHub!")
        else:
            print(f"ERROR: Git push failed (Exit code {push_res.returncode})")
            print(push_res.stdout)
            print(push_res.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"ERROR: Git command execution encountered failure - {str(e)}")
        sys.exit(1)
        
    finally:
        # 3. Clean up credentials from remote URL
        print("Cleaning up remote URL credentials for safety...")
        subprocess.run(["git", "remote", "set-url", "origin", clean_remote])
        
    print("==================================================")
    print("FINISHED: All tasks completed successfully!")
    print("==================================================")

if __name__ == "__main__":
    create_and_push()
