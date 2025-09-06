# delete_chatroll_messages.py
import os
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

load_dotenv()

CHATROLL_USER = os.getenv('CHATROLL_USERNAME', 'DSI')
CHATROLL_PASS = os.getenv('CHATROLL_PASSWORD', 'Stat3908@')
CHATROLL_ROOM_URLS = [
    os.getenv('CHATROLL_ROOM1_URL', 'https://chatroll.com/7mll'),
    os.getenv('CHATROLL_ROOM2_URL', 'https://chatroll.com/3bt8')
]

# ===== 調整ポイント（あなたの環境に合わせて変更） =====
SELECTORS = {
    # ログイン関連（実際のChatrollサインインページに合わせて調整済み）
    "login_username": '#login-username, input[name="email"]',
    "login_password": '#passwordInput',
    "login_submit":  'button[type="submit"]',

    # ルーム内のメッセージ行（1件ずつの親要素）
    "message_row":    '.message, .chat-message, div[data-message-id]',

    # メッセージの「削除」アクション：
    # 1) 三点メニュー → Delete をクリックするタイプ
    "message_menu_btn": 'button[aria-label="More"], .menu-button, .more-btn, button:has-text("...")',
    "message_delete_cmd": 'text=Delete, .menu-item-delete',

    # 2) 直接「×」「ゴミ箱」アイコンがあるタイプ（実際のChatroll構造に合わせて修正）
    "message_direct_delete": '.button-delete, .message-delete-button img, .message-delete-button .clickable',

    # 確認ダイアログ（モーダル）での「OK」ボタン
    "confirm_delete_btn": 'button:has-text("OK"), button:has-text("ＯＫ"), button:has-text("はい"), .confirm-delete',
    
    # チャットリストのスクロールコンテナ
    "scroll_container": '.messages, .chat-messages, .scroll-container',
}

# ===== オプション設定 =====
MAX_BATCH_DELETE = 999999     # 全メッセージを削除（実質無制限）
SCROLL_BATCHES = 20             # 何回スクロールして古いログを読み込むか
SCROLL_PAUSE_SEC = 0.5          # スクロール後の待機
CLICK_PAUSE_SEC = 0.15          # クリック間の待機
WAIT_AFTER_DELETE_SEC = 0.05    # 削除反映待ち
GLOBAL_TIMEOUT = 15000          # 各操作のタイムアウト(ms)

def safe_click(page, selector, timeout=GLOBAL_TIMEOUT, strict=False):
    try:
        loc = page.locator(selector)
        if strict:
            loc = loc.first
        loc.wait_for(state="visible", timeout=timeout)
        loc.click()
        time.sleep(CLICK_PAUSE_SEC)
        return True
    except PlaywrightTimeoutError:
        return False
    except Exception:
        return False

def try_delete_message(page, message_element):
    """1件のメッセージを削除する。成功したらTrue"""
    print(f"  Attempting to delete message...")
    
    # まずホバーして削除ボタンを表示
    try:
        print("    Hovering to show delete button...")
        message_element.hover()
        time.sleep(0.2)  # ホバー後の待機
        
        # 削除ボタンを探す
        direct_delete_count = message_element.locator('.button-delete').count()
        print(f"    Delete buttons found after hover: {direct_delete_count}")
        
        if direct_delete_count > 0:
            print("    Clicking delete button...")
            delete_btn = message_element.locator('.button-delete').first
            delete_btn.click()
            time.sleep(CLICK_PAUSE_SEC)
            
            # 確認ダイアログをチェック（小さいウィンドウのOKボタン）
            time.sleep(0.3)  # ダイアログ表示待ち
            confirm_count = page.locator(SELECTORS["confirm_delete_btn"]).count()
            print(f"    Confirm dialog OK buttons found: {confirm_count}")
            
            if confirm_count > 0:
                print("    Clicking OK button in confirmation dialog...")
                page.locator(SELECTORS["confirm_delete_btn"]).first.click()
                time.sleep(WAIT_AFTER_DELETE_SEC)
                print("    Delete completed successfully!")
                return True
            else:
                # より広範囲でOKボタンを探す
                ok_buttons = page.locator('button:text-is("OK"), button:text-is("ＯＫ"), input[value="OK"]')
                ok_count = ok_buttons.count()
                print(f"    Alternative OK buttons found: {ok_count}")
                
                if ok_count > 0:
                    print("    Clicking alternative OK button...")
                    ok_buttons.first.click()
                    time.sleep(WAIT_AFTER_DELETE_SEC)
                    print("    Delete completed successfully!")
                    return True
                else:
                    print("    No OK button found - delete may have completed immediately")
                    time.sleep(WAIT_AFTER_DELETE_SEC)
                    return True
        else:
            print("    No delete button found after hover")
            return False
            
    except Exception as e:
        print(f"    Delete failed: {e}")
        return False

def scroll_load_older(page):
    """古いメッセージを読み込むためにスクロール"""
    try:
        if page.locator(SELECTORS["scroll_container"]).count() > 0:
            sc = page.locator(SELECTORS["scroll_container"]).first
            page.evaluate("(el) => el.scrollTop = 0", sc)  # 上方向読み込み型なら0へ
            time.sleep(SCROLL_PAUSE_SEC)
        else:
            # 画面全体をスクロール（フォールバック）
            page.mouse.wheel(0, -2000)
            time.sleep(SCROLL_PAUSE_SEC)
    except Exception:
        pass

def login_if_needed(page):
    """ログインページが出た場合のみログインを試みる"""
    try:
        username_count = page.locator(SELECTORS["login_username"]).count()
        print(f"Username fields found: {username_count}")
        
        if username_count > 0:
            print("Attempting login...")
            page.fill(SELECTORS["login_username"], CHATROLL_USER)
            page.fill(SELECTORS["login_password"], CHATROLL_PASS)
            safe_click(page, SELECTORS["login_submit"])
            
            # より柔軟な待機処理に変更
            try:
                page.wait_for_load_state("domcontentloaded", timeout=5000)
                time.sleep(1)  # 短縮
                print(f"Login completed. Final URL: {page.url}")
            except:
                # ネットワークアイドルでタイムアウトしても続行
                print(f"Login may still be loading, but proceeding. Current URL: {page.url}")
                time.sleep(1)  # 短縮
        else:
            print("No login form detected - checking for Login button...")
            # より広範囲でログインボタンを探す
            login_selectors = [
                'a:has-text("Log in")',        # 実際に見つかったリンク
                'button:has-text("Login")', 
                'a:has-text("Login")', 
                '.login-btn',
                '[data-testid*="login"]',
                'button:has-text("Sign in")',
                'a:has-text("Sign in")',
                'button[class*="login"]',
                'a[class*="login"]'
            ]
            
            login_found = False
            for selector in login_selectors:
                login_btns = page.locator(selector)
                count = login_btns.count()
                print(f"Checking selector '{selector}': found {count}")
                if count > 0:
                    print(f"Found Login button with selector '{selector}', clicking...")
                    login_btns.first.click()
                    login_found = True
                    time.sleep(2)
                    break
            
            if not login_found:
                print("No Login button found. Page title:", page.title())
                print("Current URL:", page.url)
                # ページの構造を確認
                all_buttons = page.locator('button, a[href*="login"], a[href*="signin"]')
                count = all_buttons.count()
                print(f"Total buttons and login links found: {count}")
                
                # 実際のボタンテキストを確認
                for i in range(count):
                    btn = all_buttons.nth(i)
                    text = btn.text_content().strip()
                    href = btn.get_attribute('href') if btn.get_attribute('href') else 'N/A'
                    print(f"Button {i}: text='{text}', href='{href}'")
                
                # すべてのボタンも確認
                all_btns = page.locator('button')
                btn_count = all_btns.count()
                print(f"All buttons on page: {btn_count}")
                for i in range(min(btn_count, 10)):  # 最初の10個まで
                    btn = all_btns.nth(i)
                    text = btn.text_content().strip()
                    print(f"  Button {i}: '{text}'")
            
            # ログインページに移動後、再度フォームを探す
            username_count = page.locator(SELECTORS["login_username"]).count()
            print(f"After navigation - Username fields found: {username_count}")
            print(f"Current URL after login click: {page.url}")
            
            if username_count > 0:
                print("Login form now available, filling credentials...")
                page.fill(SELECTORS["login_username"], CHATROLL_USER)
                page.fill(SELECTORS["login_password"], CHATROLL_PASS)
                safe_click(page, SELECTORS["login_submit"])
                page.wait_for_load_state("domcontentloaded", timeout=10000)
                time.sleep(3)
                print(f"ログイン完了後のURL: {page.url}")
                print(f"Login submitted. Final URL: {page.url}")
            else:
                print("Still no login form found after clicking Log in link")
                # サインインページで実際のフォーム要素を探す
                print("Searching for actual form elements on signin page...")
                
                # より幅広いセレクタで入力フィールドを探す
                input_fields = page.locator('input')
                input_count = input_fields.count()
                print(f"Total input fields found: {input_count}")
                
                for i in range(min(input_count, 10)):
                    field = input_fields.nth(i)
                    input_type = field.get_attribute('type') or 'text'
                    name = field.get_attribute('name') or 'N/A'
                    id_attr = field.get_attribute('id') or 'N/A'
                    placeholder = field.get_attribute('placeholder') or 'N/A'
                    print(f"  Input {i}: type='{input_type}', name='{name}', id='{id_attr}', placeholder='{placeholder}'")
                
                # ボタンも確認
                buttons = page.locator('button, input[type="submit"]')
                btn_count = buttons.count()
                print(f"Submit buttons found: {btn_count}")
                
                for i in range(min(btn_count, 5)):
                    btn = buttons.nth(i)
                    text = btn.text_content().strip()
                    btn_type = btn.get_attribute('type') or 'N/A'
                    print(f"  Button {i}: text='{text}', type='{btn_type}'")
                
                # 実際のフォーム要素でログインを試行
                print("Attempting login with actual form elements...")
                try:
                    page.fill('#login-username', CHATROLL_USER)
                    page.fill('#passwordInput', CHATROLL_PASS)
                    page.click('button[type="submit"]')
                    page.wait_for_load_state("domcontentloaded", timeout=10000)
                    time.sleep(3)
                    print(f"ログイン試行完了後のURL: {page.url}")
                    print(f"Login attempted. Current URL: {page.url}")
                except Exception as login_err:
                    print(f"Login attempt failed: {login_err}")
    except Exception as e:
        print(f"Login error: {e}")
        pass

def delete_all_messages(page):
    total_deleted = 0
    print(f"Starting message deletion. Current URL: {page.url}")

    # まず一定回数スクロールして古いメッセージを読み込む
    print("Loading older messages...")
    for i in range(SCROLL_BATCHES):
        scroll_load_older(page)
        if i % 5 == 0:  # 5回ごとに進捗表示
            current_msgs = page.locator(SELECTORS["message_row"]).count()
            print(f"  Loaded {current_msgs} messages so far...")

    initial_count = page.locator(SELECTORS["message_row"]).count()
    print(f"Total messages found: {initial_count}")

    while total_deleted < MAX_BATCH_DELETE:
        rows = page.locator(SELECTORS["message_row"])
        count = rows.count()
        print(f"Found {count} messages to delete")
        if count == 0:
            print("No messages found - checking if we're on the right page")
            print(f"Page title: {page.title()}")
            break

        # 最初のメッセージで実際の構造を調査
        if count > 0 and total_deleted == 0:
            print("Investigating actual page structure...")
            first_msg = rows.first
            
            # メッセージ全体の構造を確認
            print("Message HTML structure:")
            html_content = first_msg.inner_html()
            print(f"  Message HTML: {html_content[:500]}...")  # 最初の500文字
            
            # すべてのボタンを探す
            all_buttons = first_msg.locator('button')
            all_btn_count = all_buttons.count()
            print(f"  Buttons in message: {all_btn_count}")
            
            for j in range(min(all_btn_count, 5)):
                btn = all_buttons.nth(j)
                btn_text = btn.text_content().strip()
                btn_class = btn.get_attribute('class') or 'N/A'
                btn_aria = btn.get_attribute('aria-label') or 'N/A'
                print(f"    Button {j}: text='{btn_text}', class='{btn_class}', aria-label='{btn_aria}'")
            
            # すべてのリンクも確認
            all_links = first_msg.locator('a')
            all_link_count = all_links.count()
            print(f"  Links in message: {all_link_count}")
            
            for j in range(min(all_link_count, 3)):
                link = all_links.nth(j)
                link_text = link.text_content().strip()
                link_class = link.get_attribute('class') or 'N/A'
                link_href = link.get_attribute('href') or 'N/A'
                print(f"    Link {j}: text='{link_text}', class='{link_class}', href='{link_href}'")
            
            # より詳細なホバーテスト
            print("Testing detailed hover interaction...")
            
            # マウスを動かしてからホバー
            first_msg.scroll_into_view_if_needed()
            time.sleep(0.5)
            
            print("  Hovering over message...")
            first_msg.hover()
            time.sleep(2)  # より長い待機
            
            # ホバー後の全HTML構造を確認
            print("  Message HTML after hover:")
            html_after_hover = first_msg.inner_html()
            print(f"    HTML: {html_after_hover[:800]}...")
            
            # ホバー後にボタンが出現するかチェック（より広い範囲で）
            hover_buttons = first_msg.locator('button, a, span[onclick], div[onclick], [role="button"]')
            hover_btn_count = hover_buttons.count()
            print(f"  Interactive elements after hover: {hover_btn_count}")
            
            for k in range(min(hover_btn_count, 10)):
                elem = hover_buttons.nth(k)
                elem_tag = elem.evaluate('el => el.tagName.toLowerCase()')
                elem_text = elem.text_content().strip()
                elem_class = elem.get_attribute('class') or 'N/A'
                elem_onclick = elem.get_attribute('onclick') or 'N/A'
                elem_title = elem.get_attribute('title') or 'N/A'
                print(f"    Element {k}: tag='{elem_tag}', text='{elem_text}', class='{elem_class}', onclick='{elem_onclick}', title='{elem_title}'")
            
            # ページ全体でホバー後の変化をチェック
            print("  Checking page-wide changes after hover...")
            page_wide_buttons = page.locator('button, [role="button"], .delete-btn, [onclick*="delete"], [title*="delete"], [aria-label*="delete"]')
            page_wide_count = page_wide_buttons.count()
            print(f"  Page-wide interactive elements: {page_wide_count}")
            
            if page_wide_count > 0:
                for m in range(min(page_wide_count, 5)):
                    elem = page_wide_buttons.nth(m)
                    elem_text = elem.text_content().strip()
                    elem_class = elem.get_attribute('class') or 'N/A'
                    elem_title = elem.get_attribute('title') or 'N/A'
                    print(f"    Page element {m}: text='{elem_text}', class='{elem_class}', title='{elem_title}'")
            
            # ページ全体でメニューや削除関連要素を探す
            print("Searching for delete elements on entire page...")
            page_delete_btns = page.locator('button:has-text("Delete"), button:has-text("削除"), [aria-label*="delete"], [title*="delete"]')
            page_delete_count = page_delete_btns.count()
            print(f"  Delete buttons on page: {page_delete_count}")
            
            if page_delete_count > 0:
                for k in range(min(page_delete_count, 3)):
                    btn = page_delete_btns.nth(k)
                    btn_text = btn.text_content().strip()
                    btn_class = btn.get_attribute('class') or 'N/A'
                    print(f"    Delete btn {k}: text='{btn_text}', class='{btn_class}'")
            
            # 右クリック処理は不要なので削除
            
            print("Checking if this is an admin interface...")
            page_title = page.title()
            current_url = page.url
            print(f"  Page title: {page_title}")
            print(f"  Current URL: {current_url}")
            
            # 管理画面へのリンクがあるかチェック
            admin_links = page.locator('a:has-text("Admin"), a:has-text("管理"), a[href*="admin"], a[href*="manage"]')
            admin_count = admin_links.count()
            print(f"  Admin links found: {admin_count}")

        # 削除処理（常に最初のメッセージを削除）
        while total_deleted < MAX_BATCH_DELETE:
            # メッセージを再取得（削除後にDOM構造が変わるため）
            current_rows = page.locator(SELECTORS["message_row"])
            current_count = current_rows.count()
            
            if current_count == 0:
                print("No more messages to delete")
                break
            
            # 常に最初のメッセージを削除
            first_msg = current_rows.first
            print(f"Deleting message {total_deleted + 1} (remaining: {current_count})")
            ok = try_delete_message(page, first_msg)
            
            if ok:
                total_deleted += 1
                time.sleep(0.5)  # DOM更新待ち
            else:
                print("Failed to delete message, stopping...")
                break

        # さらに古いメッセージを読み込んで続行
        if current_count == 0:
            # メッセージがなくなったら、さらに古いメッセージを読み込み
            print("No more visible messages, trying to load more...")
            for _ in range(5):  # 5回追加スクロール
                scroll_load_older(page)
                time.sleep(0.3)
            
            # 追加読み込み後にメッセージがあるかチェック
            final_check = page.locator(SELECTORS["message_row"]).count()
            if final_check == 0:
                print("No more messages to load - deletion complete!")
                break
            else:
                print(f"Found {final_check} more messages after additional loading")

    print(f"Deletion session completed. Total deleted: {total_deleted}")
    return total_deleted

def main():
    assert CHATROLL_USER and CHATROLL_PASS and CHATROLL_ROOM_URLS, \
        "CHATROLL_USER / CHATROLL_PASS / CHATROLL_ROOM_URLS を設定してください。"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # GitHub Actions用にheadless=Trueに変更
        context = browser.new_context()
        page = context.new_page()

        # まずログイン処理を実行
        page.goto("https://chatroll.com/", wait_until="domcontentloaded")
        login_if_needed(page)
        
        # ログイン完了後の追加確認
        time.sleep(2)
        print(f"メイン処理開始前のURL確認: {page.url}")
        print(f"ページタイトル: {page.title()}")

        total_deleted = 0
        
        # 各チャットルームで順次削除処理
        for i, room_url in enumerate(CHATROLL_ROOM_URLS, 1):
            print(f"\n=== Processing Room {i}: {room_url} ===")
            
            try:
                # チャットルームへ移動
                page.goto(room_url, wait_until="domcontentloaded")
                
                # ページロード待ち（タイムアウト対策）
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=5000)
                    time.sleep(0.5)  # 短縮
                    print(f"Room loaded. Current URL: {page.url}")
                except:
                    print("Room load timeout, but continuing...")

                # 削除実行
                deleted = delete_all_messages(page)
                total_deleted += deleted
                print(f"Deleted messages in room {i}: {deleted}")
                
            except Exception as e:
                print(f"Error processing room {room_url}: {e}")
                continue

        print(f"\n=== Total deleted messages across all rooms: {total_deleted} ===")

        # 終了
        time.sleep(1)
        browser.close()

if __name__ == "__main__":
    main()
