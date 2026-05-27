/**
 * 夜間レビュー — 提案 JSON 検証・差分プレビュー（§15.6 / §15.7、モック用）
 */
(function (global) {
  "use strict";

  const PARAM_KEYS = [
    "MIN_PROB",
    "MIN_EDGE",
    "KELLY_FRACTION",
    "PERSISTENCE_THRESHOLD",
  ];

  const FORBIDDEN_TOP = [
    "version",
    "metadata",
    "constraints",
    "mode",
    "risk",
    "websocket",
    "daily_loss_limit_usd",
  ];

  /**
   * §15.5.2 プロンプト雛形 + レポート JSON
   * @param {object} report
   * @returns {string}
   */
  function buildPromptText(report) {
    const header =
      "あなたは Polymarket BTC 5 分 Up/Down 予測 Bot YoRuu の戦略チューナーです。\n" +
      "以下の日次レポートを読み、Markov + Kelly 戦略のパラメータを微調整してください。\n\n" +
      "# 制約\n" +
      "- 出力は JSON のみ。説明文・前置きは不要\n" +
      "- 提案できるキーは MIN_PROB / MIN_EDGE / KELLY_FRACTION / PERSISTENCE_THRESHOLD の 4 つのみ\n" +
      "- 各値は report.constraints の min / max 範囲内に収めること\n" +
      "- 現行値からの変化率は ±20% 以内を推奨（±10% 超は警告対象、±20% 超は原則拒否される）\n" +
      "- 取引数が 20 件未満の日は変更幅を半分以下に抑え、重大変更は避ける\n" +
      "- 必ず 4 キー全てを含めること（変更不要なキーは現行値をそのまま記載）\n\n" +
      "# 出力フォーマット\n" +
      "{\n" +
      '  "parameters": {\n' +
      '    "MIN_PROB": <float>,\n' +
      '    "MIN_EDGE": <float>,\n' +
      '    "KELLY_FRACTION": <float>,\n' +
      '    "PERSISTENCE_THRESHOLD": <float>\n' +
      "  },\n" +
      '  "rationale": "<日本語 200 字以内、変更理由の要約>"\n' +
      "}\n\n" +
      "# 日次レポート\n";
    return header + JSON.stringify(report, null, 2);
  }

  /**
   * @param {string} raw
   * @returns {{ ok: boolean, data?: object, error?: string }}
   */
  function parseProposal(raw) {
    try {
      const data = JSON.parse(raw);
      if (!data || typeof data !== "object") {
        return { ok: false, error: "E_PARSE" };
      }
      return { ok: true, data: data };
    } catch (e) {
      return { ok: false, error: "E_PARSE: " + (e && e.message ? e.message : "invalid") };
    }
  }

  /**
   * @param {object} proposed
   * @returns {string[]}
   */
  function findForbiddenKeys(proposed) {
    const errors = [];
    Object.keys(proposed).forEach(function (k) {
      if (FORBIDDEN_TOP.indexOf(k) >= 0) {
        errors.push("E_NIGHTLY_006:" + k);
      }
      if (k.indexOf("risk.") === 0 || k === "constraints") {
        errors.push("E_NIGHTLY_006:" + k);
      }
    });
    if (proposed.constraints) {
      errors.push("E_NIGHTLY_005");
    }
    return errors;
  }

  /**
   * @param {object} report §15.4.8
   * @param {object} proposed §15.6.1
   * @returns {object} preview-apply 形
   */
  function computeDiffPreview(report, proposed) {
    const errors = [];
    const warnings = [];
    const forbidden = findForbiddenKeys(proposed);
    forbidden.forEach(function (e) {
      errors.push(e);
    });

    const params = proposed.parameters;
    if (!params || typeof params !== "object") {
      errors.push("E_NIGHTLY_009:parameters");
      return {
        ok: false,
        apply_enabled: false,
        diff: [],
        errors: errors,
        warnings: warnings,
      };
    }

    const current = report.current_strategy.parameters;
    const constraints = report.constraints;
    const diff = [];

    PARAM_KEYS.forEach(function (key) {
      if (params[key] === undefined || params[key] === null) {
        errors.push("E_NIGHTLY_009:" + key);
        return;
      }
      const oldVal = current[key];
      const newVal = Number(params[key]);
      if (Number.isNaN(newVal)) {
        errors.push("E_NIGHTLY_009:" + key);
        return;
      }
      const c = constraints[key];
      const inRange =
        c && newVal >= c.min && newVal <= c.max;
      if (!inRange) {
        errors.push("E_NIGHTLY_007:" + key);
      }
      const delta = newVal - oldVal;
      const deltaPct =
        oldVal === 0 ? (delta === 0 ? 0 : 100) : Math.abs((delta / oldVal) * 100);
      const unchanged = Math.abs(delta) < 1e-9;
      let warnLarge = false;
      if (!unchanged && deltaPct > 10) {
        warnLarge = true;
        warnings.push("W_NIGHTLY_001:" + key);
      }
      if (!unchanged && deltaPct > 20) {
        errors.push("E_NIGHTLY_008:" + key);
      }
      diff.push({
        key: key,
        old: oldVal,
        new: newVal,
        delta: Math.round(delta * 1000) / 1000,
        delta_pct: Math.round(deltaPct * 100) / 100,
        in_range: inRange,
        warn_large_change: warnLarge,
        unchanged: unchanged,
      });
    });

    const applyEnabled =
      errors.length === 0 &&
      diff.length === PARAM_KEYS.length &&
      diff.every(function (d) {
        return d.in_range && d.delta_pct <= 20;
      });

    return {
      ok: errors.length === 0,
      apply_enabled: applyEnabled,
      current_version: report.current_strategy.version,
      diff: diff,
      errors: errors,
      warnings: warnings,
    };
  }

  global.YoRuuNightlyReview = {
    PARAM_KEYS: PARAM_KEYS,
    buildPromptText: buildPromptText,
    parseProposal: parseProposal,
    computeDiffPreview: computeDiffPreview,
  };
})(typeof window !== "undefined" ? window : globalThis);
