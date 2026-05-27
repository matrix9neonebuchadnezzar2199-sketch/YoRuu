/**
 * YoRuu mock data — fixed scenarios (§8.23, §8.25.1 M2.1).
 * BASE_TIME: 2026-05-27T14:32:00+09:00
 */
(function (global) {
  "use strict";

  const BASE_TIME = new Date("2026-05-27T14:32:00+09:00");

  function parseScenarioFromUrl() {
    try {
      const params = new URLSearchParams(global.location.search);
      const s = params.get("scenario");
      if (s && SCENARIOS[s]) {
        return s;
      }
    } catch (_e) {
      /* file:// may lack search; ignore */
    }
    return CURRENT_SCENARIO;
  }

  function buildTrades(count, winRate, basePnl) {
    const trades = [];
    const sides = ["YES", "NO"];
    for (let i = 0; i < count; i += 1) {
      const minsAgo = i * 5 + 2;
      const closed = new Date(BASE_TIME.getTime() - minsAgo * 60 * 1000);
      const won = i % Math.round(1 / winRate) !== 1;
      const pnl = won ? basePnl * (0.6 + (i % 5) * 0.1) : -basePnl * (0.5 + (i % 3) * 0.15);
      trades.push({
        trade_id: `T-${String(1000 + count - i).padStart(4, "0")}`,
        opened_at: new Date(closed.getTime() - 4 * 60 * 1000).toISOString(),
        closed_at: closed.toISOString(),
        time_display: closed.toLocaleTimeString("ja-JP", {
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
        }),
        side: sides[i % 2],
        size_usd: 5 + (i % 6),
        entry_price: 0.55 + (i % 10) * 0.01,
        exit_price: won ? 0.62 + (i % 5) * 0.01 : 0.48,
        result: won ? "WON" : "LOST",
        pnl_usd: Math.round(pnl * 100) / 100,
        strategy_version: `v1.${2 + (i % 3)}.${i % 5}`,
        mode: "paper",
      });
    }
    return trades;
  }

  const normalTrades = buildTrades(58, 0.543, 1.1);

  const SCENARIOS = {
    normal: {
      bot_state: { state: "TRADING", mode: "paper" },
      balance: { current: 1042.18, initial: 1000.0 },
      daily_pnl: { value: 8.42, percent: 0.84 },
      cumulative_pnl: { value: 42.18, percent: 4.22 },
      win_rate: { value: 0.543, wins: 38, losses: 32, display: "54.3%" },
      ws_status: "connected",
      last_trade_at: "2026-05-27T14:32:00+09:00",
      current_position: {
        side: "YES",
        size: 7.1,
        entry: 0.62,
        expires_in_sec: 204,
        edge: 0.028,
        kelly: 0.65,
        persistence: 0.595,
      },
      markov: {
        p_uu: 0.578,
        p_dd: 0.612,
        persistence: 0.595,
        threshold_met: true,
        wait_reason: null,
        recent_series: [
          "U", "U", "U", "D", "U", "U", "D", "D", "U", "U",
          "U", "U", "D", "U", "U", "U", "D", "U", "U", "U",
        ],
      },
      recent_trades: normalTrades.slice(0, 5),
      all_trades: normalTrades,
      hub_meta: {
        trade_count: 70,
        nightly_unread: true,
        strategy_version: "v1.2.4",
        markov_p_uu: 0.578,
        alert_unread: 3,
      },
      health: { degraded: false, message: "" },
    },
    winning_streak: {
      /* PHASE 2: 枠のみ — M2.2+ で詳細 */
      bot_state: { state: "TRADING", mode: "paper" },
      balance: { current: 1088.0, initial: 1000.0 },
      daily_pnl: { value: 14.2, percent: 1.42 },
      cumulative_pnl: { value: 88.0, percent: 8.8 },
      win_rate: { value: 0.72, wins: 52, losses: 20, display: "72.0%" },
      ws_status: "connected",
      last_trade_at: "2026-05-27T14:32:00+09:00",
      current_position: null,
      markov: {
        p_uu: 0.62,
        p_dd: 0.58,
        persistence: 0.68,
        threshold_met: true,
        wait_reason: null,
        recent_series: Array(20).fill("U"),
      },
      recent_trades: [],
      all_trades: [],
      hub_meta: {
        trade_count: 72,
        nightly_unread: false,
        strategy_version: "v1.2.4",
        markov_p_uu: 0.62,
        alert_unread: 0,
      },
      health: { degraded: false, message: "" },
    },
    drawdown: {
      /* PHASE 2: 枠のみ — 緊急停止フロー検証用 */
      bot_state: { state: "TRADING", mode: "paper" },
      balance: { current: 972.5, initial: 1000.0 },
      daily_pnl: { value: -12.8, percent: -1.28 },
      cumulative_pnl: { value: -27.5, percent: -2.75 },
      win_rate: { value: 0.41, wins: 28, losses: 40, display: "41.2%" },
      ws_status: "degraded",
      last_trade_at: "2026-05-27T13:55:00+09:00",
      current_position: null,
      markov: {
        p_uu: 0.52,
        p_dd: 0.55,
        persistence: 0.48,
        threshold_met: false,
        wait_reason: "persistence",
        recent_series: [
          "D", "D", "U", "D", "D", "D", "U", "D", "D", "U",
          "D", "D", "D", "U", "D", "D", "D", "D", "U", "D",
        ],
      },
      recent_trades: [],
      all_trades: [],
      hub_meta: {
        trade_count: 68,
        nightly_unread: true,
        strategy_version: "v1.2.3",
        markov_p_uu: 0.52,
        alert_unread: 7,
      },
      health: {
        degraded: true,
        message: "WebSocket latency elevated (mock)",
        severity: "warn",
      },
    },
  };

  let CURRENT_SCENARIO = "normal";

  function getScenarioId() {
    return parseScenarioFromUrl();
  }

  function getData() {
    const id = getScenarioId();
    CURRENT_SCENARIO = id;
    const base = SCENARIOS[id] || SCENARIOS.normal;
    if (id === "winning_streak" && base.recent_trades.length === 0) {
      const t = buildTrades(58, 0.72, 1.4);
      base.recent_trades = t.slice(0, 5);
      base.all_trades = t;
    }
    if (id === "drawdown" && base.all_trades.length === 0) {
      const t = buildTrades(58, 0.41, 1.0);
      base.recent_trades = t.slice(0, 5);
      base.all_trades = t;
    }
    return JSON.parse(JSON.stringify(base));
  }

  function setScenario(id) {
    if (!SCENARIOS[id]) {
      return false;
    }
    CURRENT_SCENARIO = id;
    try {
      const url = new URL(global.location.href);
      url.searchParams.set("scenario", id);
      global.history.replaceState({}, "", url.toString());
    } catch (_e) {
      /* file:// */
    }
    global.dispatchEvent(
      new CustomEvent("scenario_changed", { detail: { scenario: id } }),
    );
    return true;
  }

  function mockSSE(eventName, payload, delayMs) {
    const delay = delayMs || 0;
    setTimeout(function () {
      global.document.dispatchEvent(
        new CustomEvent(eventName, { detail: payload }),
      );
    }, delay);
  }

  function formatPnl(value) {
    const sign = value >= 0 ? "+" : "";
    return sign + "$" + Math.abs(value).toFixed(2);
  }

  function formatPct(value) {
    const sign = value >= 0 ? "+" : "";
    return sign + value.toFixed(2) + "%";
  }

  global.YoRuuMockData = {
    SCENARIOS: SCENARIOS,
    getScenarioId: getScenarioId,
    getData: getData,
    setScenario: setScenario,
    mockSSE: mockSSE,
    formatPnl: formatPnl,
    formatPct: formatPct,
    BASE_TIME: BASE_TIME,
  };
})(typeof window !== "undefined" ? window : globalThis);
