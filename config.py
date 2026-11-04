PROJECTS = [
    "/Users/vishal/Development/finzoom_fe/finzoom_fe",
    "/Users/vishal/Development/finzoom_be/wealth_be",
]

COMMITS_LIMIT = 20

NEXUS_BOARD_URL = (
    "https://nexus.findoc.com/spaces/"
    "f90ad832-3453-4f10-92f4-e7b7882e7b00/board"
)

# repo -> sprint name shown in the Nexus "Sprint" dropdown
PROJECT_SPRINT_MAP = {
    "finzoom_fe":   "FinDost Features",
    "findost_fe":   "FinDost Features",
    "findost_r_fe": "FinDost Features",
    "wealth_r_fe":  "FinZoom Live",
    "wealth_fe":    "FinZoom Live",
}

# Fixed form values
WORK_TYPE = "task"
STATUS    = "Done"   # matched by visible label
PRIORITY  = "medium"
ASSIGNEE  = "Vishal Yadav"
REPORTER  = "Amit Gayar"

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
# Reuses task_updater's Firefox profile so the Microsoft login session carries over
SPRINTSHEET_PROFILE = "/Users/himanshu/Documents/personal projects/task_updater/playwright-firefox-profile"

PROJECT_PRODUCT_MAP = {
    "findost_be":   "Findost",
    "findost_fe":   "Findost",
    "findost_r_fe": "Findost",
    "wealth_r_fe":  "Finzoom",
    "wealth_fe":    "Finzoom",
}
