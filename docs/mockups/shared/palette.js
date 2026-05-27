/**
 * YoRuu command palette — §8.7 (palette.js)
 */
(function (global) {
  "use strict";

  const COMMANDS = [
    { id: "hub", key: "cmd.goto_hub", href: "index.html", keys: [] },
    {
      id: "dashboard",
      key: "cmd.goto_dashboard",
      href: "01_dashboard.html",
      keys: ["g", "d"],
    },
    {
      id: "trade_log",
      key: "cmd.goto_trade_log",
      href: "02_trade_log.html",
      keys: ["g", "l"],
    },
    {
      id: "nightly",
      key: "cmd.goto_nightly_review",
      href: "03_nightly_review.html",
      keys: ["g", "r"],
    },
    {
      id: "settings",
      key: "cmd.goto_settings",
      href: "04_settings.html",
      keys: ["g", "s"],
    },
    {
      id: "strategy",
      key: "cmd.goto_strategy_history",
      href: "05_strategy_history.html",
      keys: ["g", "h"],
    },
    {
      id: "markov",
      key: "cmd.goto_markov_live",
      href: "09_markov_live.html",
      keys: ["g", "m"],
    },
    {
      id: "whatif",
      key: "cmd.goto_what_if",
      href: "10_what_if.html",
      keys: ["g", "w"],
    },
    {
      id: "alerts",
      key: "cmd.goto_alerts",
      href: "06_alerts.html",
      keys: ["g", "a"],
    },
    {
      id: "mode",
      key: "cmd.goto_mode_switch",
      href: "07_mode_switch.html",
      keys: ["g", "x"],
    },
    { id: "lang", key: "cmd.switch_lang", action: "lang", keys: [] },
    { id: "help", key: "cmd.show_help", action: "help", keys: [] },
    {
      id: "stop",
      key: "cmd.emergency_stop",
      action: "emergency",
      keys: [],
      exactOnly: true,
    },
  ];

  let backdropEl = null;
  let inputEl = null;
  let listEl = null;
  let selectedIndex = 0;
  let filtered = [];
  let gSequencePending = false;
  let gSequenceTimer = null;

  function ensureDom() {
    if (backdropEl) {
      return;
    }
    backdropEl = global.document.createElement("div");
    backdropEl.className = "cmd-palette-backdrop hidden";
    backdropEl.id = "cmd-palette-backdrop";
    backdropEl.innerHTML =
      '<div class="cmd-palette" role="dialog" aria-modal="true" ' +
      'aria-labelledby="cmd-palette-label">' +
      '<label id="cmd-palette-label" class="sr-only">Command palette</label>' +
      '<input type="text" id="cmd-palette-input" autocomplete="off" />' +
      '<ul class="cmd-results" id="cmd-palette-results" role="listbox"></ul>' +
      "</div>";
    global.document.body.appendChild(backdropEl);

    inputEl = backdropEl.querySelector("#cmd-palette-input");
    listEl = backdropEl.querySelector("#cmd-palette-results");

    backdropEl.addEventListener("click", function (e) {
      if (e.target === backdropEl) {
        closePalette();
      }
    });

    inputEl.addEventListener("input", function () {
      renderResults(inputEl.value);
    });

    inputEl.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        selectedIndex = Math.min(selectedIndex + 1, filtered.length - 1);
        highlightSelection();
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        selectedIndex = Math.max(selectedIndex - 1, 0);
        highlightSelection();
      } else if (e.key === "Enter") {
        e.preventDefault();
        runSelected();
      } else if (e.key === "Escape") {
        e.preventDefault();
        closePalette();
      }
    });
  }

  function filterCommands(query) {
    const q = (query || "").trim().toLowerCase();
    if (!q) {
      return COMMANDS.slice();
    }
    const i18n = global.YoRuuI18n;
    return COMMANDS.filter(function (cmd) {
      if (cmd.id === "stop") {
        return false;
      }
      const label = i18n.t(cmd.key).toLowerCase();
      const id = cmd.id.toLowerCase();
      return label.indexOf(q) >= 0 || id.indexOf(q) >= 0;
    });
  }

  function renderResults(query) {
    const i18n = global.YoRuuI18n;
    filtered = filterCommands(query);
    selectedIndex = 0;
    listEl.innerHTML = "";
    filtered.forEach(function (cmd, idx) {
      const li = global.document.createElement("li");
      const btn = global.document.createElement("button");
      btn.type = "button";
      btn.setAttribute("role", "option");
      btn.textContent = i18n.t(cmd.key);
      if (cmd.keys && cmd.keys.length) {
        const meta = global.document.createElement("span");
        meta.className = "cmd-meta";
        meta.textContent = cmd.keys.join(" ");
        btn.appendChild(meta);
      }
      btn.addEventListener("click", function () {
        selectedIndex = idx;
        runSelected();
      });
      li.appendChild(btn);
      listEl.appendChild(li);
    });
    highlightSelection();
    inputEl.placeholder = i18n.t("cmd.palette_placeholder");
  }

  function highlightSelection() {
    const buttons = listEl.querySelectorAll("button");
    buttons.forEach(function (btn, i) {
      btn.setAttribute("aria-selected", i === selectedIndex ? "true" : "false");
    });
  }

  function runSelected() {
    const cmd = filtered[selectedIndex];
    if (!cmd) {
      return;
    }
    closePalette();
    if (cmd.action === "lang") {
      global.YoRuuI18n.toggleLanguage();
      return;
    }
    if (cmd.action === "help") {
      global.YoRuuApp.openHelp();
      return;
    }
    if (cmd.action === "emergency") {
      global.YoRuuApp.triggerEmergencyStop();
      return;
    }
    if (cmd.href) {
      global.location.href = cmd.href;
    }
  }

  function openPalette() {
    ensureDom();
    backdropEl.classList.remove("hidden");
    inputEl.value = "";
    renderResults("");
    setTimeout(function () {
      inputEl.focus();
    }, 0);
  }

  function closePalette() {
    if (backdropEl) {
      backdropEl.classList.add("hidden");
    }
  }

  function isOpen() {
    return backdropEl && !backdropEl.classList.contains("hidden");
  }

  function handleGoSequence(key) {
    const match = COMMANDS.find(function (c) {
      return c.keys && c.keys[0] === "g" && c.keys[1] === key;
    });
    if (match && match.href) {
      global.location.href = match.href;
    }
  }

  function onGlobalKeydown(e) {
    const tag = (e.target && e.target.tagName) || "";
    const inField =
      tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";

    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      if (isOpen()) {
        closePalette();
      } else {
        openPalette();
      }
      return;
    }

    if (isOpen()) {
      return;
    }

    if (e.key === "?" && !inField) {
      e.preventDefault();
      global.YoRuuApp.openHelp();
      return;
    }

    if (e.key === "g" && !inField && !e.metaKey && !e.ctrlKey) {
      gSequencePending = true;
      clearTimeout(gSequenceTimer);
      gSequenceTimer = setTimeout(function () {
        gSequencePending = false;
      }, 1000);
      return;
    }

    if (gSequencePending && !inField) {
      gSequencePending = false;
      clearTimeout(gSequenceTimer);
      handleGoSequence(e.key.toLowerCase());
    }
  }

  function initPalette() {
    ensureDom();
    global.document.addEventListener("keydown", onGlobalKeydown);
  }

  global.YoRuuPalette = {
    initPalette: initPalette,
    openPalette: openPalette,
    closePalette: closePalette,
  };
})(typeof window !== "undefined" ? window : globalThis);
