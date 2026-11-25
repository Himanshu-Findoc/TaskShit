import os

PROJECTS = [
    "/Users/himanshu/Documents/Findost/findost_be",
    "/Users/himanshu/Documents/Findost/findost_fe",
    "/Users/himanshu/Documents/Findost/findost_r_fe",
    "/Users/himanshu/Documents/Findost/wealth_r_fe",
    "/Users/himanshu/Documents/Findost/wealth_fe",
]

COMMITS_LIMIT = 10

NEXUS_BOARD_URL = (
    "https://nexus.findoc.com/spaces/"
    "6e7ee940-118e-4a8c-b83c-b73c98194303/board"
)

# repo -> sprint name shown in the Nexus "Sprint" dropdown
PROJECT_SPRINT_MAP = {
    "findost_be":   "FinDost Features",
    "findost_fe":   "FinDost Features",
    "findost_r_fe": "FinDost Features",
    "wealth_r_fe":  "FinZoom Live",
    "wealth_fe":    "FinZoom Live",
}

# Fixed form values
WORK_TYPE = "task"
STATUS    = "Done"   # matched by visible label
PRIORITY  = "medium"
ASSIGNEE  = "Himanshu Swami"
REPORTER  = "Vishal Yadav"

# Task category -> (summary prefix, repo-name filter)
CATEGORIES = {
    "Meeting":     ("Meeting-",     None),
    "Web Dev":     ("Web Dev-",     lambda r: r.endswith("_r_fe")),
    "App Dev":     ("App Dev-",     lambda r: r.endswith("_fe") and not r.endswith("_r_fe")),
    "Backend Dev": ("Backend Dev-", lambda r: r.endswith("_be")),
}

LABEL_OPTIONS = ["feature", "bug", "improvement", "urgent", "documentation"]

# ---- Sprint sheet (SharePoint list form) ----
SPRINTSHEET_URL = (
    "https://findocm365.sharepoint.com/sites/devretail/_layouts/15/listforms.aspx?cid=MWNkYTJkNWYtZDliYi00ZmY5LWFmMjgtNWU5MTc3NDU4NjVk&ct=1784550481857&or=Teams-HL&nav=YzQ3Mjc4ZDMtMzdiNy00YmFlLWExY2QtMGFkOGQ2MTYyODBj&LOF=1"
)
# Brave profile (inside this project) that keeps the Microsoft login session
SPRINTSHEET_PROFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playwright-sprint-profile")

# Browser used for both Nexus and the sprint sheet
BRAVE_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

PROJECT_PRODUCT_MAP = {
    "findost_be":   "Findost",
    "findost_fe":   "Findost",
    "findost_r_fe": "Findost",
    "wealth_r_fe":  "Finzoom",
    "wealth_fe":    "Finzoom",
}

# Run browsers in the background (set False to watch / for first-time login)
HEADLESS = False
