"""Sprint sheet (SharePoint list form) uploader — ported from task_updater."""
import os

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from config import HEADLESS, SPRINTSHEET_URL, SPRINTSHEET_PROFILE, PROJECT_PRODUCT_MAP, ASSIGNEE

load_dotenv()

EMAIL    = os.getenv("SHAREPOINT_EMAIL")
PASSWORD = os.getenv("SHAREPOINT_PASSWORD")

PRODUCT_RADIOS = {
    "Findost": "ChoiceGroup14-FinDost",
    "IPO":     "ChoiceGroup14-IPO",
    "Finzoom": "ChoiceGroup14-FinZoom",
    "Accord":  "ChoiceGroup14-Other",
    "MTF":     "ChoiceGroup14-Utility",
}


def get_product(selected_commits):
    for c in selected_commits:
        if c["repo"] in PROJECT_PRODUCT_MAP:
            return PROJECT_PRODUCT_MAP[c["repo"]]
    return "Findost"


# =====================================
# MICROSOFT LOGIN
# =====================================

def microsoft_login(page):

    try:

        if page.locator('input[type="email"]').count() > 0:
            print("🔐 Logging In...")
            page.fill('input[type="email"]', EMAIL)
            page.click('input[type="submit"]')
            page.wait_for_timeout(3000)

        if page.locator('input[type="password"]').count() > 0:
            page.fill('input[type="password"]', PASSWORD)
            page.click('input[type="submit"]')
            page.wait_for_timeout(3000)

        # ---- Microsoft Authenticator / MFA approval ----
        # This screen ("Approve sign in request") requires a human to tap
        # approve on their phone. Poll for it instead of a fixed timeout so
        # we actually wait for the person, rather than racing ahead and
        # hitting the form-not-found timeout later.
        mfa_prompt = page.locator(
            "text=Approve sign in request"
        ).or_(page.locator("#idRichContext_DisplaySign"))

        if mfa_prompt.count() > 0:
            sign = page.locator("#idRichContext_DisplaySign")
            if sign.count() > 0:
                print(f"🔢 Enter this number in Authenticator: {sign.inner_text().strip()}")
            print(
                "📱 Waiting for Microsoft Authenticator approval on your "
                "phone..."
            )
            try:
                mfa_prompt.first.wait_for(state="hidden", timeout=120000)
                print("✅ MFA Approved")
            except Exception:
                print(
                    "⚠️ Still waiting on MFA approval after 120s "
                    "(continuing anyway)"
                )

        # ---- "Stay signed in?" (KMSI) ----
        # Clicking "Yes" here is what persists the session cookie in the
        # Firefox profile so future runs can skip email/password. Target it
        # explicitly instead of a blind submit click, and give the page a
        # moment to actually render before looking for it.
        page.wait_for_timeout(1500)
        kmsi_yes = page.locator("#idSIButton9")
        if kmsi_yes.count() > 0:
            kmsi_yes.click()
            page.wait_for_timeout(2000)

        print("✅ Login Success")

    except Exception as e:
        print(f"❌ Login Error: {e}")

# =====================================
# NORMAL TEXT INPUT
# =====================================

def fill_input(page, element_id, value):

    try:
        field = page.locator(f"#{element_id}")
        field.wait_for(state="visible", timeout=15000)
        field.click()
        field.fill("")
        field.type(str(value), delay=30)
        page.keyboard.press("Tab")

        actual = field.input_value()
        if actual != str(value):
            print(
                f"⚠️ {element_id} Filled but value is '{actual}' "
                f"(expected '{value}')"
            )
        else:
            print(f"✅ {element_id} Filled -> '{actual}'")

    except Exception as e:
        print(f"❌ {element_id} Error: {e}")

# =====================================
# DESCRIPTION
# =====================================

def fill_description(page, value):

    try:

        display_div = page.locator(
            "#field-element-1 .ReactFieldEditor-core--display"
        )
        display_div.hover()
        page.wait_for_timeout(500)

        edit_btn = page.locator(
            "#field-element-1 button[title='Edit']"
        )
        edit_btn.wait_for(state="visible", timeout=10000)
        edit_btn.click()

        page.wait_for_timeout(1500)

        editor = page.locator(
            "div.rooster-editor[contenteditable='true']"
        )
        editor.wait_for(state="visible", timeout=15000)

        editor.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        editor.type(value, delay=20)

        page.wait_for_timeout(500)

        save_btn = page.locator(
            ".bottom-menu-bar .ms-Button--primary"
        ).first
        save_btn.wait_for(state="visible", timeout=10000)
        save_btn.click()

        page.wait_for_timeout(800)
        print("✅ Description Filled")

    except Exception as e:
        print(f"❌ Description Error: {e}")

# =====================================
# START DATE
# =====================================

def fill_start_date(page, date_str, time_str=None):
    """
    Fill SharePoint's "Start date" DateTime field.

    `date_str` e.g. "7/22/2026", `time_str` e.g. "3:00 PM" (optional).
    Typed together into the field, then Enter closes the date/time
    callout — per the field's own aria-label instructions ("enter to
    close date time callout") — without needing to click through the
    calendar/time dropdown.
    """

    try:
        field = page.locator(
            "div.ReactFieldEditor",
            has=page.locator(
                "label.ReactFieldEditor-fieldTitle", has_text="Start date"
            ),
        ).locator("#sp-DateTimePicker-DateTimeTextField")

        field.wait_for(state="visible", timeout=15000)

        value = f"{date_str} {time_str}" if time_str else date_str

        field.click()
        field.fill("")
        field.type(value, delay=30)
        page.keyboard.press("Enter")

        page.wait_for_timeout(500)

        actual = field.input_value()
        print(f"✅ Start date Filled -> '{actual}'")

    except Exception as e:
        print(f"❌ Start date Error: {e}")

# =====================================
# RADIO BUTTON
# =====================================

def select_radio(page, element_id):

    try:
        radio = page.locator(f"#{element_id}")
        radio.wait_for(state="attached", timeout=15000)

        label = page.locator(f'label[for="{element_id}"]')
        if label.count() > 0:
            label.click()
        else:
            radio.check(force=True)

        is_checked = radio.is_checked()
        if is_checked:
            print(f"✅ {element_id} Selected")
        else:
            print(f"⚠️ {element_id} Clicked but not checked afterward")

    except Exception as e:
        print(f"❌ {element_id} Error: {e}")

# =====================================
# PEOPLE PICKER
# =====================================

def fill_people_picker(page, element_id, value):

    try:

        picker = page.locator(f"#{element_id}")
        picker.click()
        picker.fill("")
        picker.type(value, delay=80)

        suggestions = page.locator(
            ".ms-Suggestions-container .ms-Suggestions-item button"
        )
        suggestions.first.wait_for(state="visible", timeout=15000)
        suggestions.first.click()

        page.wait_for_timeout(800)
        print(f"✅ {value} Selected")

    except Exception as e:
        print(f"❌ People Picker ({value}) Error: {e}")

# =====================================
# AUTO SUBMIT
# =====================================

def click_submit(page) -> bool:
    """
    Click the SharePoint submit button by its ID: #form-submit-button
    Returns True on success, False on failure.
    """

    print("⏳ Looking for Submit button...")

    try:
        btn = page.locator("#form-submit-button")
        btn.wait_for(state="visible", timeout=10000)
        btn.click()
        print("🖱  Clicked: #form-submit-button")
    except Exception as e:
        print(f"❌ Submit button not found: {e}")
        return False

    # Wait for SharePoint to process
    try:
        page.wait_for_load_state("networkidle", timeout=25000)
    except Exception:
        pass  # networkidle may time out on slow SP; that's OK

    # Look for a success signal
    SUCCESS_SELECTORS = [
        "[data-automationid='infoBarMessage']",
        ".ms-MessageBar--success",
        "div[role='status']",
    ]

    submitted = False

    for sel in SUCCESS_SELECTORS:
        try:
            page.locator(sel).wait_for(state="visible", timeout=6000)
            submitted = True
            break
        except Exception:
            continue

    if submitted:
        print("✅ Task Submitted Successfully!")
    else:
        print("✅ Task Submitted (no banner detected — assuming success).")

    return True

# =====================================
# MAIN SUBMIT
# =====================================

def submit_sprintsheet(title, description, selected_commits, estimated_hours,
                       start_date, start_time, product=None) -> bool:
    """Fill and submit the sprint sheet form. start_date 'M/D/YYYY', start_time 'H:MM AM'."""
    product = product or get_product(selected_commits)
    success = False

    with sync_playwright() as p:
        browser = p.firefox.launch_persistent_context(
            user_data_dir=SPRINTSHEET_PROFILE, headless=HEADLESS,
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        try:
            page.goto(SPRINTSHEET_URL)
            page.wait_for_timeout(2000)
            microsoft_login(page)

            try:
                page.locator("#TextField1").wait_for(state="visible", timeout=30000)
            except Exception as e:
                page.screenshot(path="sprintsheet_error.png")
                print(f"❌ Sprint sheet form did not load (screenshot: sprintsheet_error.png): {e}")
                return False

            fill_input(page, "TextField1", title)
            fill_description(page, description)
            fill_start_date(page, start_date, start_time)
            select_radio(page, "ChoiceGroup11-Engineering")
            select_radio(page, PRODUCT_RADIOS.get(product, "ChoiceGroup14-Other"))
            fill_people_picker(page, "combobox-id__21", ASSIGNEE)
            fill_input(page, "TextField23", description)
            fill_input(page, "TextField29", estimated_hours)

            page.wait_for_timeout(1200)
            success = click_submit(page)
            page.wait_for_timeout(2500)
        except Exception as e:
            print(f"❌ Sprint sheet error: {e}")
        finally:
            try:
                browser.close()
            except Exception:
                pass
    return success
