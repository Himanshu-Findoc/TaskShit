def sort_commits(all_commits):

    return sorted(
        all_commits,
        key=lambda x: x["datetime"],
        reverse=True
    )