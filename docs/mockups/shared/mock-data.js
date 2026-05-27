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

  /** §15.4.8 マスク済み完全サンプル（固定値） */
  const DAILY_REPORT_NORMAL = {
    schema_version: "1.0",
    report_date: "2026-05-27",
    generated_at: "2026-05-28T04:00:12+09:00",
    mode: "PAPER",
    current_strategy: {
      version: 3,
      parameters: {
        MIN_PROB: 0.87,
        MIN_EDGE: 0.06,
        KELLY_FRACTION: 0.65,
        PERSISTENCE_THRESHOLD: 0.72,
      },
      metadata: {
        applied_at: "2026-05-26T04:15:00+09:00",
        applied_by: "NIGHTLY_REVIEW",
        previous_version: 2,
      },
    },
    performance: {
      trades_total: 23,
      trades_win: 14,
      trades_loss: 9,
      trades_expired: 0,
      win_rate: 0.6087,
      pnl_usd: 8.42,
      pnl_pct: 0.81,
      balance_start_usd: 1033.76,
      balance_end_usd: 1042.18,
      max_drawdown_usd: -3.5,
      avg_edge_at_entry: 0.071,
      avg_persistence_at_entry: 0.74,
      by_state: {
        TRADING: { count: 23, win: 14 },
        MONITORING_POSITION: { count: 23, win: 14 },
      },
    },
    markov_snapshot: {
      computed_at: "2026-05-28T03:55:00+09:00",
      window_size: 20,
      matrix: {
        p_up_up: 0.578,
        p_up_down: 0.422,
        p_down_up: 0.388,
        p_down_down: 0.612,
      },
      rolling_persistence: 0.578,
      last_direction: "UP",
      history_summary: {
        avg_persistence_24h: 0.62,
        min_persistence_24h: 0.51,
        max_persistence_24h: 0.78,
      },
    },
    trade_breakdown: {
      by_side: {
        YES: { count: 12, win: 8, pnl_usd: 5.1 },
        NO: { count: 11, win: 6, pnl_usd: 3.32 },
      },
      by_hour_jst: {
        "09": { count: 3, win: 2 },
        "10": { count: 5, win: 3 },
      },
      wait_reason_distribution: {
        persistence: 142,
        edge: 38,
        prob: 17,
        liquidity: 4,
        risk_budget: 0,
      },
    },
    constraints: {
      MIN_PROB: { min: 0.8, max: 0.95, default: 0.87 },
      MIN_EDGE: { min: 0.03, max: 0.15, default: 0.06 },
      KELLY_FRACTION: { min: 0.1, max: 1.0, default: 0.65 },
      PERSISTENCE_THRESHOLD: { min: 0.5, max: 0.9, default: 0.7 },
    },
    notes: [],
  };

  /** §15.7.1 差分確認用サンプル提案 */
  const SAMPLE_PROPOSAL_JSON = {
    parameters: {
      MIN_PROB: 0.89,
      MIN_EDGE: 0.06,
      KELLY_FRACTION: 0.65,
      PERSISTENCE_THRESHOLD: 0.74,
    },
    rationale:
      "勝率 60.9%、avg_persistence 0.74 と高水準のため MIN_PROB を 0.87→0.89 に微増。他は維持。",
    applied_by: "NIGHTLY_REVIEW",
    source_report_id: 7,
  };

  const STRATEGY_VERSIONS_NORMAL = [
    {
      version: 4,
      applied_at: "2026-05-26T04:15:00+09:00",
      applied_by: "NIGHTLY_REVIEW",
      parameters: {
        MIN_PROB: 0.87,
        MIN_EDGE: 0.06,
        KELLY_FRACTION: 0.65,
        PERSISTENCE_THRESHOLD: 0.72,
      },
      rationale: "Persistence 安定のため閾値を 0.70→0.72 に微増。",
      performance: { trades: 23, win_rate: 0.6087, pnl_usd: 8.42 },
    },
    {
      version: 3,
      applied_at: "2026-05-22T04:12:00+09:00",
      applied_by: "NIGHTLY_REVIEW",
      parameters: {
        MIN_PROB: 0.86,
        MIN_EDGE: 0.06,
        KELLY_FRACTION: 0.65,
        PERSISTENCE_THRESHOLD: 0.7,
      },
      rationale: "Edge 平均が閾値付近のため MIN_EDGE は維持。",
      performance: { trades: 41, win_rate: 0.5366, pnl_usd: 12.1 },
    },
    {
      version: 2,
      applied_at: "2026-05-15T04:08:00+09:00",
      applied_by: "USER",
      parameters: {
        MIN_PROB: 0.85,
        MIN_EDGE: 0.055,
        KELLY_FRACTION: 0.6,
        PERSISTENCE_THRESHOLD: 0.68,
      },
      rationale: "手動微調整: Kelly を保守化。",
      performance: { trades: 38, win_rate: 0.5, pnl_usd: 4.2 },
    },
    {
      version: 1,
      applied_at: "2026-05-08T04:00:00+09:00",
      applied_by: "USER",
      parameters: {
        MIN_PROB: 0.84,
        MIN_EDGE: 0.05,
        KELLY_FRACTION: 0.55,
        PERSISTENCE_THRESHOLD: 0.65,
      },
      rationale: "初版デフォルト適用。",
      performance: { trades: 52, win_rate: 0.48, pnl_usd: -2.1 },
    },
  ];

  const SETTINGS_MOCK = {
    mode: "paper",
    initial_balance_usd: 1000,
    max_trade_size_usd: 10,
    daily_loss_limit_usd: 15,
    nightly_review: { enabled: true, send_time: "04:00", timezone: "Asia/Tokyo" },
    yaml: [
      "mode: paper",
      "initial_balance_usd: 1000.00",
      "max_trade_size_usd: 10.00",
      "daily_loss_limit_usd: 15.00",
      "nightly_review:",
      "  enabled: true",
      "  send_time: \"04:00\"",
      "  timezone: Asia/Tokyo",
    ].join("\n"),
    strategy_readonly: {
      MIN_PROB: 0.87,
      MIN_EDGE: 0.06,
      KELLY_FRACTION: 0.65,
      PERSISTENCE_THRESHOLD: 0.72,
    },
  };

  const ALERTS_MOCK = [
    {
      id: 1,
      severity: "WARN",
      code: "W_WS_001",
      message: "WebSocket レイテンシが上昇しています",
      location: "websocket/polymarket",
      created_at: "2026-05-27T14:20:00+09:00",
      read: false,
    },
    {
      id: 2,
      severity: "ERROR",
      code: "E_FILL_001",
      message: "流動性不足のため約定できませんでした",
      location: "executor/paper",
      created_at: "2026-05-27T13:58:00+09:00",
      read: false,
    },
    {
      id: 3,
      severity: "INFO",
      code: "I_REPORT_001",
      message: "夜間レポートが生成されました",
      location: "nightly/reporter",
      created_at: "2026-05-28T04:00:12+09:00",
      read: false,
    },
    {
      id: 4,
      severity: "CRITICAL",
      code: "C_STOP_001",
      message: "緊急停止が実行されました（モック履歴）",
      location: "killswitch",
      created_at: "2026-05-26T18:12:00+09:00",
      read: true,
    },
  ];

  const EMERGENCY_ACTIVE_MOCK = {
    active: true,
    triggered_at: "2026-05-27T14:35:00+09:00",
    trigger_source: "dashboard_fab",
    reason: "user_initiated",
    snapshot: {
      state: "EMERGENCY_STOP",
      mode: "paper",
      open_positions: 0,
      balance_usd: 1042.18,
    },
    checklist_done: [
      "open_orders_cancelled",
      "positions_closed",
      "websocket_disconnected",
    ],
    logs: [
      "[14:35:00] emergency_stop_triggered received",
      "[14:35:01] cancel_all_orders: ok",
      "[14:35:02] close_positions: none open",
      "[14:35:03] state → EMERGENCY_STOP",
    ],
  };

  const MODE_HEALTH_MOCK = {
    ws_polymarket_connected: true,
    ws_binance_connected: true,
    usdc_balance_usd: 128.5,
    daily_loss_limit_usd: 15,
    max_trade_size_usd: 10,
  };

  const WHAT_IF_SCENARIOS = [
    {
      id: "baseline",
      label: "現行 (baseline)",
      params: {
        MIN_PROB: 0.87,
        MIN_EDGE: 0.06,
        KELLY_FRACTION: 0.65,
        PERSISTENCE_THRESHOLD: 0.72,
      },
      result: { trades: 70, win_rate: 0.543, pnl_usd: 42.18 },
    },
    {
      id: "conservative",
      label: "保守 (高 MIN_PROB)",
      params: {
        MIN_PROB: 0.92,
        MIN_EDGE: 0.07,
        KELLY_FRACTION: 0.55,
        PERSISTENCE_THRESHOLD: 0.75,
      },
      result: { trades: 52, win_rate: 0.58, pnl_usd: 28.4 },
    },
    {
      id: "aggressive",
      label: "積極 (低閾値)",
      params: {
        MIN_PROB: 0.82,
        MIN_EDGE: 0.05,
        KELLY_FRACTION: 0.7,
        PERSISTENCE_THRESHOLD: 0.68,
      },
      result: { trades: 89, win_rate: 0.51, pnl_usd: 35.6 },
    },
    {
      id: "drawdown_sim",
      label: "DD シミュレーション",
      params: {
        MIN_PROB: 0.88,
        MIN_EDGE: 0.08,
        KELLY_FRACTION: 0.5,
        PERSISTENCE_THRESHOLD: 0.74,
      },
      result: { trades: 45, win_rate: 0.49, pnl_usd: -8.2 },
    },
  ];

  const MARKOV_LIVE_NORMAL = {
    window_size: 20,
    matrix: {
      p_up_up: 0.578,
      p_up_down: 0.422,
      p_down_up: 0.388,
      p_down_down: 0.612,
    },
    recent_series_full: [
      "U", "U", "U", "D", "U", "U", "D", "D", "U", "U",
      "U", "U", "D", "U", "U", "U", "D", "U", "U", "U",
      "D", "U", "U", "D", "D", "U", "U", "U", "D", "U",
      "U", "U", "D", "U", "D", "D", "U", "U", "U", "U",
      "D", "D", "U", "U", "D", "U", "U", "D", "U", "U",
    ],
    persistence_series: [
      0.55, 0.56, 0.57, 0.54, 0.56, 0.58, 0.57, 0.59, 0.58, 0.6,
      0.59, 0.58, 0.57, 0.58, 0.59, 0.6, 0.58, 0.57, 0.58, 0.578,
    ],
    persistence: 0.578,
    persistence_threshold: 0.72,
    edge: { value: 0.028, min_edge: 0.06, met: false },
    min_prob: { value: 0.91, threshold: 0.87, met: true },
    threshold_met: true,
    wait_reason: null,
    last_direction: "UP",
  };

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
      dailyReport: DAILY_REPORT_NORMAL,
      sampleProposal: SAMPLE_PROPOSAL_JSON,
      strategyVersions: STRATEGY_VERSIONS_NORMAL,
      markovLive: MARKOV_LIVE_NORMAL,
      settings: SETTINGS_MOCK,
      alerts: ALERTS_MOCK,
      emergencyStop: null,
      modeHealth: MODE_HEALTH_MOCK,
      whatIfScenarios: WHAT_IF_SCENARIOS,
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
      dailyReport: DAILY_REPORT_NORMAL,
      sampleProposal: SAMPLE_PROPOSAL_JSON,
      strategyVersions: STRATEGY_VERSIONS_NORMAL,
      markovLive: Object.assign({}, MARKOV_LIVE_NORMAL, {
        threshold_met: true,
        wait_reason: null,
        edge: { value: 0.095, min_edge: 0.06, met: true },
      }),
      settings: SETTINGS_MOCK,
      alerts: [],
      emergencyStop: null,
      modeHealth: MODE_HEALTH_MOCK,
      whatIfScenarios: WHAT_IF_SCENARIOS,
    },
    drawdown: {
      /* 緊急停止フロー検証用 */
      bot_state: { state: "EMERGENCY_STOP", mode: "paper" },
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
      dailyReport: DAILY_REPORT_NORMAL,
      sampleProposal: SAMPLE_PROPOSAL_JSON,
      strategyVersions: STRATEGY_VERSIONS_NORMAL,
      markovLive: Object.assign({}, MARKOV_LIVE_NORMAL, {
        threshold_met: false,
        wait_reason: "persistence",
        persistence: 0.48,
        persistence_series: [
          0.62, 0.6, 0.58, 0.55, 0.52, 0.5, 0.49, 0.48, 0.47, 0.48,
          0.49, 0.48, 0.47, 0.48, 0.49, 0.48, 0.47, 0.48, 0.48, 0.48,
        ],
      }),
      settings: SETTINGS_MOCK,
      alerts: ALERTS_MOCK.map(function (a) {
        return Object.assign({}, a, { read: false });
      }),
      emergencyStop: EMERGENCY_ACTIVE_MOCK,
      modeHealth: Object.assign({}, MODE_HEALTH_MOCK, {
        ws_polymarket_connected: false,
      }),
      whatIfScenarios: WHAT_IF_SCENARIOS,
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

  function getDailyReport() {
    return JSON.parse(JSON.stringify(getData().dailyReport));
  }

  function getStrategyVersions() {
    return JSON.parse(JSON.stringify(getData().strategyVersions));
  }

  function getMarkovLive() {
    return JSON.parse(JSON.stringify(getData().markovLive));
  }

  function getEmergencyStop() {
    var d = getData();
    if (d.emergencyStop) {
      return JSON.parse(JSON.stringify(d.emergencyStop));
    }
    return JSON.parse(JSON.stringify(EMERGENCY_ACTIVE_MOCK));
  }

  function getAlerts() {
    return JSON.parse(JSON.stringify(getData().alerts));
  }

  function getSettings() {
    return JSON.parse(JSON.stringify(getData().settings));
  }

  function getWhatIfScenarios() {
    return JSON.parse(JSON.stringify(getData().whatIfScenarios));
  }

  function getModeHealth() {
    return JSON.parse(JSON.stringify(getData().modeHealth));
  }

  global.YoRuuMockData = {
    SCENARIOS: SCENARIOS,
    DAILY_REPORT_NORMAL: DAILY_REPORT_NORMAL,
    getScenarioId: getScenarioId,
    getData: getData,
    getDailyReport: getDailyReport,
    getStrategyVersions: getStrategyVersions,
    getMarkovLive: getMarkovLive,
    getEmergencyStop: getEmergencyStop,
    getAlerts: getAlerts,
    getSettings: getSettings,
    getWhatIfScenarios: getWhatIfScenarios,
    getModeHealth: getModeHealth,
    EMERGENCY_ACTIVE_MOCK: EMERGENCY_ACTIVE_MOCK,
    setScenario: setScenario,
    mockSSE: mockSSE,
    formatPnl: formatPnl,
    formatPct: formatPct,
    BASE_TIME: BASE_TIME,
  };
})(typeof window !== "undefined" ? window : globalThis);
