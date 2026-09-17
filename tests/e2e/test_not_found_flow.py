from __future__ import annotations

import uuid

from playwright.sync_api import Page, expect


def test_question_with_no_ingested_documents_shows_not_found_state(page: Page, frontend_url: str):
    # Scoped to a freshly created, never-populated set rather than "search
    # everything": the backend fixture is session-scoped and shared with
    # other E2E tests, and the fake embedding client returns an identical
    # vector for every text, so an unscoped query would match documents
    # other tests already uploaded. An empty set guarantees zero chunks
    # regardless of what else has been ingested in this session.
    set_name = f"E2E Empty Set {uuid.uuid4().hex[:8]}"

    page.goto(frontend_url)
    page.get_by_role("textbox", name="New set name").fill(set_name)
    page.get_by_role("button", name="Create set").click()

    page.goto(f"{frontend_url}/chat")
    expect(page.get_by_role("heading", name="Chat")).to_be_visible()

    scope_combobox = page.get_by_role("combobox", name="Ask against")
    scope_combobox.click()
    page.get_by_role("option", name=set_name).click()

    page.get_by_test_id("stChatInput").locator("textarea").fill(
        "What is the meaning of life, the universe, and everything?"
    )
    page.get_by_test_id("stChatInput").locator("textarea").press("Enter")

    expect(page.get_by_text("Not found in the documents.")).to_be_visible(timeout=15000)
