import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8000"


@pytest.fixture(autouse=True)
def reset_todos():
    """각 테스트 전후 todo 데이터 초기화"""
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from main import save_todos
    save_todos([])
    yield
    save_todos([])


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def add_todo(page: Page, title: str, description: str, priority: str = "medium", category: str = "general", due_date: str = ""):
    """할일 추가 후 네트워크 응답 및 렌더링까지 대기"""
    page.fill("#title", title)
    page.fill("#description", description)
    page.select_option("#priority", priority)
    page.fill("#category", category)
    if due_date:
        page.evaluate(f"document.getElementById('due-date').value = '{due_date}'")
    with page.expect_response(lambda r: r.url.endswith("/todos") and r.request.method == "POST"):
        page.click("button[type=submit]")
    # fetchTodos() 재호출 후 렌더링 대기
    page.wait_for_function("document.querySelectorAll('.todo-item').length > 0")


# ── TC-01: 페이지 로드 ─────────────────────────────────────────────────────────

def test_TC01_page_load(page: Page):
    """TC-01: 메인 페이지가 정상적으로 로드되는지 확인"""
    page.goto(BASE_URL)
    expect(page).to_have_title("Modern To-Do | Stay Organized")
    expect(page.locator("h1")).to_have_text("My Tasks")
    expect(page.locator("#todo-form")).to_be_visible()


# ── TC-02: 할일 추가 ──────────────────────────────────────────────────────────

def test_TC02_add_todo(page: Page):
    """TC-02: 새 할일 항목이 정상적으로 추가되는지 확인"""
    page.goto(BASE_URL)
    add_todo(page, "플레이라이트 테스트", "UI 자동화 테스트입니다", "high", "테스트")
    todo_items = page.locator(".todo-item")
    expect(todo_items).to_have_count(1)
    expect(todo_items.first.locator(".todo-title")).to_have_text("플레이라이트 테스트")
    expect(todo_items.first.locator(".todo-description")).to_have_text("UI 자동화 테스트입니다")
    expect(todo_items.first.locator(".badge-high")).to_be_visible()


# ── TC-03: 여러 할일 추가 ─────────────────────────────────────────────────────

def test_TC03_add_multiple_todos(page: Page):
    """TC-03: 여러 개의 할일 항목이 누적 추가되는지 확인"""
    page.goto(BASE_URL)
    add_todo(page, "첫 번째 할일", "첫 번째 설명")
    add_todo(page, "두 번째 할일", "두 번째 설명")
    add_todo(page, "세 번째 할일", "세 번째 설명")
    page.wait_for_function("document.querySelectorAll('.todo-item').length === 3")
    expect(page.locator(".todo-item")).to_have_count(3)


# ── TC-04: 완료 토글 ──────────────────────────────────────────────────────────

def test_TC04_toggle_complete(page: Page):
    """TC-04: 체크박스 클릭 시 완료 상태로 전환되는지 확인"""
    page.goto(BASE_URL)
    add_todo(page, "완료 테스트", "완료 처리할 항목")
    checkbox = page.locator(".todo-checkbox").first
    with page.expect_response(lambda r: "/todos/" in r.url and r.request.method == "PUT"):
        checkbox.click()
    page.wait_for_function("document.querySelector('.todo-item.completed') !== null")
    expect(page.locator(".todo-item.completed")).to_have_count(1)


# ── TC-05: 편집 모달 열기 ─────────────────────────────────────────────────────

def test_TC05_open_edit_modal(page: Page):
    """TC-05: 편집 버튼 클릭 시 모달이 열리는지 확인"""
    page.goto(BASE_URL)
    add_todo(page, "편집 테스트", "편집할 항목")
    # 편집 버튼: todo-actions 안의 첫 번째 btn-icon
    page.locator(".todo-actions .btn-icon").first.click()
    expect(page.locator("#edit-modal")).to_be_visible()
    expect(page.locator("#edit-title")).to_have_value("편집 테스트")
    expect(page.locator("#edit-description")).to_have_value("편집할 항목")


# ── TC-06: 할일 수정 ──────────────────────────────────────────────────────────

def test_TC06_edit_todo(page: Page):
    """TC-06: 할일 제목과 설명이 정상적으로 수정되는지 확인"""
    page.goto(BASE_URL)
    add_todo(page, "수정 전 제목", "수정 전 설명")
    page.locator(".todo-actions .btn-icon").first.click()
    page.wait_for_selector("#edit-modal", state="visible")
    page.fill("#edit-title", "수정 후 제목")
    page.fill("#edit-description", "수정 후 설명")
    with page.expect_response(lambda r: "/todos/" in r.url and r.request.method == "PUT"):
        page.click("#edit-form button[type=submit]")
    page.wait_for_function("document.querySelector('.todo-title').textContent.includes('수정 후 제목')")
    expect(page.locator(".todo-title").first).to_have_text("수정 후 제목")
    expect(page.locator(".todo-description").first).to_have_text("수정 후 설명")


# ── TC-07: 모달 닫기 ──────────────────────────────────────────────────────────

def test_TC07_close_modal(page: Page):
    """TC-07: 모달 닫기 버튼 클릭 시 모달이 닫히는지 확인"""
    page.goto(BASE_URL)
    add_todo(page, "모달 닫기 테스트", "테스트 설명")
    page.locator(".todo-actions .btn-icon").first.click()
    expect(page.locator("#edit-modal")).to_be_visible()
    # 모달 헤더의 X 버튼 (onclick="closeModal()")
    page.locator(".modal-header .btn-icon").click()
    page.wait_for_function("document.getElementById('edit-modal').style.display === 'none'")
    expect(page.locator("#edit-modal")).to_be_hidden()


# ── TC-08: 할일 삭제 ──────────────────────────────────────────────────────────

def test_TC08_delete_todo(page: Page):
    """TC-08: 삭제 버튼 클릭 후 확인 시 항목이 삭제되는지 확인"""
    page.goto(BASE_URL)
    add_todo(page, "삭제 테스트", "삭제할 항목")
    expect(page.locator(".todo-item")).to_have_count(1)
    page.on("dialog", lambda d: d.accept())
    with page.expect_response(lambda r: "/todos/" in r.url and r.request.method == "DELETE"):
        page.locator(".btn-danger").first.click()
    page.wait_for_function("document.querySelectorAll('.todo-item').length === 0")
    expect(page.locator(".todo-item")).to_have_count(0)


# ── TC-09: 삭제 취소 ──────────────────────────────────────────────────────────

def test_TC09_delete_cancel(page: Page):
    """TC-09: 삭제 확인창에서 취소 시 항목이 유지되는지 확인"""
    page.goto(BASE_URL)
    add_todo(page, "삭제 취소 테스트", "삭제하지 않을 항목")
    page.on("dialog", lambda d: d.dismiss())
    page.locator(".btn-danger").first.click()
    page.wait_for_timeout(1000)
    expect(page.locator(".todo-item")).to_have_count(1)


# ── TC-10: 빈 입력 방지 ───────────────────────────────────────────────────────

def test_TC10_empty_input_validation(page: Page):
    """TC-10: 제목 미입력 시 폼이 제출되지 않는지 확인"""
    page.goto(BASE_URL)
    page.click("button[type=submit]")
    page.wait_for_timeout(500)
    expect(page.locator(".todo-item")).to_have_count(0)


# ── TC-11: 마감일 추가 ────────────────────────────────────────────────────────

def test_TC11_add_todo_with_due_date(page: Page):
    """TC-11: 마감일이 설정된 할일이 정상적으로 추가되는지 확인"""
    page.goto(BASE_URL)
    add_todo(page, "마감일 테스트", "기한 있는 항목", due_date="2099-12-31")
    expect(page.locator(".badge-due")).to_be_visible()
    expect(page.locator(".badge-due")).to_contain_text("2099-12-31")


# ── TC-12: 마감일 초과 표시 ───────────────────────────────────────────────────

def test_TC12_overdue_highlight(page: Page):
    """TC-12: 마감일이 지난 항목에 overdue 스타일이 적용되는지 확인"""
    page.goto(BASE_URL)
    add_todo(page, "기한 초과 테스트", "이미 지난 항목", due_date="2000-01-01")
    expect(page.locator(".badge-due.overdue")).to_be_visible()


# ── TC-13: 마감일 수정 ────────────────────────────────────────────────────────

def test_TC13_edit_due_date(page: Page):
    """TC-13: 편집 모달에서 마감일이 수정되는지 확인"""
    page.goto(BASE_URL)
    add_todo(page, "마감일 수정 테스트", "수정할 항목", due_date="2099-06-01")
    page.locator(".todo-actions .btn-icon").first.click()
    page.wait_for_selector("#edit-modal", state="visible")
    expect(page.locator("#edit-due-date")).to_have_value("2099-06-01")
    page.evaluate("document.getElementById('edit-due-date').value = '2099-12-31'")
    with page.expect_response(lambda r: "/todos/" in r.url and r.request.method == "PUT"):
        page.click("#edit-form button[type=submit]")
    page.wait_for_function("document.querySelector('.badge-due').textContent.includes('2099-12-31')")
    expect(page.locator(".badge-due")).to_contain_text("2099-12-31")
