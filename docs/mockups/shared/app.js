/**
 * YoRuu mock app shell — health banner, help modal, emergency stop, SSE hooks.
 */
(function (global) {
  "use strict";

  let helpBackdrop = null;

  function ensureHealthBanner() {
    let el = global.document.getElementById("health-banner");
    if (!el) {
      el = global.document.createElement("div");
      el.id = "health-banner";
      el.className = "health-banner hidden";
      el.setAttribute("role", "alert");
      el.setAttribute("aria-live", "polite");
      global.document.body.insertBefore(el, global.document.body.firstChild);
    }
    return el;
  }

  function refreshHealthBanner() {
    const data = global.YoRuuMockData.getData();
    const banner = ensureHealthBanner();
    if (!data.health || !data.health.degraded) {
      banner.classList.add("hidden");
      global.document.body.classList.remove("has-banner");
      return;
    }
    banner.classList.remove("hidden");
    banner.dataset.severity = data.health.severity || "warn";
    banner.textContent =
      global.YoRuuI18n.t("health.degraded") + ": " + data.health.message;
    global.document.body.classList.add("has-banner");
  }

  function triggerEmergencyStop() {
    global.YoRuuMockData.mockSSE("emergency_stop_triggered", {
      trigger: "dashboard_button",
      timestamp: new Date().toISOString(),
      open_positions_closed: 1,
    });
    global.location.href = "08_emergency_stop.html";
  }

  function ensureHelpModal() {
    if (helpBackdrop) {
      return helpBackdrop;
    }
    const i18n = global.YoRuuI18n;
    helpBackdrop = global.document.createElement("div");
    helpBackdrop.className = "modal-backdrop hidden";
    helpBackdrop.id = "help-modal-backdrop";
    helpBackdrop.innerHTML =
      '<div class="modal" role="dialog" aria-modal="true" aria-labelledby="help-modal-title">' +
      '<div class="modal-header">' +
      '<h2 id="help-modal-title" data-i18n="help.shortcuts_title"></h2>' +
      '<button type="button" class="btn btn-sm" id="help-modal-close" data-i18n="action.close"></button>' +
      "</div>" +
      '<div class="modal-body">' +
      "<table class=\"shortcut-table\">" +
      "<tr><td><kbd>⌘/Ctrl</kbd> + <kbd>K</kbd></td><td data-i18n=\"help.shortcut.cmd_k\"></td></tr>" +
      "<tr><td><kbd>?</kbd></td><td data-i18n=\"help.shortcut.question\"></td></tr>" +
      "<tr><td><kbd>g</kbd> <kbd>d</kbd></td><td data-i18n=\"help.shortcut.go_dashboard\"></td></tr>" +
      "<tr><td><kbd>g</kbd> <kbd>l</kbd></td><td data-i18n=\"help.shortcut.go_trade_log\"></td></tr>" +
      "<tr><td><kbd>Esc</kbd></td><td data-i18n=\"help.shortcut.esc\"></td></tr>" +
      "</table></div></div>";
    global.document.body.appendChild(helpBackdrop);
    helpBackdrop.addEventListener("click", function (e) {
      if (e.target === helpBackdrop) {
        closeHelp();
      }
    });
    helpBackdrop
      .querySelector("#help-modal-close")
      .addEventListener("click", closeHelp);
    i18n.applyI18n(helpBackdrop);
    return helpBackdrop;
  }

  function openHelp() {
    const modal = ensureHelpModal();
    modal.classList.remove("hidden");
    global.YoRuuI18n.applyI18n(modal);
  }

  function closeHelp() {
    if (helpBackdrop) {
      helpBackdrop.classList.add("hidden");
    }
    global.YoRuuPalette.closePalette();
  }

  function bindLangToggle(btnId) {
    const btn = global.document.getElementById(btnId);
    if (!btn) {
      return;
    }
    function refreshLabel() {
      const lang = global.YoRuuI18n.getLang();
      btn.setAttribute(
        "data-i18n",
        lang === "ja" ? "lang.switch" : "lang.switch_back",
      );
      global.YoRuuI18n.applyI18n(btn.parentElement || btn);
    }
    btn.addEventListener("click", function () {
      global.YoRuuI18n.toggleLanguage();
      refreshLabel();
    });
    global.document.addEventListener("language_changed", refreshLabel);
    refreshLabel();
  }

  function bindScenarioSelect(selectId) {
    const sel = global.document.getElementById(selectId);
    if (!sel) {
      return;
    }
    sel.value = global.YoRuuMockData.getScenarioId();
    sel.addEventListener("change", function () {
      global.YoRuuMockData.setScenario(sel.value);
      global.location.reload();
    });
  }

  function bindEmergencyButtons(selector) {
    global.document.querySelectorAll(selector).forEach(function (btn) {
      btn.addEventListener("click", function () {
        triggerEmergencyStop();
      });
    });
  }

  function updateModeBadges() {
    const data = global.YoRuuMockData.getData();
    const mode = data.bot_state.mode;
    const i18n = global.YoRuuI18n;
    global.document.querySelectorAll(".mode-badge").forEach(function (el) {
      el.dataset.mode = mode;
      const upper = i18n.t(i18n.modeUpperKey(mode));
      if (el.classList.contains("mode-badge-header")) {
        el.textContent = upper;
      }
    });
    global.document.querySelectorAll("[data-mode-label]").forEach(function (el) {
      el.textContent = i18n.t(i18n.modeUpperKey(mode));
    });
  }

  function initApp(options) {
    options = options || {};
    global.YoRuuI18n.initI18n();
    global.YoRuuPalette.initPalette();

    if (options.sidebar) {
      const aside = global.document.getElementById("sidebar");
      if (aside) {
        global.YoRuuSidebar.renderSidebar(aside, options.activePage);
      }
    }

    refreshHealthBanner();
    updateModeBadges();
    bindLangToggle(options.langToggleId || "lang-toggle");
    bindScenarioSelect(options.scenarioSelectId || "scenario-select");
    bindEmergencyButtons(options.emergencySelector || ".fab-emergency, .hub-emergency-btn");

    global.document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        closeHelp();
      }
    });

    global.document.addEventListener("scenario_changed", function () {
      refreshHealthBanner();
      updateModeBadges();
      if (options.sidebar) {
        global.YoRuuSidebar.updateSidebarStatus();
      }
    });

    global.document.addEventListener("health_degraded", function (e) {
      const banner = ensureHealthBanner();
      banner.classList.remove("hidden");
      banner.dataset.severity = "warn";
      banner.textContent = e.detail && e.detail.message ? e.detail.message : "degraded";
      global.document.body.classList.add("has-banner");
    });

    global.document.addEventListener("health_recovered", function () {
      refreshHealthBanner();
    });

    global.document.addEventListener("language_changed", function () {
      if (options.sidebar) {
        global.YoRuuSidebar.updateSidebarStatus();
      }
      updateModeBadges();
    });

    ["position_opened", "position_closed", "balance_updated"].forEach(function (ev) {
      global.document.addEventListener(ev, function () {
        if (options.onBalanceChange) {
          options.onBalanceChange();
        }
      });
    });
  }

  global.YoRuuApp = {
    initApp: initApp,
    triggerEmergencyStop: triggerEmergencyStop,
    openHelp: openHelp,
    closeHelp: closeHelp,
    refreshHealthBanner: refreshHealthBanner,
    updateModeBadges: updateModeBadges,
  };
})(typeof window !== "undefined" ? window : globalThis);
