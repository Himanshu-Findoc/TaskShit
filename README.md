# Nexus Task Uploader

A terminal tool that turns your **git commits** (or a **meeting agenda**) into a task, writes the title and description with AI, and uploads it to **Nexus** and the **SharePoint sprint sheet** in one go.

## Features

- Pick a task type. Each one adds its own prefix to the Summary:

  | Type        | Summary prefix  | Commits shown from         |
  |-------------|-----------------|----------------------------|
  | Meeting     | `Meeting-`      | none (you type the agenda) |
  | Web Dev     | `Web Dev-`      | `*_r_fe` repos             |
  | App Dev     | `App Dev-`      | `*_fe` repos (not `_r_fe`) |
  | Backend Dev | `Backend Dev-`  | `*_be` repos               |

- AI (Groq) writes the title and description. You can edit both before uploading.
- Labels are picked from a checklist: feature, bug, improvement, urgent, documentation.
- Sprint is detected from the repo (FinDost Features / FinZoom Live). For meetings, you pick it.
- Upload to **Nexus + Sprint sheet**, **Nexus only**, or **Sprint sheet only**.
- Nexus fields filled: Work Type, Status (Done), Priority, Summary, Description, Assignee, Labels, Start/Due date, Sprint, Reporter.
- Sprint sheet fields filled: Title, Description, Start date & time, Category, Product, Assignee, Estimated hours.

## Requirements

- macOS (the paths in `config.py` assume it)
- Python 3.9+
- [Brave Browser](https://brave.com/) (opens Nexus)
- A Groq API key: https://console.groq.com/keys
- Local clones of the repos listed in `config.py`

## Installation

```bash
cd "/path/to/Nexus Task Uploader"

# 1. Create a virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Install the browsers Playwright uses (Firefox opens the sprint sheet)
python -m playwright install firefox chromium

# 3. Set up your credentials
cp .env.example .env
# then open .env and fill in the values
```

### Environment variables (`.env`)

| Variable              | Required | Purpose                                              |
|-----------------------|----------|------------------------------------------------------|
| `GROQ_API_KEY`        | yes      | AI title/description generation                      |
| `SHAREPOINT_EMAIL`    | yes      | Microsoft login for the sprint sheet                 |
| `SHAREPOINT_PASSWORD` | yes      | Microsoft login for the sprint sheet                 |
| `NEXUS_EMAIL`         | no       | Nexus login (uses the `SHAREPOINT_*` values if empty) |
| `NEXUS_PASSWORD`      | no       | Nexus login (uses the `SHAREPOINT_*` values if empty) |

## Run it from anywhere (global command)

Create a launcher at `~/.local/bin/nexus`. Make sure `~/.local/bin` is on your `PATH`.

```bash
mkdir -p ~/.local/bin
cat > ~/.local/bin/nexus <<'EOF'
#!/bin/zsh
cd "/path/to/Nexus Task Uploader" || exit 1
exec ./venv/bin/python app.py "$@"
EOF
chmod +x ~/.local/bin/nexus
```

Then just type:

```bash
nexus
```

Or run it directly: `./venv/bin/python app.py`

## Usage

1. Choose the **task type** (Meeting / Web Dev / App Dev / Backend Dev).
2. **Meeting:** type the agenda (Esc+Enter to finish). **Dev:** select commits (space to toggle, enter to confirm).
3. Pick the sprint (if asked), labels, and the start/due date (`DD-MM-YYYY`).
4. Choose where to upload. For the sprint sheet, also enter hours and a start time (`H:MM AM/PM`).
5. Review and edit the AI summary and description, then confirm.

The browsers open, fill the forms and submit by themselves. On the first run, log in by hand if asked, and approve Microsoft MFA on your phone (the script waits up to 2 minutes). After that, logins are remembered.

## Configuration (`config.py`)

| Setting               | What it controls                                     |
|-----------------------|------------------------------------------------------|
| `PROJECTS`            | Local repo paths to read commits from                |
| `COMMITS_LIMIT`       | Commits loaded per repo                              |
| `NEXUS_BOARD_URL`     | Nexus board to create tasks on                       |
| `PROJECT_SPRINT_MAP`  | Repo → Nexus sprint                                  |
| `WORK_TYPE`, `STATUS`, `PRIORITY`, `ASSIGNEE`, `REPORTER` | Fixed Nexus form values |
| `CATEGORIES`          | Task types, prefixes and repo filters                |
| `LABEL_OPTIONS`       | Labels shown in the checklist                        |
| `SPRINTSHEET_URL`     | SharePoint sprint sheet form                         |
| `SPRINTSHEET_PROFILE` | Firefox profile that keeps the Microsoft login       |
| `PROJECT_PRODUCT_MAP` | Repo → sprint sheet Product (Findost / Finzoom)      |

## Project structure

```
app.py                  # CLI flow (prompts, orchestration)
ai_service.py           # Groq: title/description for commits & meetings
git_service.py          # Reads commits from local repos
nexus_service.py        # Playwright automation for Nexus (Brave)
sprintsheet_service.py  # Playwright automation for SharePoint (Firefox)
config.py               # All settings
helpers.py              # Commit sorting
.env.example            # Credentials template
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `Executable doesn't exist ... ms-playwright` | `./venv/bin/python -m playwright install firefox chromium` |
| `nexus: command not found` | Open a new terminal or run `rehash`; check that `~/.local/bin` is on your `PATH` |
| Nexus step fails | Check the screenshot in `nexus_error.png`. The Nexus UI may have changed. |
| Sprint sheet form doesn't load | Check `sprintsheet_error.png`. Log in or approve MFA in the Firefox window. |
| Profile already in use | Close any other app using the same Firefox/Brave profile |
| AI fails | Check `GROQ_API_KEY`. The tool falls back to the commit message or agenda. |

## Security

`.env` and the `playwright-*-profile` folders hold credentials and login sessions. **Never commit or share them.**
