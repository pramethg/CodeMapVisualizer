
import os
import subprocess
import requests
import json


class LinearService:
    def __init__(self):
        pass

    def _get_visualizer_env_path(self, root_path: str):
        return os.path.join(root_path, "assets", ".visualizer", ".env")

    def check_connection(self, root_path: str):
        env_path = self._get_visualizer_env_path(root_path)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(env_path), exist_ok=True)
        
        if not os.path.exists(env_path):
            # Create template
            with open(env_path, "w") as f:
                f.write("""# Linear Integration Configuration
# 
# 1. LINEAR_API_KEY (Required):
#    - Go to Linear -> Click your profile picture -> Account -> API
#    - Under "Personal API keys", click "Create key"
#    - Name it "CodeMapVisualizer" and copy the key (starts with 'lin_')
#
# 2. LINEAR_TEAM_ID (Optional, defaults to your first team):
#    - Open a specific team in Linear -> Cmd+K -> "Copy Team ID"
#
# 3. LINEAR_PROJECT_ID (Optional, to auto-assign issues to a project):
#    - Open a project -> Cmd+K -> "Copy Project ID"

LINEAR_API_KEY=
LINEAR_TEAM_ID=
LINEAR_PROJECT_ID=
""")
            return {"connected": False, "message": "Created assets/.visualizer/.env template"}
        
        # Load env vars from this specific file
        config = {}
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    config[key] = value.strip().strip('"').strip("'")
        
        api_key = config.get("LINEAR_API_KEY")
        
        if not api_key:
            return {"connected": False, "message": "Missing API Key in assets/.visualizer/.env"}
            
        # Validate connection
        try:
            headers = {"Authorization": api_key, "Content-Type": "application/json"}
            query = """
            query {
              viewer {
                id
                name
                email
              }
            }
            """
            response = requests.post("https://api.linear.app/graphql", json={"query": query}, headers=headers)
            if response.status_code == 200 and "data" in response.json():
                return {"connected": True, "user": response.json()["data"]["viewer"]}
            else:
                return {"connected": False, "message": "Invalid API Key"}
        except Exception as e:
            return {"connected": False, "message": str(e)}

    def _get_github_url(self, root_path: str, file_path: str, line_number: int):
        try:
            # Get remote URL
            remote_url = subprocess.check_output(
                ["git", "config", "--get", "remote.origin.url"], 
                cwd=root_path
            ).decode("utf-8").strip()
            
            # Get current branch
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], 
                cwd=root_path
            ).decode("utf-8").strip()
            
            # Normalize remote URL (handle SSH)
            # git@github.com:user/repo.git -> https://github.com/user/repo
            if remote_url.startswith("git@"):
                remote_url = remote_url.replace(":", "/").replace("git@", "https://")
            
            if remote_url.endswith(".git"):
                remote_url = remote_url[:-4]
                
            # Construct blob URL
            # Relativize path
            rel_path = os.path.relpath(file_path, root_path)
            
            return f"{remote_url}/blob/{branch}/{rel_path}#L{line_number}"
        except Exception as e:
            print(f"Failed to get git info: {e}")
            return None

    def create_issue(self, root_path: str, title: str, description: str, file_path: str, line_number: int, tag: str):
        env_path = self._get_visualizer_env_path(root_path)
        if not os.path.exists(env_path):
             return {"success": False, "error": "Configuration not found"}

        config = {}
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    config[key] = value.strip().strip('"').strip("'")

        api_key = config.get("LINEAR_API_KEY")
        team_id = config.get("LINEAR_TEAM_ID")
        project_id = config.get("LINEAR_PROJECT_ID")
        
        if not api_key:
             return {"success": False, "error": "Missing Linear API Key"}

        headers = {"Authorization": api_key, "Content-Type": "application/json"}
        
        # If team_id is missing, try to fetch the first team
        if not team_id:
            try:
                teams_query = """
                query {
                  viewer {
                    teams(first: 1) {
                      nodes {
                        id
                      }
                    }
                  }
                }
                """
                response = requests.post("https://api.linear.app/graphql", json={"query": teams_query}, headers=headers)
                data = response.json()
                if "data" in data and data["data"]["viewer"]["teams"]["nodes"]:
                     team_id = data["data"]["viewer"]["teams"]["nodes"][0]["id"]
                else:
                     # Fallback if no teams found?
                     pass
            except Exception:
                pass
        
        if not team_id:
             return {"success": False, "error": "Could not determine Linear Team ID. Please set LINEAR_TEAM_ID in .env"}

        # Generate GitHub Link
        github_link = self._get_github_url(root_path, file_path, line_number)
        
        full_description = f"{description}"
        if github_link:
            full_description += f"\n\n---\nCode: {github_link}"
            
        full_title = f"{tag.upper()}: {title}" if tag and tag != "none" else title

        mutation = """
        mutation CreateIssue($title: String!, $description: String!, $teamId: String!, $projectId: String) {
          issueCreate(input: {
            title: $title
            description: $description
            teamId: $teamId
            projectId: $projectId
          }) {
            success
            issue {
              id
              identifier
              url
            }
          }
        }
        """
        
        variables = {
            "title": full_title,
            "description": full_description,
            "teamId": team_id,
            "projectId": project_id 
        }
        
        try:
            response = requests.post(
                "https://api.linear.app/graphql", 
                json={"query": mutation, "variables": variables}, 
                headers=headers
            )
            result = response.json()
            
            if "errors" in result:
                return {"success": False, "error": str(result["errors"])}
                
            return {"success": True, "issue": result["data"]["issueCreate"]["issue"]}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
