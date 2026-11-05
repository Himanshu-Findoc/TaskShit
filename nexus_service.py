import os

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from config import (
    HEADLESS,
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
    # Current UI: native <select> with options todo/in_progress/in_review/done/blocked.
    # Locate it by its options rather than the label wrapper, which is unreliable.
    sel = modal.locator("xpath=.//select[option[@value='in_progress'] and option[@value='done']]")
    if sel.count() == 0:
        sel = field(modal, "Status").locator("select")
    if sel.count() > 0:
        s = sel.first
        s.scroll_into_view_if_needed()
        s.select_option(label=STATUS)
        page.wait_for_timeout(300)
        chosen = s.evaluate("e => e.options[e.selectedIndex].text").strip()
        if chosen.lower() != STATUS.lower():
            # React-controlled select ignored it: set via native setter + events
            s.evaluate(
                """(e, label) => {
                    const opt = [...e.options].find(o => o.text.trim().toLowerCase() === label.toLowerCase());
                    const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set;
                    setter.call(e, opt.value);
                    e.dispatchEvent(new Event('input', {bubbles: true}));
                    e.dispatchEvent(new Event('change', {bubbles: true}));
                }""",
                STATUS,
            )
            page.wait_for_timeout(300)
        print(f"   Status → {s.evaluate('e => e.options[e.selectedIndex].text')}")
        return
    btn = field(modal, "Status").locator("button").first
    if btn.inner_text().strip().lower() == STATUS.lower():
        return  # already Done
    btn.click()
    page.wait_for_timeout(400)
    page.locator(
        f"xpath=//*[(self::button or @role='option' or @role='menuitem' or self::li)"
        f" and normalize-space(.)='{STATUS}']"
    ).last.click()
    page.wait_for_timeout(300)


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
            user_data_dir=BROWSER_PROFILE, headless=HEADLESS,
            executable_path="/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
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
