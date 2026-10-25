"""Capture the real dbt Docs page using an installed Chrome and Playwright."""
import functools
import http.server
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright


root = Path(__file__).resolve().parents[1]
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root / 'dbt/target'))
server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={'width': 1600, 'height': 1100}, device_scale_factor=1)
        page.goto(f'http://127.0.0.1:{server.server_port}/#!/model/model.fraud_analytics.stg_transactions')
        page.wait_for_load_state('networkidle')
        page.wait_for_function("document.body.innerText.includes('stg_transactions')")
        page.screenshot(path=str(root / 'artifacts/dbt_docs.png'), full_page=True)
        page.get_by_title('View Lineage Graph', exact=True).click()
        page.get_by_title('View Fullscreen', exact=True).locator('visible=true').click()
        page.wait_for_function("document.querySelectorAll('canvas').length > 0")
        page.wait_for_timeout(1500)  # Allow the graph layout and labels to settle.
        page.screenshot(path=str(root / 'artifacts/dbt_dag.png'))
        print('Saved artifacts/dbt_docs.png and artifacts/dbt_dag.png')
        browser.close()
finally:
    server.shutdown()
