from __future__ import annotations

import uuid

from playwright.sync_api import Page, expect


def test_upload_flow_creates_set_and_shows_ready_document(page: Page, frontend_url: str):
    set_name = f"E2E Set {uuid.uuid4().hex[:8]}"

    page.goto(frontend_url)
    expect(page.get_by_role("heading", name="Sets & Documents")).to_be_visible()

    page.get_by_role("textbox", name="New set name").fill(set_name)
    page.get_by_role("button", name="Create set").click()

    # Selecting the newly created set.
    combobox = page.get_by_role("combobox", name="Select a set")
    combobox.click()
    page.get_by_role("option", name=set_name).click()

    # Native file input, hidden behind Streamlit's dropzone UI.
    page.locator('input[type="file"]').set_input_files(
        files=[
            {
                "name": "note.txt",
                "mimeType": "text/plain",
                "buffer": b"E2E test document content.",
            }
        ]
    )
    page.get_by_role("button", name="Upload").click()

    expect(page.get_by_text("note.txt")).to_be_visible(timeout=15000)
    expect(page.get_by_text("ready")).to_be_visible(timeout=15000)


def test_remove_document_removes_it_from_the_list(page: Page, frontend_url: str):
    set_name = f"E2E Removal Set {uuid.uuid4().hex[:8]}"

    page.goto(frontend_url)
    page.get_by_role("textbox", name="New set name").fill(set_name)
    page.get_by_role("button", name="Create set").click()

    combobox = page.get_by_role("combobox", name="Select a set")
    combobox.click()
    page.get_by_role("option", name=set_name).click()

    page.locator('input[type="file"]').set_input_files(
        files=[{"name": "temp.txt", "mimeType": "text/plain", "buffer": b"Temporary content."}]
    )
    page.get_by_role("button", name="Upload").click()
    expect(page.get_by_text("temp.txt")).to_be_visible(timeout=15000)

    page.get_by_role("button", name="Remove").click()
    expect(page.get_by_text("temp.txt")).not_to_be_visible(timeout=15000)
