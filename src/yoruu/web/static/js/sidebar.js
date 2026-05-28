/**
 * YoRuu mock sidebar — §8.6
 */
(function (global) {
  "use strict";

  const NAV_ITEMS = [
    { key: "nav.dashboard", href: "/pages/01_dashboard.html", page: "dashboard" },
    { key: "nav.trade_log", href: "/pages/02_trade_log.html", page: "trade_log" },
    {
      key: "nav.nightly_review",
      href: "/pages/03_nightly_review.html",
      page: "nightly_review",
      badge: "nightly",
    },
    {
      key: "nav.strategy_history",
      href: "/pages/05_strategy_history.html",
      page: "strategy_history",
    },
    { key: "nav.markov_live", href: "/pages/09_markov_live.html", page: "markov_live" },
    { key: "nav.what_if", href: "/pages/10_what_if.html", page: "what_if" },
    { key: "nav.settings", href: "/pages/04_settings.html", page: "settings" },
    {
      key: "nav.alerts",
      href: "/pages/06_alerts.html",
      page: "alerts",
      badge: "alerts",
    },
    { key: "nav.mode_switch", href: "/pages/07_mode_switch.html", page: "mode_switch" },
  ];

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderSidebar(container, activePage) {
    const data = global.YoRuuMockData.getData();
    const i18n = global.YoRuuI18n;
    const mode = data.bot_state.mode;
    const stateLabel = i18n.t(i18n.stateKeyForBot(data.bot_state.state));

    let navHtml = '<ul role="list">';
    navHtml +=
      '<li><a href="/pages/07_mode_switch.html" class="mode-nav-link">' +
      '<span class="mode-badge" data-mode="' +
      escapeHtml(mode) +
      '">' +
      escapeHtml(i18n.t("mode." + mode)) +
      "</span></a></li>";

    NAV_ITEMS.forEach(function (item) {
      const current =
        item.page === activePage ? ' aria-current="page"' : "";
      let badge = "";
      if (item.badge === "nightly" && data.hub_meta.nightly_unread) {
        badge =
          '<span class="nav-badge" data-i18n="nightly.unconsumed"></span>';
      }
      if (item.badge === "alerts" && data.hub_meta.alert_unread > 0) {
        badge =
          '<span class="nav-badge">' +
          escapeHtml(
            i18n.t("alert.unread_count", null, {
              count: data.hub_meta.alert_unread,
            }),
          ) +
          "</span>";
      }
      navHtml +=
        "<li><a href=\"" +
        item.href +
        "\"" +
        current +
        ' data-i18n="' +
        item.key +
        '"></a>' +
        badge +
        "</li>";
    });
    navHtml += "</ul>";

    container.innerHTML =
      '<div class="sidebar-brand"><a href="/pages/index.html" data-i18n="nav.hub">YoRuu</a></div>' +
      '<nav class="sidebar-nav" role="navigation" aria-label="' +
      escapeHtml(i18n.t("a11y.main_nav")) +
      '">' +
      navHtml +
      "</nav>" +
      '<dl class="sidebar-status" aria-live="polite">' +
      "<dt data-i18n=\"sidebar.status.state\"></dt>" +
      '<dd id="sidebar-state">' +
      escapeHtml(stateLabel) +
      "</dd>" +
      "<dt data-i18n=\"sidebar.status.ws\"></dt>" +
      '<dd id="sidebar-ws">' +
      escapeHtml(data.ws_status) +
      "</dd>" +
      "<dt data-i18n=\"sidebar.status.last_trade\"></dt>" +
      '<dd id="sidebar-last-trade">' +
      escapeHtml(data.last_trade_at.slice(11, 19)) +
      "</dd>" +
      "</dl>" +
      '<div class="sidebar-emergency">' +
      '<button type="button" class="btn-emergency-sidebar" id="sidebar-emergency-btn" ' +
      'data-i18n="action.emergency_stop" ' +
      'aria-label="' +
      escapeHtml(i18n.t("a11y.emergency_stop_label")) +
      '"></button>' +
      "</div>";

    i18n.applyI18n(container);

    const emergBtn = container.querySelector("#sidebar-emergency-btn");
    if (emergBtn) {
      emergBtn.addEventListener("click", function () {
        global.YoRuuApp.triggerEmergencyStop();
      });
    }
  }

  function updateSidebarStatus() {
    const data = global.YoRuuMockData.getData();
    const i18n = global.YoRuuI18n;
    const stateEl = global.document.getElementById("sidebar-state");
    const wsEl = global.document.getElementById("sidebar-ws");
    const lastEl = global.document.getElementById("sidebar-last-trade");
    if (stateEl) {
      stateEl.textContent = i18n.t(
        i18n.stateKeyForBot(data.bot_state.state),
      );
    }
    if (wsEl) {
      wsEl.textContent = data.ws_status;
    }
    if (lastEl) {
      lastEl.textContent = data.last_trade_at.slice(11, 19);
    }
  }

  global.YoRuuSidebar = {
    renderSidebar: renderSidebar,
    updateSidebarStatus: updateSidebarStatus,
  };
})(typeof window !== "undefined" ? window : globalThis);
