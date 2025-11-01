import re
import requests
import os
import git
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
api_server = os.getenv('WEB_API_SERVER')

# Function to update version in a Python file
def update_version(version_file, new_version):
    with open(version_file, 'r') as file:
        version_content = file.read()

    new_content = re.sub(r'(__version__ = ")(.*)(")', r'\g<1>{}\g<3>'.format(new_version), version_content)

    with open(version_file, 'w') as file:
        file.write(new_content)

# Function to add a new changelog item
def add_changelog_item(version, comment, created_at, commit_id, branch_name):
    payload = {
        "name": "vendingapp",
        "version": version,
        "comment": comment,
        "gitcommit": commit_id,
        "gitbranch": branch_name,
        "created_at": created_at,
    }
    response = requests.post(f'{api_server}/api/changelog/add', json=payload, verify=False)
    if response.status_code == 201:
        print("Changelog item added successfully")
    else:
        print("Failed to add changelog item")
        print(response.json())
        # Stop the script if the API call fails
        exit(1)

if __name__ == "__main__":
    version_file = "__init__.py"
    new_version = input("Enter new version number: ")
    comment = input("Enter changelog comment: ")

    # Get current datetime
    created_at = datetime.now().isoformat()

    # Get current Git commit and branch name
    repo = git.Repo(search_parent_directories=True)
    commit_id = repo.head.object.hexsha
    branch_name = repo.active_branch.name

    add_changelog_item(new_version, comment, created_at, commit_id, branch_name)
    update_version(version_file, new_version)
    print("Version updated successfully!")
