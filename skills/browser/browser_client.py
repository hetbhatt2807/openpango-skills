#!/usr/bin/env python3
"""
browser_client.py - CLI client for the browser daemon.
Sends JSON commands to localhost:9222 and prints the response.
"""
import argparse
import json
import sys
import urllib.request
import urllib.error

PORT = 9222


def send_command(payload):
    """POST a JSON command to the daemon and print the response."""
    req = urllib.request.Request(f"http://localhost:{PORT}")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(payload).encode("utf-8")
    try:
        with urllib.request.urlopen(req, data=data, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            print(json.dumps(result, indent=2))
    except urllib.error.URLError:
        print(json.dumps({
            "status": "error",
            "message": f"Could not connect to browser daemon on port {PORT}. Start it first: python3 browser_skill/browser_daemon.py &",
        }, indent=2))
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Browser Client - connects to browser daemon")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # goto
    p = subparsers.add_parser("goto", help="Navigate to a URL")
    p.add_argument("url", help="Full URL to navigate to")

    # click
    p = subparsers.add_parser("click", help="Click an element")
    p.add_argument("selector", nargs="?", default=None, help="Playwright selector")
    p.add_argument("--index", "-i", type=int, help="Click by interactive-read index number")
    p.add_argument("--double", "-d", action="store_true", help="Double-click")
    p.add_argument("--right", "-r", action="store_true", help="Right-click (context menu)")

    # type
    p = subparsers.add_parser("type", help="Type text into an element")
    p.add_argument("selector", nargs="?", default=None, help="Playwright selector")
    p.add_argument("text", help="Text to type")
    p.add_argument("--index", "-i", type=int, help="Target by interactive-read index number")
    p.add_argument("--no-clear", action="store_true", help="Don't clear existing text first")
    p.add_argument("--submit", "-s", action="store_true", help="Press Enter after typing")

    # select
    p = subparsers.add_parser("select", help="Select dropdown option")
    p.add_argument("selector", help="Playwright selector for the select element")
    p.add_argument("value", help="Label text to select")

    # read
    p = subparsers.add_parser("read", help="Read page content")
    p.add_argument("--mode", "-m", choices=["interactive", "text", "full"], default="interactive",
                   help="Output mode (default: interactive)")
    p.add_argument("--selector", help="Read only within this container")
    p.add_argument("--no-iframes", action="store_true", help="Skip iframe content extraction")

    # screenshot
    p = subparsers.add_parser("screenshot", help="Take a screenshot")
    p.add_argument("--selector", help="Screenshot only this element")
    p.add_argument("--full-page", "-f", action="store_true", help="Capture full scrollable page")

    # keyboard
    p = subparsers.add_parser("keyboard", help="Press a key or key combo")
    p.add_argument("key", help="Key to press (e.g. Enter, Tab, Escape, Control+a)")

    # scroll
    p = subparsers.add_parser("scroll", help="Scroll the page")
    p.add_argument("direction", nargs="?", default="down", choices=["up", "down"], help="Scroll direction")
    p.add_argument("amount", nargs="?", type=int, default=500, help="Pixels to scroll (default 500)")
    p.add_argument("--selector", help="Scroll to a specific element instead")

    # wait
    p = subparsers.add_parser("wait", help="Wait for an element or duration")
    p.add_argument("selector", nargs="?", default=None, help="Selector to wait for")
    p.add_argument("--state", choices=["visible", "hidden", "attached", "detached"], default="visible")
    p.add_argument("--timeout", type=int, default=10000, help="Timeout in ms (default 10000)")

    # wait_for_change
    p = subparsers.add_parser("wait_for_change", help="Wait until page content or URL changes")
    p.add_argument("--watch", choices=["url", "content", "any"], default="any",
                   help="What to watch for changes (default: any)")
    p.add_argument("--timeout", type=int, default=10000, help="Timeout in ms (default 10000)")

    # hover
    p = subparsers.add_parser("hover", help="Hover over an element")
    p.add_argument("selector", help="Playwright selector")

    # exec_js
    p = subparsers.add_parser("exec_js", help="Execute JavaScript on the page")
    p.add_argument("script", help="JavaScript code to evaluate")

    # upload
    p = subparsers.add_parser("upload", help="Upload a file to a file input")
    p.add_argument("selector", help="Playwright selector for file input")
    p.add_argument("file_path", help="Path to the file to upload")

    # tabs
    p = subparsers.add_parser("tabs", help="Manage browser tabs")
    tabs_sub = p.add_subparsers(dest="sub", required=True)
    tabs_sub.add_parser("list", help="List all open tabs")
    sp = tabs_sub.add_parser("switch", help="Switch to a tab by index")
    sp.add_argument("index", type=int)
    sp = tabs_sub.add_parser("new", help="Open a new tab")
    sp.add_argument("url", nargs="?", default="about:blank")
    sp = tabs_sub.add_parser("close", help="Close a tab by index")
    sp.add_argument("index", nargs="?", type=int, default=-1)

    # dialog
    p = subparsers.add_parser("dialog", help="Set dialog handler (accept/dismiss)")
    p.add_argument("action", choices=["accept", "dismiss"], help="What to do with the next dialog")
    p.add_argument("--text", help="Text to enter for prompt dialogs")

    # cookies
    p = subparsers.add_parser("cookies", help="Manage cookies")
    cookies_sub = p.add_subparsers(dest="sub", required=True)
    sp = cookies_sub.add_parser("list", help="List cookies")
    sp.add_argument("--domain", help="Filter by domain")
    sp = cookies_sub.add_parser("set", help="Set a cookie")
    sp.add_argument("cookie_json", help='JSON string: {"url":"...","name":"...","value":"..."}')
    cookies_sub.add_parser("clear", help="Clear all cookies")

    # fill_form
    p = subparsers.add_parser("fill_form", help="Fill multiple form fields at once")
    p.add_argument("fields_json", help='JSON dict: {"selector": "value", ...}')
    p.add_argument("--submit", "-s", action="store_true", help="Press Enter after filling")

    # drag
    p = subparsers.add_parser("drag", help="Drag an element to a target")
    p.add_argument("source", help="Playwright selector for the source element")
    p.add_argument("target", help="Playwright selector for the target element")

    # block_urls
    p = subparsers.add_parser("block_urls", help="Block network requests by URL pattern")
    block_sub = p.add_subparsers(dest="sub", required=True)
    sp = block_sub.add_parser("add", help="Add URL patterns to block")
    sp.add_argument("patterns", nargs="+", help="URL glob patterns (e.g. **/*google-analytics.com/**)")
    block_sub.add_parser("preset", help="Block common ad/tracker domains")
    block_sub.add_parser("list", help="List blocked patterns")
    block_sub.add_parser("clear", help="Remove all URL blocks")

    # console_logs
    p = subparsers.add_parser("console_logs", help="View captured browser console output")
    p.add_argument("--level", choices=["log", "error", "warning", "info", "debug"],
                   help="Filter by log level")
    p.add_argument("--clear", action="store_true", help="Clear the log buffer after reading")
    p.add_argument("--limit", type=int, default=50, help="Max entries to return (default 50)")

    # download
    p = subparsers.add_parser("download", help="Manage downloaded files")
    download_sub = p.add_subparsers(dest="sub", required=True)
    download_sub.add_parser("list", help="List downloaded files")
    download_sub.add_parser("clear", help="Clear download history")

    args = parser.parse_args()

    # Build the payload
    payload = {"command": args.command}

    if args.command == "goto":
        payload["url"] = args.url

    elif args.command == "click":
        if args.selector:
            payload["selector"] = args.selector
        if args.index is not None:
            payload["index"] = args.index
        payload["double"] = args.double
        payload["right"] = args.right

    elif args.command == "type":
        if args.selector:
            payload["selector"] = args.selector
        payload["text"] = args.text
        if args.index is not None:
            payload["index"] = args.index
        payload["clear"] = not args.no_clear
        payload["submit"] = args.submit

    elif args.command == "select":
        payload["selector"] = args.selector
        payload["value"] = args.value

    elif args.command == "read":
        payload["mode"] = args.mode
        if args.selector:
            payload["selector"] = args.selector
        payload["iframes"] = not args.no_iframes

    elif args.command == "screenshot":
        if args.selector:
            payload["selector"] = args.selector
        payload["full_page"] = args.full_page

    elif args.command == "keyboard":
        payload["key"] = args.key

    elif args.command == "scroll":
        if args.selector:
            payload["selector"] = args.selector
        else:
            payload["direction"] = args.direction
            payload["amount"] = args.amount

    elif args.command == "wait":
        if args.selector:
            payload["selector"] = args.selector
        payload["state"] = args.state
        payload["timeout"] = args.timeout

    elif args.command == "wait_for_change":
        payload["watch"] = args.watch
        payload["timeout"] = args.timeout

    elif args.command == "hover":
        payload["selector"] = args.selector

    elif args.command == "exec_js":
        payload["script"] = args.script

    elif args.command == "upload":
        payload["selector"] = args.selector
        payload["file_path"] = args.file_path

    elif args.command == "tabs":
        payload["sub"] = args.sub
        if args.sub == "switch":
            payload["index"] = args.index
        elif args.sub == "new":
            payload["url"] = args.url
        elif args.sub == "close":
            payload["index"] = args.index

    elif args.command == "dialog":
        payload["action"] = args.action
        if args.text:
            payload["text"] = args.text

    elif args.command == "cookies":
        payload["sub"] = args.sub
        if args.sub == "list" and hasattr(args, "domain") and args.domain:
            payload["domain"] = args.domain
        elif args.sub == "set":
            payload["cookie"] = json.loads(args.cookie_json)

    elif args.command == "fill_form":
        payload["fields"] = json.loads(args.fields_json)
        payload["submit"] = args.submit

    elif args.command == "drag":
        payload["source"] = args.source
        payload["target"] = args.target

    elif args.command == "block_urls":
        payload["sub"] = args.sub
        if args.sub == "add":
            payload["patterns"] = args.patterns

    elif args.command == "console_logs":
        if args.level:
            payload["level"] = args.level
        payload["clear"] = args.clear
        payload["limit"] = args.limit

    elif args.command == "download":
        payload["sub"] = args.sub

    send_command(payload)


if __name__ == "__main__":
    main()
