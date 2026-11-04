import os

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from config import (
    NEXUS_BOARD_URL, PROJECT_SPRINT_MAP,
    WORK_TYPE, STATUS, PRIORITY, ASSIGNEE, REPORTER,
)

load_dotenv()

EMAIL    = os.getenv("NEXUS_EMAIL") or os.getenv("SHAREPOINT_EMAIL")
PASSWORD = os.getenv("NEXUS_PASSWORD") or os.getenv("SHAREPOINT_PASSWORD")

BROWSER_PROFILE = "./playwright-nexus-profile"


# =====================================
# HELPERS
# =====================================

def get_sprint(selected_commits):
    for c in selected_commits:
        if c["repo"] in PROJECT_SPRINT_MAP:
            return PROJECT_SPRINT_MAP[c["repo"]]
    return None


def field(modal, label):
    """Form-group div whose label/span starts with `label`."""
    return modal.locator(
        f"xpath=.//div[./label[starts-with(normalize-space(.), '{label}')]"
        f" or ./div/span[starts-with(normalize-space(.), '{label}')]]"
    ).first


def pick_suggestion(page, input_box, name):
    """Type into a search box and click the matching dropdown option."""
    input_box.click()
    input_box.fill("")
    input_box.type(name, delay=60)
    page.wait_for_timeout(1200)

    option = page.locator(
        f"xpath=//*[not(self::input) and not(self::label) and "
        f"normalize-space(text())='{name}']"
    )
    try:
        option.first.wait_for(state="visible", timeout=8000)
        option.first.click()
    except Exception:
        page.keyboard.press("ArrowDown")
        page.keyboard.press("Enter")
    page.wait_for_timeout(500)


def set_status(page, modal):
    """Status is a custom dropdown button (not a <select>). Ensure it shows STATUS."""
    btn = field(modal, "Status").locator("button").first
    if btn.count() == 0:  # fallback: old <select> UI
        field(modal, "Status").locator("select").select_option(label=STATUS)
        return
    if btn.inner_text().strip().lower() == STATUS.lower():
        return  # already Done
    btn.click()
    page.wait_for_timeout(400)
    # Menu items may be div/span/etc. Match any visible element with exact text.
    option = page.get_by_text(STATUS, exact=True).locator("visible=true")
    try:
        option.last.click(timeout=5000)
    except Exception:
        # Fallback: keyboard navigation inside the opened dropdown
        page.keyboard.type(STATUS, delay=50)
        page.keyboard.press("Enter")
    page.wait_for_timeout(300)
    if btn.inner_text().strip().lower() != STATUS.lower():
        print(f"⚠️  Status may not be set (shows '{btn.inner_text().strip()}')")


# =====================================
# LOGIN
# =====================================

def nexus_login(page):
    pwd = page.locator('input[type="password"]')
    if pwd.count() == 0:
        return  # already logged in (profile session)

    print("🔐 Logging in to Nexus...")
    email = page.locator(
        'input[type="email"], input[name*="email" i], input[placeholder*="email" i]'
    ).first
    email.fill(EMAIL)
    pwd.first.fill(PASSWORD)
    pwd.first.press("Enter")

    page.wait_for_url("**/board**", timeout=60000)
    print("✅ Login Success")


# =====================================
# FILL FORM
# =====================================

def fill_form(page, title, description, labels, date_iso, sprint):
    page.get_by_role("button", name="Create").first.click()

    modal = page.locator(
        "xpath=//h2[normalize-space()='Create']/ancestor::div[.//textarea][1]"
    )
    modal.wait_for(state="visible", timeout=15000)

    field(modal, "Work Type").locator("select").select_option(WORK_TYPE)
    set_status(page, modal)
    field(modal, "Priority").locator("select").select_option(PRIORITY)
    print("✅ Work type / Status / Priority set")

    field(modal, "Summary").locator("input").fill(title)
    field(modal, "Description").locator("textarea").fill(description)
    print("✅ Summary & Description filled")

    # Assignee -> "Assign to me"
    modal.get_by_role("button", name="Assign to me").click()
    page.wait_for_timeout(500)
    assignee_input = field(modal, "Assignee").locator("input")
    if ASSIGNEE.lower() not in (assignee_input.input_value() or "").lower():
        pick_suggestion(page, assignee_input, ASSIGNEE)
    print(f"✅ Assignee -> {ASSIGNEE}")

    # Labels
    label_input = field(modal, "Labels").locator("input")
    for lbl in labels:
        label_input.click()
        label_input.type(lbl, delay=40)
        page.wait_for_timeout(400)
        label_input.press("Enter")
        page.wait_for_timeout(300)
    if labels:
        print(f"✅ Labels -> {', '.join(labels)}")

    # Dates (input[type=date] takes YYYY-MM-DD)
    field(modal, "Due date").locator("input").fill(date_iso)
    field(modal, "Start date").locator("input").fill(date_iso)
    print(f"✅ Start/Due date -> {date_iso}")

    if sprint:
        field(modal, "Sprint").locator("select").select_option(label=sprint)
        print(f"✅ Sprint -> {sprint}")

    # Reporter
    pick_suggestion(page, field(modal, "Reporter").locator("input"), REPORTER)
    print(f"✅ Reporter -> {REPORTER}")

    return modal


# =====================================
# MAIN SUBMIT
# =====================================

def submit_task(title, description, selected_commits, labels, date_iso,
                sprint=None) -> bool:
    sprint = sprint or get_sprint(selected_commits)
    success = False

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=BROWSER_PROFILE, headless=False,
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        )
        page = browser.pages[0] if browser.pages else browser.new_page()

        try:
            page.goto(NEXUS_BOARD_URL)
            page.wait_for_load_state("networkidle")
            nexus_login(page)
            if "/board" not in page.url:
                page.goto(NEXUS_BOARD_URL)
            page.get_by_role("button", name="Create").first.wait_for(timeout=30000)

            modal = fill_form(page, title, description, labels, date_iso, sprint)
            page.wait_for_timeout(800)

            # Footer "Create" button (last one inside modal)
            modal.locator("button", has_text="Create").last.click()
            print("🖱  Clicked Create")

            modal.wait_for(state="hidden", timeout=15000)
            print("✅ Task created in Nexus!")
            success = True
            page.wait_for_timeout(1500)

        except Exception as e:
            page.screenshot(path="nexus_error.png")
            print(f"❌ Error: {e}  (screenshot: nexus_error.png)")

        finally:
            browser.close()

    return success
