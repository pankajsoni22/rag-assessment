from __future__ import annotations

import uuid

from playwright.sync_api import Page, expect


def test_qa_flow_returns_grounded_answer_with_citations(page: Page, frontend_url: str):
    set_name = f"E2E QA Set {uuid.uuid4().hex[:8]}"

    page.goto(f"{frontend_url}/sets")
    page.get_by_role("textbox", name="New set name").fill(set_name)
    page.get_by_role("button", name="Create set").click()

    combobox = page.get_by_role("combobox", name="Select a set")
    combobox.click()
    page.get_by_role("option", name=set_name).click()

    page.locator('input[type="file"]').set_input_files(
        files=[
            {"name": "answer.txt", "mimeType": "text/plain", "buffer": b"The answer is 42."}
        ]
    )
    page.get_by_role("button", name="Upload").click()
    expect(page.get_by_text("ready")).to_be_visible(timeout=15000)

    page.goto(f"{frontend_url}/chat")
    expect(page.get_by_role("heading", name="Chat")).to_be_visible()

    # Scoped to this test's own set: the backend fixture is session-scoped
    # and shared with other E2E tests, and the fake embedding client returns
    # an identical vector for every text, so an unscoped query's top-k
    # results aren't guaranteed to include this test's own chunk once other
    # tests have populated the shared store.
    scope_combobox = page.get_by_role("combobox", name="Ask against")
    scope_combobox.click()
    page.get_by_role("option", name=set_name).click()

    page.get_by_test_id("stChatInput").locator("textarea").fill("What is the answer?")
    page.get_by_test_id("stChatInput").locator("textarea").press("Enter")

    expect(page.get_by_text("This is a fake grounded answer")).to_be_visible(timeout=15000)
    expect(page.get_by_text("Sources:")).to_be_visible(timeout=15000)
    expect(page.get_by_text("answer.txt")).to_be_visible(timeout=15000)
