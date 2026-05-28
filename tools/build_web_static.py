#!/usr/bin/env python3
"""Sync docs/mockups into src/yoruu/web/static for FastAPI serving (M4.2)."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOCKUPS = ROOT / "docs" / "mockups"
STATIC = ROOT / "src" / "yoruu" / "web" / "static"
SSE_CLIENT_SRC = ROOT / "src" / "yoruu" / "web" / "static_src" / "sse-client.js"

PAGE_FILES = [
    "00_hud.html",
    "index.html",
    "01_dashboard.html",
    "02_trade_log.html",
    "03_nightly_review.html",
    "04_settings.html",
    "05_strategy_history.html",
    "06_alerts.html",
    "07_mode_switch.html",
    "08_emergency_stop.html",
    "09_markov_live.html",
    "10_what_if.html",
]

JS_FILES = [
    "mock-data.js",
    "app.js",
    "i18n.js",
    "severity.js",
    "nightly-review.js",
    "palette.js",
    "sidebar.js",
]

MOCK_SSE_BODY = """    setTimeout(function () {
      if (eventName === "position_opened") {
        const data = getData();
        ensureRuntimeLedger(getScenarioId(), data.balance);
        applyPositionOpened(detail);
        global.document.dispatchEvent(
          new CustomEvent("balance_updated", {
            detail: getBalanceSnapshot(),
          }),
        );
      } else if (eventName === "position_closed") {
        const data = getData();
        ensureRuntimeLedger(getScenarioId(), data.balance);
        applyPositionClosed(detail);
        global.document.dispatchEvent(
          new CustomEvent("balance_updated", {
            detail: getBalanceSnapshot(),
          }),
        );
      }
      global.document.dispatchEvent(
        new CustomEvent(eventName, { detail: detail }),
      );
    }, delay);"""

DISPATCH_FN = """
  function dispatchSseEvent(eventName, detail) {
    if (eventName === "position_opened") {
      const data = getData();
      ensureRuntimeLedger(getScenarioId(), data.balance);
      applyPositionOpened(detail);
      global.document.dispatchEvent(
        new CustomEvent("balance_updated", { detail: getBalanceSnapshot() }),
      );
    } else if (eventName === "position_closed") {
      const data = getData();
      ensureRuntimeLedger(getScenarioId(), data.balance);
      applyPositionClosed(detail);
      global.document.dispatchEvent(
        new CustomEvent("balance_updated", { detail: getBalanceSnapshot() }),
      );
    }
    global.document.dispatchEvent(new CustomEvent(eventName, { detail: detail }));
  }

"""

APP_EMERGENCY_OLD = """  function triggerEmergencyStop() {
    global.YoRuuMockData.mockSSE("emergency_stop_triggered", {
      trigger: "dashboard_button",
      timestamp: new Date().toISOString(),
      open_positions_closed: 1,
    });
    global.location.href = "08_emergency_stop.html";
  }"""

APP_EMERGENCY_NEW = """  function triggerEmergencyStop() {
    if (global.YoRuuSse && global.YoRuuSse.isLive && global.YoRuuSse.isLive()) {
      global.fetch("/api/v1/emergency/stop", { method: "POST" }).catch(function () {});
      global.location.href = "/pages/08_emergency_stop.html";
      return;
    }
    global.YoRuuMockData.mockSSE("emergency_stop_triggered", {
      trigger: "dashboard_button",
      timestamp: new Date().toISOString(),
      open_positions_closed: 1,
    });
    global.location.href = "/pages/08_emergency_stop.html";
  }"""

SSE_BANNER_SNIPPET = """
  function ensureSseBanner() {
    let el = global.document.getElementById("sse-connection-banner");
    if (!el) {
      el = global.document.createElement("div");
      el.id = "sse-connection-banner";
      el.className = "health-banner hidden";
      el.setAttribute("role", "status");
      global.document.body.insertBefore(el, global.document.body.firstChild);
    }
    return el;
  }

  function setSseConnectionState(connected) {
    const el = ensureSseBanner();
    if (!global.YoRuuSse || global.YoRuuSse.useMockMode()) {
      el.classList.add("hidden");
      return;
    }
    if (connected) {
      el.classList.add("hidden");
      return;
    }
    el.classList.remove("hidden");
    el.dataset.severity = "WARN";
    el.textContent = global.YoRuuI18n
      ? global.YoRuuI18n.t("health.degraded") + ": SSE disconnected"
      : "SSE disconnected";
    global.document.body.classList.add("has-banner");
  }

  global.document.addEventListener("sse_connection_changed", function (e) {
    setSseConnectionState(e.detail && e.detail.connected);
  });

"""


def _rewrite_asset_paths(text: str) -> str:
    text = text.replace('href="shared/style.css"', 'href="/static/css/style.css"')
    for name in JS_FILES:
        text = text.replace(f'src="shared/{name}"', f'src="/static/js/{name}"')
    text = text.replace(
        'src="shared/locales/ja.bundle.js"',
        'src="/static/locales/ja.bundle.js"',
    )
    if 'src="/static/js/sse-client.js"' not in text:
        text = text.replace(
            'src="/static/js/mock-data.js"></script>',
            'src="/static/js/mock-data.js"></script>\n  <script src="/static/js/sse-client.js"></script>',
        )
    return text


def _rewrite_page_links(text: str) -> str:
    for page in PAGE_FILES:
        text = text.replace(f'href="{page}"', f'href="/pages/{page}"')
        text = text.replace(f"href='{page}'", f"href='/pages/{page}'")
        text = text.replace(f'href: "{page}"', f'href: "/pages/{page}"')
        text = text.replace(
            f'global.location.href = "{page}"',
            f'global.location.href = "/pages/{page}"',
        )
        text = text.replace(
            f'window.location.href = "{page}"',
            f'window.location.href = "/pages/{page}"',
        )
    return text


def _patch_mock_data(js: str) -> str:
    if "dispatchSseEvent" not in js:
        js = js.replace("  function mockSSE(eventName, payload, delayMs) {", DISPATCH_FN + "  function mockSSE(eventName, payload, delayMs) {")
    if MOCK_SSE_BODY in js:
        js = js.replace(
            MOCK_SSE_BODY,
            "    setTimeout(function () {\n      dispatchSseEvent(eventName, detail);\n    }, delay);",
        )
    if "dispatchSseEvent: dispatchSseEvent" not in js:
        js = js.replace("    mockSSE: mockSSE,", "    mockSSE: mockSSE,\n    dispatchSseEvent: dispatchSseEvent,")
    return js


def _patch_app_js(js: str) -> str:
    if APP_EMERGENCY_OLD in js:
        js = js.replace(APP_EMERGENCY_OLD, APP_EMERGENCY_NEW)
    if "ensureSseBanner" not in js:
        js = js.replace("  function ensureHealthBanner() {", SSE_BANNER_SNIPPET + "  function ensureHealthBanner() {")
    return js


def main() -> None:
    if STATIC.exists():
        shutil.rmtree(STATIC)
    for sub in ("pages", "js", "css", "locales"):
        (STATIC / sub).mkdir(parents=True)

    for page in PAGE_FILES:
        text = (MOCKUPS / page).read_text(encoding="utf-8")
        text = _rewrite_asset_paths(_rewrite_page_links(text))
        (STATIC / "pages" / page).write_text(text, encoding="utf-8")

    shutil.copy2(MOCKUPS / "shared" / "style.css", STATIC / "css" / "style.css")
    shutil.copy2(
        MOCKUPS / "shared" / "locales" / "ja.bundle.js",
        STATIC / "locales" / "ja.bundle.js",
    )
    shutil.copy2(SSE_CLIENT_SRC, STATIC / "js" / "sse-client.js")

    for name in JS_FILES:
        text = (MOCKUPS / "shared" / name).read_text(encoding="utf-8")
        text = _rewrite_page_links(text)
        if name == "mock-data.js":
            text = _patch_mock_data(text)
        elif name == "app.js":
            text = _patch_app_js(text)
        (STATIC / "js" / name).write_text(text, encoding="utf-8")

    print(f"OK: static assets -> {STATIC}")


if __name__ == "__main__":
    main()
