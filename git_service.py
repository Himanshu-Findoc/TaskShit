import os
from datetime import datetime
from git import Repo

def get_commits(repo_path, limit=10):

    repo = Repo(repo_path)

    branch = repo.active_branch.name

    commits = []

    for commit in repo.iter_commits(
        branch,
        max_count=limit
    ):

        commit_date = datetime.fromtimestamp(
            commit.committed_date
        )

        commits.append({
            "repo": os.path.basename(repo_path),
            "message": commit.message.strip(),
            "hash": commit.hexsha[:7],
            "date": commit_date.strftime(
                "%d %b %Y %I:%M %p"
            ),
            "datetime": commit_date
        })

    return commits