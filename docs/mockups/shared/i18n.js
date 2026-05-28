/**
 * YoRuu mock i18n — t(), switchLanguage(), data-i18n (§8.8, ch14).
 */
(function (global) {
  "use strict";

  const STORAGE_KEY = "yoruu_mock_lang";
  let currentLang = "ja";

  function getDict(lang) {
    const locales = global.YORUU_LOCALES || {};
    return locales[lang] || {};
  }

  /**
   * Resolve translation with optional {var} interpolation.
   * @param {string} key
   * @param {string} [lang]
   * @param {Record<string, string|number>} [vars]
   * @returns {string}
   */
  function t(key, lang, vars) {
    const lg = lang || currentLang;
    const jaDict = getDict("ja");
    const enDict = getDict("en");
    let text;
    if (lg === "ja") {
      if (Object.prototype.hasOwnProperty.call(jaDict, key)) {
        text = jaDict[key];
      } else if (Object.prototype.hasOwnProperty.call(enDict, key)) {
        console.warn("[YoRuu i18n] en fallback for key:", key);
        text = enDict[key];
      } else {
        text = key;
      }
    } else if (Object.prototype.hasOwnProperty.call(enDict, key)) {
      text = enDict[key];
    } else if (Object.prototype.hasOwnProperty.call(jaDict, key)) {
      text = jaDict[key];
    } else {
      text = key;
    }

    if (vars && typeof text === "string") {
      Object.keys(vars).forEach(function (k) {
        text = text.replace(
          new RegExp("\\{" + k + "\\}", "g"),
          String(vars[k]),
        );
      });
    }
    return text;
  }

  function getLang() {
    return currentLang;
  }

  function switchLanguage(lang) {
    currentLang = lang === "en" ? "en" : "ja";
    try {
      global.localStorage.setItem(STORAGE_KEY, currentLang);
    } catch (_e) {
      /* private mode */
    }
    applyI18n();
    global.document.documentElement.lang = currentLang;
    global.dispatchEvent(
      new CustomEvent("language_changed", { detail: { lang: currentLang } }),
    );
  }

  function toggleLanguage() {
    switchLanguage(currentLang === "ja" ? "en" : "ja");
  }

  function applyI18n(root) {
    const scope = root || global.document;
    scope.querySelectorAll("[data-i18n]").forEach(function (el) {
      const key = el.getAttribute("data-i18n");
      if (!key) {
        return;
      }
      const varsRaw = el.getAttribute("data-i18n-vars");
      let vars = null;
      if (varsRaw) {
        try {
          vars = JSON.parse(varsRaw);
        } catch (_e) {
          vars = null;
        }
      }
      const text = t(key, currentLang, vars);
      const attr = el.getAttribute("data-i18n-attr");
      if (attr) {
        el.setAttribute(attr, text);
      } else if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
        if (el.getAttribute("data-i18n-target") === "placeholder") {
          el.placeholder = text;
        } else {
          el.value = text;
        }
      } else {
        el.textContent = text;
      }
    });
  }

  function stateKeyForBot(state) {
    const map = {
      TRADING: "state.trading.short",
      IDLE: "state.idle.short",
      INITIALIZING: "state.initializing.short",
      MONITORING_POSITION: "state.monitoring_position.short",
      NIGHTLY_REVIEW: "state.nightly_review.short",
      EMERGENCY_STOP: "state.emergency_stop.short",
      ERROR: "state.error.short",
      SHUTDOWN: "state.shutdown.short",
      BACKTEST: "state.backtest.short",
    };
    return map[state] || "state.idle.short";
  }

  function modeUpperKey(mode) {
    return "mode." + (mode || "paper") + ".upper";
  }

  function initI18n() {
    try {
      const saved = global.localStorage.getItem(STORAGE_KEY);
      if (saved === "en" || saved === "ja") {
        currentLang = saved;
      }
    } catch (_e) {
      /* ignore */
    }
    global.document.documentElement.lang = currentLang;
    applyI18n();
  }

  global.YoRuuI18n = {
    t: t,
    getLang: getLang,
    switchLanguage: switchLanguage,
    toggleLanguage: toggleLanguage,
    applyI18n: applyI18n,
    stateKeyForBot: stateKeyForBot,
    modeUpperKey: modeUpperKey,
    initI18n: initI18n,
  };
})(typeof window !== "undefined" ? window : globalThis);
