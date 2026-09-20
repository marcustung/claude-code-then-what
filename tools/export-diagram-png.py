from playwright.sync_api import sync_playwright
import sys, pathlib
src, out = sys.argv[1], sys.argv[2]
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 2
vw = int(sys.argv[4]) if len(sys.argv) > 4 else 1280  # viewport width; widen for maps wider than 1280 so the scroll container does not clip
sel = sys.argv[5] if len(sys.argv) > 5 else 'svg'  # element to capture (default: first svg)
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(device_scale_factor=scale, viewport={'width': vw, 'height': 900})
    page.goto(pathlib.Path(src).resolve().as_uri())
    page.wait_for_load_state("networkidle")
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(800)
    page.locator(sel).first.screenshot(path=out, omit_background=True)
    browser.close()
print("wrote", out)
