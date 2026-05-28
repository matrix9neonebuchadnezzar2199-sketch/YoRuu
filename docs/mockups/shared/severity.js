/**
 * Severity helpers — exact match only (ch08 §8.4.3, no prefix matching).
 */
(function (global) {
  "use strict";

  function isSeverity(value, expected) {
    return value === expected;
  }

  function cssClassForSeverity(severity) {
    if (severity === "ERROR" || severity === "CRITICAL") {
      return "severity-error";
    }
    if (severity === "WARN") {
      return "severity-warn";
    }
    if (severity === "INFO") {
      return "severity-info";
    }
    return "";
  }

  global.YoRuuSeverity = {
    isSeverity: isSeverity,
    cssClassForSeverity: cssClassForSeverity,
  };
})(typeof window !== "undefined" ? window : globalThis);
