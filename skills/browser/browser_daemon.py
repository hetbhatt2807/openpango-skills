#!/usr/bin/env python3
"""
browser_daemon.py - Full-capability Browser Daemon for OpenClaw.
Keeps a persistent Chromium browser open with anti-detection measures.
Listens on localhost:9222 for HTTP POST commands.

Commands: goto, click, type, select, read, screenshot, keyboard, scroll,
          wait, wait_for_change, hover, exec_js, upload, tabs, dialog,
          cookies, fill_form, drag, block_urls, console_logs, download
"""

import json
import os
import random
import re
import sys
import time
import threading
from collections import deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print(json.dumps({"status": "error", "message": "Playwright is not installed. Run: pip install playwright && playwright install"}))
    sys.exit(1)

BASE_DIR = Path(__file__).parent
USER_DATA_DIR = BASE_DIR / ".browser_data"
SCREENSHOTS_DIR = USER_DATA_DIR / "screenshots"
DOWNLOADS_DIR = USER_DATA_DIR / "downloads"
PORT = 9222

# Global state
playwright_instance = None
browser_context = None
current_page = None
all_pages = []  # Track all open tabs
element_index = {}  # Maps interactive-read index numbers to selectors
console_buffer = deque(maxlen=200)  # Ring buffer of console messages
blocked_patterns = []  # URL patterns to block
download_files = []  # Completed downloads


def log_err(msg):
    print(msg, file=sys.stderr, flush=True)


def auto_screenshot_on_error(func):
    """Decorator: auto-capture screenshot when a command fails."""
    def wrapper(payload):
        try:
            return func(payload)
        except Exception as e:
            error_msg = str(e)
            screenshot_path = None
            try:
                SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filepath = SCREENSHOTS_DIR / f"error_{timestamp}.png"
                current_page.screenshot(path=str(filepath))
                screenshot_path = str(filepath.resolve())
                log_err(f"Error screenshot saved: {filepath}")
            except Exception:
                pass
            result = {"status": "error", "message": error_msg}
            if screenshot_path:
                result["error_screenshot"] = screenshot_path
            return result
    return wrapper


def dismiss_popups(page):
    """Attempt to clear common cookie banners and popups."""
    common_selectors = [
        "button:has-text('Accept All')",
        "button:has-text('Accept cookies')",
        "button:has-text('Accept all cookies')",
        "button:has-text('I Agree')",
        "button:has-text('Got it')",
        "button:has-text('OK')",
        "[aria-label='Close']",
        "[aria-label='Accept']",
        "button:has-text('Allow all')",
        "button:has-text('Consent')",
    ]
    for sel in common_selectors:
        try:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                loc.first.click(timeout=1500)
                time.sleep(0.3)
        except Exception:
            pass


def simulate_natural_click(page, selector, double=False, right=False):
    """Move mouse to element center and click naturally."""
    loc = page.locator(selector).first
    loc.wait_for(state="attached", timeout=5000)
    loc.scroll_into_view_if_needed()
    time.sleep(0.2)

    box = loc.bounding_box()
    if box:
        x = box["x"] + box["width"] / 2 + random.uniform(-2, 2)
        y = box["y"] + box["height"] / 2 + random.uniform(-2, 2)
        page.mouse.move(x, y, steps=random.randint(5, 15))
        time.sleep(random.uniform(0.05, 0.15))

        if right:
            page.mouse.click(x, y, button="right")
        elif double:
            page.mouse.dblclick(x, y)
        else:
            page.mouse.down()
            time.sleep(random.uniform(0.03, 0.08))
            page.mouse.up()
    else:
        if double:
            loc.dblclick(force=True)
        elif right:
            loc.click(button="right", force=True)
        else:
            loc.click(force=True)


def sync_pages():
    """Keep our page list in sync with the browser context."""
    global all_pages, current_page
    all_pages = list(browser_context.pages)
    if current_page not in all_pages and all_pages:
        current_page = all_pages[-1]


def setup_page_listeners(page):
    """Attach console and download listeners to a page."""
    page.on("console", lambda msg: console_buffer.append({
        "type": msg.type,
        "text": msg.text,
        "url": page.url,
        "timestamp": datetime.now().isoformat(),
    }))

    page.on("download", lambda dl: _handle_download(dl))


def _handle_download(download):
    """Save downloaded files automatically."""
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    suggested = download.suggested_filename
    save_path = DOWNLOADS_DIR / suggested
    # Avoid overwriting
    if save_path.exists():
        stem = save_path.stem
        suffix = save_path.suffix
        save_path = DOWNLOADS_DIR / f"{stem}_{datetime.now().strftime('%H%M%S')}{suffix}"
    try:
        download.save_as(str(save_path))
        download_files.append({
            "filename": save_path.name,
            "path": str(save_path.resolve()),
            "url": download.url,
            "timestamp": datetime.now().isoformat(),
        })
        log_err(f"Download saved: {save_path}")
    except Exception as e:
        log_err(f"Download failed: {e}")


def _get_iframe_content(page):
    """Extract content from same-origin iframes."""
    iframe_texts = []
    try:
        frames = page.frames
        for frame in frames:
            if frame == page.main_frame:
                continue
            try:
                name = frame.name or frame.url
                text = frame.evaluate("() => document.body ? document.body.innerText : ''")
                if text and text.strip():
                    iframe_texts.append(f"[IFRAME: {name}]\n{text[:2000]}")
            except Exception:
                pass
    except Exception:
        pass
    return "\n\n".join(iframe_texts)


# ─── Command Handlers ────────────────────────────────────────────

@auto_screenshot_on_error
def handle_goto(payload):
    global current_page
    url = payload.get("url")
    if not url:
        return {"status": "error", "message": "Missing 'url' parameter"}

    log_err(f"Navigating to {url} ...")
    current_page.goto(url, timeout=30000, wait_until="domcontentloaded")
    time.sleep(1)
    dismiss_popups(current_page)
    return {
        "status": "success",
        "action": "goto",
        "url": current_page.url,
        "title": current_page.title(),
    }


@auto_screenshot_on_error
def handle_click(payload):
    global current_page
    selector = payload.get("selector")
    index = payload.get("index")
    double = payload.get("double", False)
    right = payload.get("right", False)

    if index is not None:
        idx = int(index)
        if idx not in element_index:
            return {"status": "error", "message": f"Index [{idx}] not found. Run 'read' with mode='interactive' first."}
        selector = element_index[idx]

    if not selector:
        return {"status": "error", "message": "Provide 'selector' or 'index' parameter"}

    log_err(f"Clicking: '{selector}' (double={double}, right={right})")
    dismiss_popups(current_page)
    simulate_natural_click(current_page, selector, double=double, right=right)
    current_page.wait_for_timeout(800)
    sync_pages()
    return {
        "status": "success",
        "action": "click",
        "selector": selector,
        "current_url": current_page.url,
    }


@auto_screenshot_on_error
def handle_type(payload):
    global current_page
    selector = payload.get("selector")
    text = payload.get("text", "")
    clear = payload.get("clear", True)
    submit = payload.get("submit", False)
    index = payload.get("index")

    if index is not None:
        idx = int(index)
        if idx not in element_index:
            return {"status": "error", "message": f"Index [{idx}] not found."}
        selector = element_index[idx]

    if not selector:
        return {"status": "error", "message": "Provide 'selector' or 'index' parameter"}

    log_err(f"Typing into: '{selector}'")
    dismiss_popups(current_page)
    simulate_natural_click(current_page, selector)
    time.sleep(0.2)

    if clear:
        current_page.locator(selector).first.fill("")

    current_page.keyboard.type(text, delay=random.randint(40, 100))

    if submit:
        time.sleep(0.2)
        current_page.keyboard.press("Enter")
        current_page.wait_for_timeout(1000)

    return {
        "status": "success",
        "action": "type",
        "selector": selector,
        "text_length": len(text),
        "submitted": submit,
    }


@auto_screenshot_on_error
def handle_select(payload):
    global current_page
    selector = payload.get("selector")
    value = payload.get("value")

    if not selector or not value:
        return {"status": "error", "message": "Missing 'selector' or 'value'"}

    log_err(f"Selecting '{value}' in: '{selector}'")
    dismiss_popups(current_page)
    current_page.locator(selector).first.select_option(label=value)
    time.sleep(0.3)
    return {"status": "success", "action": "select", "selector": selector, "value": value}


@auto_screenshot_on_error
def handle_read(payload):
    global current_page, element_index
    mode = payload.get("mode", "interactive")
    container = payload.get("selector")
    include_iframes = payload.get("iframes", True)

    current_page.wait_for_load_state("domcontentloaded")
    time.sleep(1)

    if mode == "full":
        if container:
            html = current_page.locator(container).first.inner_html()
        else:
            html = current_page.content()
        iframe_content = ""
        if include_iframes:
            iframe_content = _get_iframe_content(current_page)
            if iframe_content:
                html += f"\n\n=== IFRAME CONTENT ===\n{iframe_content}"
        max_chars = 30000
        if len(html) > max_chars:
            html = html[:max_chars] + "\n\n...[TRUNCATED]"
        return {
            "status": "success",
            "action": "read",
            "mode": "full",
            "url": current_page.url,
            "title": current_page.title(),
            "content": html,
        }

    elif mode == "interactive":
        script = """
        (containerSel) => {
            const root = containerSel ? document.querySelector(containerSel) : document;
            if (!root) return { elements: [], text_summary: "Container not found." };

            const interactiveEls = root.querySelectorAll(
                'a, button, input, textarea, select, [role="button"], [role="link"], [role="tab"], [role="menuitem"], [role="checkbox"], [role="radio"], [role="switch"], [contenteditable="true"], [onclick], [tabindex]'
            );

            const elements = [];
            let idx = 1;

            for (const el of interactiveEls) {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                if (rect.width === 0 || rect.height === 0 || style.visibility === 'hidden' || style.display === 'none' || style.opacity === '0') continue;

                const tag = el.tagName.toLowerCase();
                let desc = '';
                let selectorStr = '';

                if (el.id) {
                    selectorStr = '#' + CSS.escape(el.id);
                } else if (el.name && (tag === 'input' || tag === 'textarea' || tag === 'select')) {
                    selectorStr = tag + '[name="' + el.getAttribute('name') + '"]';
                } else if (el.getAttribute('data-testid')) {
                    selectorStr = '[data-testid="' + el.getAttribute('data-testid') + '"]';
                } else if (el.getAttribute('aria-label')) {
                    selectorStr = '[aria-label="' + el.getAttribute('aria-label') + '"]';
                } else {
                    const text = (el.textContent || '').trim().substring(0, 40);
                    if (text && (tag === 'a' || tag === 'button' || el.getAttribute('role'))) {
                        selectorStr = tag + ':has-text("' + text.replace(/"/g, '\\\\"') + '")';
                    } else {
                        let path = [];
                        let node = el;
                        while (node && node !== document.body && path.length < 4) {
                            let seg = node.tagName.toLowerCase();
                            if (node.id) { seg = '#' + CSS.escape(node.id); path.unshift(seg); break; }
                            const parent = node.parentElement;
                            if (parent) {
                                const siblings = Array.from(parent.children).filter(c => c.tagName === node.tagName);
                                if (siblings.length > 1) seg += ':nth-child(' + (Array.from(parent.children).indexOf(node) + 1) + ')';
                            }
                            path.unshift(seg);
                            node = parent;
                        }
                        selectorStr = path.join(' > ');
                    }
                }

                if (tag === 'input') {
                    const type = el.getAttribute('type') || 'text';
                    const name = el.getAttribute('name') || '';
                    const placeholder = el.getAttribute('placeholder') || '';
                    const val = el.value || '';
                    const checked = el.checked;
                    desc = 'Input[' + type + ']' + (name ? ' name="' + name + '"' : '') + (placeholder ? ' placeholder="' + placeholder + '"' : '') + (val ? ' value="' + val + '"' : '');
                    if (type === 'checkbox' || type === 'radio') desc += checked ? ' [CHECKED]' : ' [unchecked]';
                } else if (tag === 'textarea') {
                    const name = el.getAttribute('name') || '';
                    const placeholder = el.getAttribute('placeholder') || '';
                    const val = el.value || '';
                    desc = 'Textarea' + (name ? ' name="' + name + '"' : '') + (placeholder ? ' placeholder="' + placeholder + '"' : '') + (val ? ' value="' + val.substring(0, 30) + '..."' : '');
                } else if (tag === 'select') {
                    const name = el.getAttribute('name') || el.id || '';
                    const opts = Array.from(el.options).map(o => o.text.trim()).slice(0, 5).join(', ');
                    const selected = el.options[el.selectedIndex] ? el.options[el.selectedIndex].text.trim() : '';
                    desc = 'Select' + (name ? ' name="' + name + '"' : '') + ' selected="' + selected + '" options=[' + opts + ']';
                } else if (tag === 'a') {
                    const text = (el.textContent || '').trim().substring(0, 60);
                    const href = el.getAttribute('href') || '';
                    desc = 'Link: "' + text + '"' + (href ? ' -> ' + href : '');
                } else if (tag === 'button' || el.getAttribute('role') === 'button') {
                    const text = (el.textContent || '').trim().substring(0, 60);
                    const disabled = el.disabled || el.getAttribute('aria-disabled') === 'true';
                    desc = 'Button: "' + text + '"' + (disabled ? ' [DISABLED]' : '');
                } else {
                    const role = el.getAttribute('role') || '';
                    const text = (el.textContent || '').trim().substring(0, 60);
                    const checked = el.getAttribute('aria-checked');
                    desc = (role ? role.charAt(0).toUpperCase() + role.slice(1) : tag) + ': "' + text + '"';
                    if (checked !== null) desc += checked === 'true' ? ' [CHECKED]' : ' [unchecked]';
                }

                elements.push({ idx: idx, desc: desc, selector: selectorStr });
                idx++;
            }

            const headings = root.querySelectorAll('h1, h2, h3');
            let textSummary = '';
            for (const h of headings) {
                if (h.offsetWidth > 0 && h.offsetHeight > 0) {
                    const level = parseInt(h.tagName.substring(1));
                    textSummary += '#'.repeat(level) + ' ' + h.textContent.trim() + '\\n';
                }
            }

            const mainText = (root.body || root).innerText || '';
            textSummary += '\\n' + mainText.substring(0, 3000);

            return { elements: elements, text_summary: textSummary };
        }
        """
        result = current_page.evaluate(script, container)

        element_index = {}
        lines = []
        for el in result.get("elements", []):
            element_index[el["idx"]] = el["selector"]
            lines.append(f"[{el['idx']}] {el['desc']}")

        interactive_content = "\n".join(lines)
        text_summary = result.get("text_summary", "")

        # Include iframe content
        iframe_section = ""
        if include_iframes:
            iframe_text = _get_iframe_content(current_page)
            if iframe_text:
                iframe_section = f"\n\n=== Iframe Content ===\n{iframe_text}"

        full_content = f"=== Interactive Elements ===\n{interactive_content}\n\n=== Page Text ===\n{text_summary}{iframe_section}"
        max_chars = 25000
        if len(full_content) > max_chars:
            full_content = full_content[:max_chars] + "\n\n...[TRUNCATED]"

        return {
            "status": "success",
            "action": "read",
            "mode": "interactive",
            "url": current_page.url,
            "title": current_page.title(),
            "element_count": len(result.get("elements", [])),
            "content": full_content,
        }

    else:  # mode == "text" (legacy)
        script = """
        (containerSel) => {
            const root = containerSel ? document.querySelector(containerSel) : document;
            if (!root) return "Container not found.";
            let markdown = "";
            const elements = (root.body || root).querySelectorAll('h1, h2, h3, h4, h5, h6, p, a, button, li, span, input, textarea, select');

            for (const el of elements) {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                if (rect.width === 0 || rect.height === 0 || style.visibility === 'hidden' || style.display === 'none') continue;

                let text = "";
                const tag = el.tagName;

                if (tag === 'INPUT' || tag === 'TEXTAREA') {
                    const name = el.getAttribute('name') || '';
                    const placeholder = el.getAttribute('placeholder') || '';
                    const type = el.getAttribute('type') || 'text';
                    const val = el.value || '';
                    markdown += '[INPUT ' + type + ': name="' + name + '", placeholder="' + placeholder + '", value="' + val + '"]\\n\\n';
                    continue;
                } else if (tag === 'SELECT') {
                    const name = el.getAttribute('name') || el.id || '';
                    const options = Array.from(el.options).map(o => o.text.trim() || o.value).slice(0,5).join(', ');
                    markdown += '[SELECT: name="' + name + '", options="' + options + '..."]\\n\\n';
                    continue;
                } else if (tag === 'SPAN') {
                    text = Array.from(el.childNodes).filter(n => n.nodeType === Node.TEXT_NODE).map(n => n.textContent).join('').trim();
                } else {
                    text = el.innerText ? el.innerText.trim() : '';
                }

                if (!text) continue;

                if (tag.startsWith('H')) {
                    const level = parseInt(tag.substring(1));
                    markdown += '#'.repeat(level) + ' ' + text + '\\n\\n';
                } else if (tag === 'A') {
                    markdown += '[' + text + '](' + el.href + ')\\n\\n';
                } else if (tag === 'BUTTON') {
                    markdown += '`[BUTTON: ' + text + ']`\\n\\n';
                } else if (tag === 'LI') {
                    markdown += '- ' + text + '\\n';
                } else {
                    markdown += text + '\\n\\n';
                }
            }

            if (markdown.trim() === "") {
                markdown = (root.body || root).innerText || "Page appears empty.";
            }
            return markdown;
        }
        """
        markdown_content = current_page.evaluate(script, container)
        max_chars = 20000
        if len(markdown_content) > max_chars:
            markdown_content = markdown_content[:max_chars] + "\n\n...[TRUNCATED]"

        return {
            "status": "success",
            "action": "read",
            "mode": "text",
            "url": current_page.url,
            "title": current_page.title(),
            "content": markdown_content,
        }


@auto_screenshot_on_error
def handle_screenshot(payload):
    global current_page
    selector = payload.get("selector")
    full_page = payload.get("full_page", False)

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filepath = SCREENSHOTS_DIR / f"screenshot_{timestamp}.png"

    if selector:
        loc = current_page.locator(selector).first
        loc.wait_for(state="visible", timeout=5000)
        loc.screenshot(path=str(filepath))
    else:
        current_page.screenshot(path=str(filepath), full_page=full_page)

    log_err(f"Screenshot saved: {filepath}")
    return {
        "status": "success",
        "action": "screenshot",
        "path": str(filepath.resolve()),
        "url": current_page.url,
    }


@auto_screenshot_on_error
def handle_keyboard(payload):
    global current_page
    key = payload.get("key")
    if not key:
        return {"status": "error", "message": "Missing 'key' parameter. Examples: 'Enter', 'Tab', 'Escape', 'Control+a'"}

    log_err(f"Pressing key: {key}")
    current_page.keyboard.press(key)
    current_page.wait_for_timeout(300)
    return {"status": "success", "action": "keyboard", "key": key, "current_url": current_page.url}


@auto_screenshot_on_error
def handle_scroll(payload):
    global current_page
    selector = payload.get("selector")
    direction = payload.get("direction", "down")
    amount = int(payload.get("amount", 500))

    if selector:
        loc = current_page.locator(selector).first
        loc.scroll_into_view_if_needed()
        time.sleep(0.3)
        return {"status": "success", "action": "scroll", "scrolled_to": selector, "current_url": current_page.url}
    else:
        delta_y = amount if direction == "down" else -amount
        current_page.mouse.wheel(0, delta_y)
        time.sleep(0.5)
        return {"status": "success", "action": "scroll", "direction": direction, "amount": amount, "current_url": current_page.url}


@auto_screenshot_on_error
def handle_wait(payload):
    global current_page
    selector = payload.get("selector")
    state = payload.get("state", "visible")
    timeout = int(payload.get("timeout", 10000))

    if not selector:
        duration = timeout / 1000
        time.sleep(duration)
        return {"status": "success", "action": "wait", "waited_ms": timeout}

    log_err(f"Waiting for '{selector}' to be {state} (timeout={timeout}ms)")
    current_page.locator(selector).first.wait_for(state=state, timeout=timeout)
    return {"status": "success", "action": "wait", "selector": selector, "state": state}


@auto_screenshot_on_error
def handle_wait_for_change(payload):
    """Wait until page content changes (URL change, new elements, text change)."""
    global current_page
    timeout = int(payload.get("timeout", 10000))
    watch = payload.get("watch", "any")  # "url", "content", "any"

    old_url = current_page.url
    old_text_hash = hash(current_page.evaluate("() => document.body ? document.body.innerText.substring(0, 5000) : ''"))

    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        if watch in ("url", "any") and current_page.url != old_url:
            return {"status": "success", "action": "wait_for_change", "changed": "url", "old": old_url, "new": current_page.url}

        new_hash = hash(current_page.evaluate("() => document.body ? document.body.innerText.substring(0, 5000) : ''"))
        if watch in ("content", "any") and new_hash != old_text_hash:
            return {"status": "success", "action": "wait_for_change", "changed": "content", "url": current_page.url}

        time.sleep(0.3)

    return {"status": "error", "message": f"No change detected within {timeout}ms"}


@auto_screenshot_on_error
def handle_hover(payload):
    global current_page
    selector = payload.get("selector")
    if not selector:
        return {"status": "error", "message": "Missing 'selector' parameter"}

    loc = current_page.locator(selector).first
    loc.wait_for(state="visible", timeout=5000)
    loc.scroll_into_view_if_needed()
    time.sleep(0.2)

    box = loc.bounding_box()
    if box:
        x = box["x"] + box["width"] / 2
        y = box["y"] + box["height"] / 2
        current_page.mouse.move(x, y, steps=10)
    else:
        loc.hover()

    time.sleep(0.3)
    return {"status": "success", "action": "hover", "selector": selector}


@auto_screenshot_on_error
def handle_exec_js(payload):
    global current_page
    script = payload.get("script")
    if not script:
        return {"status": "error", "message": "Missing 'script' parameter"}

    log_err(f"Executing JS: {script[:80]}...")
    result = current_page.evaluate(script)

    try:
        json.dumps(result)
        serialized = result
    except (TypeError, ValueError):
        serialized = str(result)

    return {"status": "success", "action": "exec_js", "result": serialized}


@auto_screenshot_on_error
def handle_upload(payload):
    global current_page
    selector = payload.get("selector")
    file_path = payload.get("file_path")

    if not selector or not file_path:
        return {"status": "error", "message": "Missing 'selector' or 'file_path'"}

    if not Path(file_path).exists():
        return {"status": "error", "message": f"File not found: {file_path}"}

    log_err(f"Uploading {file_path} to {selector}")
    current_page.locator(selector).first.set_input_files(file_path)
    time.sleep(0.5)
    return {"status": "success", "action": "upload", "selector": selector, "file": file_path}


@auto_screenshot_on_error
def handle_tabs(payload):
    global current_page, all_pages
    sync_pages()
    sub = payload.get("sub", "list")

    if sub == "list":
        tab_info = []
        for i, pg in enumerate(all_pages):
            tab_info.append({
                "index": i,
                "url": pg.url,
                "title": pg.title(),
                "active": pg == current_page,
            })
        return {"status": "success", "action": "tabs_list", "tabs": tab_info, "count": len(tab_info)}

    elif sub == "switch":
        idx = int(payload.get("index", 0))
        if 0 <= idx < len(all_pages):
            current_page = all_pages[idx]
            current_page.bring_to_front()
            return {"status": "success", "action": "tabs_switch", "index": idx, "url": current_page.url}
        return {"status": "error", "message": f"Tab index {idx} out of range (0-{len(all_pages)-1})"}

    elif sub == "new":
        url = payload.get("url", "about:blank")
        new_page = browser_context.new_page()
        setup_page_listeners(new_page)
        if url != "about:blank":
            new_page.goto(url, timeout=30000, wait_until="domcontentloaded")
        current_page = new_page
        sync_pages()
        return {"status": "success", "action": "tabs_new", "index": len(all_pages) - 1, "url": current_page.url}

    elif sub == "close":
        idx = int(payload.get("index", -1))
        if idx < 0:
            idx = all_pages.index(current_page) if current_page in all_pages else len(all_pages) - 1
        if 0 <= idx < len(all_pages):
            all_pages[idx].close()
            sync_pages()
            return {"status": "success", "action": "tabs_close", "closed_index": idx, "remaining": len(all_pages)}
        return {"status": "error", "message": f"Tab index {idx} out of range"}

    return {"status": "error", "message": f"Unknown tabs sub-command: {sub}"}


def handle_dialog(payload):
    action = payload.get("action", "accept")
    text = payload.get("text")

    def on_dialog(dialog):
        log_err(f"Dialog detected: type={dialog.type}, message={dialog.message}")
        if action == "dismiss":
            dialog.dismiss()
        else:
            if text is not None:
                dialog.accept(text)
            else:
                dialog.accept()

    current_page.on("dialog", on_dialog)
    return {
        "status": "success",
        "action": "dialog",
        "handler_set": action,
        "message": f"Dialog handler registered. Next dialog will be {action}ed.",
    }


def handle_cookies(payload):
    sub = payload.get("sub", "list")

    if sub == "list":
        domain = payload.get("domain")
        cookies = browser_context.cookies()
        if domain:
            cookies = [c for c in cookies if domain in c.get("domain", "")]
        for c in cookies:
            c.pop("sameSite", None)
            c.pop("httpOnly", None)
            c.pop("secure", None)
        return {"status": "success", "action": "cookies_list", "count": len(cookies), "cookies": cookies[:50]}

    elif sub == "set":
        cookie_data = payload.get("cookie")
        if not cookie_data:
            return {"status": "error", "message": "Missing 'cookie' object with url/name/value"}
        if isinstance(cookie_data, list):
            browser_context.add_cookies(cookie_data)
        else:
            browser_context.add_cookies([cookie_data])
        return {"status": "success", "action": "cookies_set"}

    elif sub == "clear":
        browser_context.clear_cookies()
        return {"status": "success", "action": "cookies_clear"}

    return {"status": "error", "message": f"Unknown cookies sub-command: {sub}"}


@auto_screenshot_on_error
def handle_fill_form(payload):
    """Fill multiple form fields at once from a JSON dict."""
    global current_page
    fields = payload.get("fields")
    if not fields or not isinstance(fields, dict):
        return {"status": "error", "message": "Missing 'fields' dict. Example: {\"input[name='email']\": \"user@example.com\", \"input[name='password']\": \"pass123\"}"}

    filled = []
    errors = []
    dismiss_popups(current_page)

    for selector, value in fields.items():
        try:
            loc = current_page.locator(selector).first
            loc.wait_for(state="attached", timeout=3000)
            loc.scroll_into_view_if_needed()
            time.sleep(0.15)

            tag = loc.evaluate("el => el.tagName.toLowerCase()")
            input_type = loc.evaluate("el => (el.getAttribute('type') || '').toLowerCase()")

            if tag == "select":
                loc.select_option(label=value)
            elif input_type in ("checkbox", "radio"):
                checked = loc.is_checked()
                should_check = str(value).lower() in ("true", "1", "yes", "on")
                if checked != should_check:
                    loc.click()
            else:
                # Click, clear, type with natural-looking delays
                loc.click()
                time.sleep(0.1)
                loc.fill("")
                current_page.keyboard.type(str(value), delay=random.randint(30, 80))

            filled.append(selector)
            time.sleep(random.uniform(0.1, 0.3))
        except Exception as e:
            errors.append({"selector": selector, "error": str(e)})

    submit = payload.get("submit", False)
    if submit and filled:
        time.sleep(0.3)
        current_page.keyboard.press("Enter")
        current_page.wait_for_timeout(1000)

    return {
        "status": "success" if not errors else "partial",
        "action": "fill_form",
        "filled": filled,
        "errors": errors,
        "submitted": submit,
        "current_url": current_page.url,
    }


@auto_screenshot_on_error
def handle_drag(payload):
    """Drag an element from source to target."""
    global current_page
    source = payload.get("source")
    target = payload.get("target")

    if not source or not target:
        return {"status": "error", "message": "Missing 'source' or 'target' selector"}

    src_loc = current_page.locator(source).first
    tgt_loc = current_page.locator(target).first

    src_loc.wait_for(state="visible", timeout=5000)
    tgt_loc.wait_for(state="visible", timeout=5000)

    src_box = src_loc.bounding_box()
    tgt_box = tgt_loc.bounding_box()

    if not src_box or not tgt_box:
        # Fallback to Playwright's built-in drag
        src_loc.drag_to(tgt_loc)
    else:
        sx = src_box["x"] + src_box["width"] / 2
        sy = src_box["y"] + src_box["height"] / 2
        tx = tgt_box["x"] + tgt_box["width"] / 2
        ty = tgt_box["y"] + tgt_box["height"] / 2

        # Natural-looking drag: move to source, press, move to target in steps, release
        current_page.mouse.move(sx, sy, steps=10)
        time.sleep(0.15)
        current_page.mouse.down()
        time.sleep(0.1)
        current_page.mouse.move(tx, ty, steps=20)
        time.sleep(0.1)
        current_page.mouse.up()

    time.sleep(0.5)
    return {"status": "success", "action": "drag", "source": source, "target": target}


def handle_block_urls(payload):
    """Block network requests matching URL patterns (ads, trackers, etc.)."""
    global blocked_patterns
    sub = payload.get("sub", "add")

    if sub == "add":
        patterns = payload.get("patterns", [])
        if isinstance(patterns, str):
            patterns = [patterns]
        blocked_patterns.extend(patterns)

        # Apply route blocking
        for pattern in patterns:
            try:
                browser_context.route(pattern, lambda route: route.abort())
                log_err(f"Blocking URL pattern: {pattern}")
            except Exception as e:
                log_err(f"Failed to block pattern {pattern}: {e}")

        return {"status": "success", "action": "block_urls", "blocked_count": len(blocked_patterns), "patterns": blocked_patterns}

    elif sub == "list":
        return {"status": "success", "action": "block_urls_list", "patterns": blocked_patterns}

    elif sub == "preset":
        # Common ad/tracker domains
        preset_patterns = [
            "**/*doubleclick.net/**",
            "**/*google-analytics.com/**",
            "**/*googletagmanager.com/**",
            "**/*facebook.com/tr/**",
            "**/*facebook.net/signals/**",
            "**/*hotjar.com/**",
            "**/*mixpanel.com/**",
            "**/*segment.io/**",
            "**/*amplitude.com/**",
            "**/*ads.linkedin.com/**",
            "**/*bat.bing.com/**",
            "**/*pixel.wp.com/**",
            "**/*connect.facebook.net/**",
            "**/*pagead2.googlesyndication.com/**",
            "**/*adservice.google.com/**",
        ]
        for pattern in preset_patterns:
            try:
                browser_context.route(pattern, lambda route: route.abort())
            except Exception:
                pass
        blocked_patterns.extend(preset_patterns)
        return {"status": "success", "action": "block_urls_preset", "blocked_count": len(preset_patterns), "message": "Common ad/tracker domains blocked."}

    elif sub == "clear":
        browser_context.unroute_all()
        blocked_patterns.clear()
        return {"status": "success", "action": "block_urls_clear"}

    return {"status": "error", "message": f"Unknown sub-command: {sub}"}


def handle_console_logs(payload):
    """Retrieve captured console log messages."""
    level = payload.get("level")  # filter: "error", "warning", "log", etc.
    clear = payload.get("clear", False)
    limit = int(payload.get("limit", 50))

    logs = list(console_buffer)
    if level:
        logs = [l for l in logs if l["type"] == level]

    logs = logs[-limit:]

    if clear:
        console_buffer.clear()

    return {
        "status": "success",
        "action": "console_logs",
        "count": len(logs),
        "logs": logs,
    }


def handle_download(payload):
    """List or manage downloaded files."""
    sub = payload.get("sub", "list")

    if sub == "list":
        return {
            "status": "success",
            "action": "downloads_list",
            "count": len(download_files),
            "files": download_files[-20:],
        }

    elif sub == "clear":
        download_files.clear()
        return {"status": "success", "action": "downloads_clear"}

    return {"status": "error", "message": f"Unknown sub-command: {sub}"}


# ─── Command Router ───────────────────────────────────────────────

COMMANDS = {
    "goto": handle_goto,
    "click": handle_click,
    "type": handle_type,
    "select": handle_select,
    "read": handle_read,
    "screenshot": handle_screenshot,
    "keyboard": handle_keyboard,
    "scroll": handle_scroll,
    "wait": handle_wait,
    "wait_for_change": handle_wait_for_change,
    "hover": handle_hover,
    "exec_js": handle_exec_js,
    "upload": handle_upload,
    "tabs": handle_tabs,
    "dialog": handle_dialog,
    "cookies": handle_cookies,
    "fill_form": handle_fill_form,
    "drag": handle_drag,
    "block_urls": handle_block_urls,
    "console_logs": handle_console_logs,
    "download": handle_download,
}


class BrowserHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)

        try:
            payload = json.loads(post_data)
        except json.JSONDecodeError:
            self._respond(400, {"status": "error", "message": "Invalid JSON"})
            return

        cmd = payload.get("command")
        handler = COMMANDS.get(cmd)

        if not handler:
            self._respond(200, {"status": "error", "message": f"Unknown command: {cmd}. Available: {', '.join(COMMANDS.keys())}"})
            return

        try:
            result = handler(payload)
        except Exception as e:
            result = {"status": "error", "message": str(e)}

        self._respond(200, result)

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def do_GET(self):
        """Health check endpoint."""
        self._respond(200, {"status": "ok", "commands": list(COMMANDS.keys())})


# ─── Server Startup ───────────────────────────────────────────────

def run_server():
    global playwright_instance, browser_context, current_page, all_pages

    log_err("Initializing Playwright with anti-detection measures...")
    playwright_instance = sync_playwright().start()
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # Randomize viewport slightly to avoid fingerprinting
    vw = 1280 + random.randint(-20, 20)
    vh = 800 + random.randint(-10, 10)

    browser_context = playwright_instance.chromium.launch_persistent_context(
        user_data_dir=str(USER_DATA_DIR),
        headless=False,
        viewport={"width": vw, "height": vh},
        locale="en-US",
        timezone_id="America/New_York",
        accept_downloads=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process",
            "--no-first-run",
            "--no-default-browser-check",
        ],
        ignore_default_args=["--enable-automation"],
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    )

    # Anti-detection init script
    browser_context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        if (window.chrome) {
            window.chrome.runtime = undefined;
        }
        // Patch permissions query for notifications
        const origQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                origQuery(parameters)
        );
        // Hide plugin count anomaly
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
    """)

    all_pages = list(browser_context.pages)
    current_page = all_pages[0] if all_pages else browser_context.new_page()
    if current_page not in all_pages:
        all_pages.append(current_page)

    # Set up listeners on initial page
    for page in all_pages:
        setup_page_listeners(page)

    # Listen for new pages (popups / new tabs)
    def on_new_page(page):
        setup_page_listeners(page)
        sync_pages()

    browser_context.on("page", on_new_page)

    server_address = ("", PORT)
    httpd = HTTPServer(server_address, BrowserHandler)
    log_err(f"Browser daemon ready on port {PORT}")
    log_err(f"  Viewport: {vw}x{vh}")
    log_err(f"  Commands: {', '.join(COMMANDS.keys())}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        browser_context.close()
        playwright_instance.stop()
        log_err("Daemon shut down.")


if __name__ == "__main__":
    run_server()
