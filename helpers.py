def sort_commits(all_commits):

    return sorted(
        all_commits,
        key=lambda x: x["datetime"],
        reverse=True
    )

def close_browser(browser, profile_dir):
    """Close every tab, close the browser, then wipe the saved tab session
    so the next launch starts with a single fresh tab (logins/cookies kept)."""
    import os
    import shutil

    try:
        for page in list(browser.pages):
            try:
                page.close()
            except Exception:
                pass
        browser.close()
    except Exception:
        pass

    default = os.path.join(profile_dir, "Default")
    for name in ("Sessions", "Sessions_Encrypted"):
        shutil.rmtree(os.path.join(default, name), ignore_errors=True)
    for name in ("Current Session", "Current Tabs", "Last Session", "Last Tabs"):
        try:
            os.remove(os.path.join(default, name))
        except OSError:
            pass
