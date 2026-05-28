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

  /** M4.6 — FX mock (ch18 / GET /api/v1/fx/usd_jpy 相当) */
  const FX_USD_JPY_MOCK = {
    rate: 156.42,
    fetched_at: "2026-05-28T06:00:00+00:00",
    source: "exchangerate.host",
    stale: false,
  };

  const FX_USD_JPY_STALE_MOCK = {
    rate: 155.88,
    fetched_at: "2026-05-27T22:00:00+00:00",
    source: "exchangerate.host",
    stale: true,
  };

  function lockedFromPosition(pos) {
    if (!pos || pos.size == null) {
      return 0;
    }
    const size = Number(pos.size);
    return Number.isFinite(size) && size > 0 ? size : 0;
  }

  /** H-1 派生: principal / locked / balance（自由資金）から 5 値を算出 */
  function principalDerived(balanceFree, principalValue, locked) {
    const principal = Number(principalValue);
    const locked_principal = Number(locked) || 0;
    const balance = Number(balanceFree);
    const total_assets = balance + locked_principal;
    const cumulative_pnl = Math.round((total_assets - principal) * 100) / 100;
    const withdrawable_principal =
      Math.round((principal - locked_principal) * 100) / 100;
    return {
      value: principal,
      locked_principal: locked_principal,
      withdrawable_principal: withdrawable_principal,
      total_assets: Math.round(total_assets * 100) / 100,
      cumulative_pnl: cumulative_pnl,
    };
  }

  function bootstrapPrincipalTxns(initialPrincipal) {
    return [
      {
        id: 1,
        kind: "DEPOSIT",
        amount: initialPrincipal,
        balance_before: 0,
        balance_after: initialPrincipal,
        principal_before: 0,
        principal_after: initialPrincipal,
        ts_utc: "2026-05-08T04:00:00+09:00",
        note: "initial_principal bootstrap",
      },
    ];
  }

  const HUD_SIGNAL_COUNTS_NORMAL = {
    signals: 142,
    entries: 58,
    expired: 12,
  };

  const HUD_TRADE_STATS_NORMAL = {
    max_win_usd: 4.85,
    avg_size_usd: 6.2,
    total_trades: 70,
  };

  const HUD_SYSTEM_PANELS_NORMAL = {
    sse_status: "connected",
    runtime_uptime_sec: 86412,
    env: "paper",
    brain: "markov+kelly",
    host: "lab.local",
  };

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
      principal_base: 1000.0,
      principal_transactions: bootstrapPrincipalTxns(1000.0),
      signal_counts: HUD_SIGNAL_COUNTS_NORMAL,
      trade_stats: HUD_TRADE_STATS_NORMAL,
      system_panels: HUD_SYSTEM_PANELS_NORMAL,
      nightly_countdown_sec: 48912,
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
      principal_base: 1000.0,
      principal_transactions: bootstrapPrincipalTxns(1000.0),
      signal_counts: { signals: 98, entries: 72, expired: 6 },
      trade_stats: {
        max_win_usd: 6.2,
        avg_size_usd: 6.8,
        total_trades: 72,
      },
      system_panels: Object.assign({}, HUD_SYSTEM_PANELS_NORMAL, {
        sse_status: "connected",
      }),
      nightly_countdown_sec: 12000,
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
      principal_base: 1000.0,
      principal_transactions: bootstrapPrincipalTxns(1000.0),
      signal_counts: { signals: 210, entries: 68, expired: 24 },
      trade_stats: {
        max_win_usd: 3.1,
        avg_size_usd: 5.9,
        total_trades: 68,
      },
      system_panels: Object.assign({}, HUD_SYSTEM_PANELS_NORMAL, {
        sse_status: "degraded",
        runtime_uptime_sec: 43200,
      }),
      nightly_countdown_sec: 7200,
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

  /** Q3-MOCK: PaperExecutor 準拠の可変残高（open 減算 / close 加算、INV-D-06） */
  let runtimeLedger = null;

  function resetRuntimeLedger(scenarioId, baseBalance, baseScenario) {
    const principalBase =
      baseScenario && baseScenario.principal_base != null
        ? baseScenario.principal_base
        : baseBalance.initial;
    const txns =
      baseScenario && baseScenario.principal_transactions
        ? JSON.parse(JSON.stringify(baseScenario.principal_transactions))
        : bootstrapPrincipalTxns(principalBase);
    const staticLocked =
      baseScenario && baseScenario.current_position
        ? lockedFromPosition(baseScenario.current_position)
        : 0;
    const closedPnlSeed =
      baseBalance.current + staticLocked - principalBase;
    runtimeLedger = {
      scenarioId: scenarioId,
      initial: baseBalance.initial,
      balance: baseBalance.current,
      principal: principalBase,
      openPositions: [],
      closedPnlSum: Math.round(closedPnlSeed * 100) / 100,
      nextTradeId: 8100,
      principalTxns: txns,
    };
  }

  function ensureRuntimeLedger(scenarioId, baseBalance, baseScenario) {
    if (!runtimeLedger || runtimeLedger.scenarioId !== scenarioId) {
      resetRuntimeLedger(scenarioId, baseBalance, baseScenario);
    }
    return runtimeLedger;
  }

  function sumOpenNotional() {
    if (!runtimeLedger) {
      return 0;
    }
    return runtimeLedger.openPositions.reduce(function (sum, pos) {
      return sum + pos.size_usd;
    }, 0);
  }

  function sumPrincipalDeposits() {
    if (!runtimeLedger) {
      return 0;
    }
    return runtimeLedger.principalTxns.reduce(function (sum, tx) {
      return tx.kind === "DEPOSIT" ? sum + Number(tx.amount) : sum;
    }, 0);
  }

  function sumPrincipalWithdrawals() {
    if (!runtimeLedger) {
      return 0;
    }
    return runtimeLedger.principalTxns.reduce(function (sum, tx) {
      return tx.kind === "WITHDRAW" ? sum + Number(tx.amount) : sum;
    }, 0);
  }

  /** INV-D-06 v2: balance + open ≈ principal + closed_pnl */
  function checkInvD06() {
    if (!runtimeLedger) {
      return true;
    }
    const left = runtimeLedger.balance + sumOpenNotional();
    const right = runtimeLedger.principal + runtimeLedger.closedPnlSum;
    return Math.abs(left - right) < 0.02;
  }

  /** INV-D-07: principal == Σ(DEPOSIT) − Σ(WITHDRAW) */
  function checkInvD07() {
    if (!runtimeLedger) {
      return true;
    }
    const expected = sumPrincipalDeposits() - sumPrincipalWithdrawals();
    return Math.abs(runtimeLedger.principal - expected) < 0.02;
  }

  function checkInvD09() {
    if (!runtimeLedger) {
      return true;
    }
    return runtimeLedger.principal >= -0.001 && runtimeLedger.balance >= -0.001;
  }

  function effectiveLocked(clone) {
    const openSum = sumOpenNotional();
    if (openSum > 0) {
      return openSum;
    }
    return lockedFromPosition(clone && clone.current_position);
  }

  function buildPrincipalChangedPayload(kind, amount, note) {
    const ledger = runtimeLedger;
    if (!ledger) {
      return null;
    }
    const locked = sumOpenNotional();
    const balanceBefore = ledger.balance;
    const principalBefore = ledger.principal;
    let balanceAfter = balanceBefore;
    let principalAfter = principalBefore;
    if (kind === "DEPOSIT") {
      balanceAfter += amount;
      principalAfter += amount;
    } else {
      balanceAfter -= amount;
      principalAfter -= amount;
    }
    const withdrawable = principalAfter - locked;
    const totalAssets = balanceAfter + locked;
    return {
      kind: kind,
      amount: amount,
      balance_before: Math.round(balanceBefore * 100) / 100,
      balance_after: Math.round(balanceAfter * 100) / 100,
      principal_before: Math.round(principalBefore * 100) / 100,
      principal_after: Math.round(principalAfter * 100) / 100,
      locked_principal: Math.round(locked * 100) / 100,
      withdrawable_principal: Math.round(withdrawable * 100) / 100,
      total_assets: Math.round(totalAssets * 100) / 100,
      cumulative_pnl:
        Math.round((totalAssets - principalAfter) * 100) / 100,
      ts_utc: new Date().toISOString(),
      note: note || null,
      severity: "INFO",
    };
  }

  function applyPrincipalChange(payload) {
    const ledger = runtimeLedger;
    if (!ledger || !payload) {
      return false;
    }
    const kind = payload.kind;
    const amount = Number(payload.amount);
    if (!Number.isFinite(amount) || amount <= 0) {
      return false;
    }
    if (kind === "WITHDRAW" && amount > ledger.balance + 0.001) {
      console.warn("[M4.6-MOCK] INV-D-08: withdraw exceeds balance", amount);
      return false;
    }
    const balanceBefore = ledger.balance;
    const principalBefore = ledger.principal;
    if (kind === "DEPOSIT") {
      ledger.balance += amount;
      ledger.principal += amount;
    } else if (kind === "WITHDRAW") {
      ledger.balance -= amount;
      ledger.principal -= amount;
    } else {
      return false;
    }
    ledger.principalTxns.push({
      id: ledger.principalTxns.length + 1,
      kind: kind,
      amount: amount,
      balance_before: balanceBefore,
      balance_after: ledger.balance,
      principal_before: principalBefore,
      principal_after: ledger.principal,
      ts_utc: payload.ts_utc || new Date().toISOString(),
      note: payload.note || null,
    });
    if (!checkInvD06()) {
      console.warn("[M4.6-MOCK] INV-D-06 drift after principal change");
    }
    if (!checkInvD07()) {
      console.warn("[M4.6-MOCK] INV-D-07 drift after principal change");
    }
    if (!checkInvD09()) {
      console.warn("[M4.6-MOCK] INV-D-09 violated after principal change");
    }
    return true;
  }

  function applyPositionOpened(payload) {
    const ledger = runtimeLedger;
    if (!ledger || !payload) {
      return;
    }
    const sizeUsd = Number(payload.size_usd);
    if (!Number.isFinite(sizeUsd) || sizeUsd <= 0) {
      return;
    }
    ledger.balance -= sizeUsd;
    ledger.openPositions.push({
      trade_id: payload.trade_id,
      size_usd: sizeUsd,
      side: payload.side || "YES",
      entry_price: payload.entry_price || 0.62,
    });
    if (!checkInvD06()) {
      console.warn("[Q3-MOCK] INV-D-06 drift after position_opened", {
        balance: ledger.balance,
        open_sum: sumOpenNotional(),
        initial: ledger.initial,
        closed_pnl: ledger.closedPnlSum,
      });
    }
  }

  function applyPositionClosed(payload) {
    const ledger = runtimeLedger;
    if (!ledger || !payload) {
      return false;
    }
    const tradeId = payload.trade_id;
    const idx = ledger.openPositions.findIndex(function (p) {
      return p.trade_id === tradeId;
    });
    if (idx < 0) {
      console.warn("[Q3-MOCK] position_closed: unknown trade_id", tradeId);
      return false;
    }
    const pos = ledger.openPositions[idx];
    const pnl = Number(payload.pnl);
    const safePnl = Number.isFinite(pnl) ? pnl : 0;
    ledger.balance += pos.size_usd + safePnl;
    ledger.closedPnlSum += safePnl;
    ledger.openPositions.splice(idx, 1);
    if (!checkInvD06()) {
      console.warn("[Q3-MOCK] INV-D-06 drift after position_closed", {
        balance: ledger.balance,
        open_sum: sumOpenNotional(),
        initial: ledger.initial,
        closed_pnl: ledger.closedPnlSum,
      });
    }
    return true;
  }

  function getBalanceSnapshot() {
    if (!runtimeLedger) {
      const d = SCENARIOS[CURRENT_SCENARIO] || SCENARIOS.normal;
      const locked = lockedFromPosition(d.current_position);
      const derived = principalDerived(
        d.balance.current,
        d.principal_base,
        locked,
      );
      return {
        current: d.balance.current,
        initial: d.balance.initial,
        open_notional: locked,
        closed_pnl_sum: derived.cumulative_pnl,
        principal: derived.value,
        locked_principal: derived.locked_principal,
        withdrawable_principal: derived.withdrawable_principal,
        total_assets: derived.total_assets,
        cumulative_pnl: derived.cumulative_pnl,
      };
    }
    const locked = sumOpenNotional();
    const derived = principalDerived(
      runtimeLedger.balance,
      runtimeLedger.principal,
      locked,
    );
    return {
      current: runtimeLedger.balance,
      initial: runtimeLedger.initial,
      open_notional: locked,
      closed_pnl_sum: runtimeLedger.closedPnlSum,
      principal: derived.value,
      locked_principal: derived.locked_principal,
      withdrawable_principal: derived.withdrawable_principal,
      total_assets: derived.total_assets,
      cumulative_pnl: derived.cumulative_pnl,
    };
  }

  function simulatePositionOpened(sizeUsd, side) {
    const scenarioId = getScenarioId();
    const base = SCENARIOS[scenarioId] || SCENARIOS.normal;
    const data = getData();
    const ledger = ensureRuntimeLedger(scenarioId, data.balance, base);
    const payload = {
      trade_id: ledger.nextTradeId,
      market: "BTC_5MIN_UPDOWN",
      side: side || "YES",
      size_usd: sizeUsd,
      entry_price: 0.62,
      expires_at: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
      edge_at_entry: 0.071,
      persistence_at_entry: 0.72,
    };
    ledger.nextTradeId += 1;
    applyPositionOpened(payload);
    global.document.dispatchEvent(
      new CustomEvent("position_opened", { detail: payload }),
    );
    global.document.dispatchEvent(
      new CustomEvent("balance_updated", {
        detail: getBalanceSnapshot(),
      }),
    );
    return payload;
  }

  function simulatePositionClosed(tradeId, pnlUsd) {
    const payload = {
      trade_id: tradeId,
      exit_price: 1.0,
      pnl: pnlUsd,
      win: pnlUsd >= 0,
      closed_at: new Date().toISOString(),
    };
    applyPositionClosed(payload);
    global.document.dispatchEvent(
      new CustomEvent("position_closed", { detail: payload }),
    );
    global.document.dispatchEvent(
      new CustomEvent("balance_updated", {
        detail: getBalanceSnapshot(),
      }),
    );
    return payload;
  }

  function simulatePrincipalDeposit(amountUsd, note) {
    const scenarioId = getScenarioId();
    const base = SCENARIOS[scenarioId] || SCENARIOS.normal;
    const data = getData();
    ensureRuntimeLedger(scenarioId, data.balance, base);
    const payload = buildPrincipalChangedPayload(
      "DEPOSIT",
      amountUsd,
      note || "simulate_deposit",
    );
    if (!payload || !applyPrincipalChange(payload)) {
      return null;
    }
    global.document.dispatchEvent(
      new CustomEvent("principal_changed", { detail: payload }),
    );
    global.document.dispatchEvent(
      new CustomEvent("balance_updated", { detail: getBalanceSnapshot() }),
    );
    return payload;
  }

  function simulatePrincipalWithdraw(amountUsd, note) {
    const scenarioId = getScenarioId();
    const base = SCENARIOS[scenarioId] || SCENARIOS.normal;
    const data = getData();
    ensureRuntimeLedger(scenarioId, data.balance, base);
    const payload = buildPrincipalChangedPayload(
      "WITHDRAW",
      amountUsd,
      note || "simulate_withdraw",
    );
    if (!payload || !applyPrincipalChange(payload)) {
      return null;
    }
    global.document.dispatchEvent(
      new CustomEvent("principal_changed", { detail: payload }),
    );
    global.document.dispatchEvent(
      new CustomEvent("balance_updated", { detail: getBalanceSnapshot() }),
    );
    return payload;
  }

  /** 手動確認: deposit → open → close → withdraw（M4.6） */
  function runQ3PrincipalDemo() {
    const log = [];
    log.push({ step: "initial", snap: getBalanceSnapshot() });
    const dep = simulatePrincipalDeposit(100, "q3_principal_demo");
    log.push({ step: "deposit", payload: dep, snap: getBalanceSnapshot() });
    const opened = simulatePositionOpened(5.0, "YES");
    log.push({ step: "open", payload: opened, snap: getBalanceSnapshot() });
    simulatePositionClosed(opened.trade_id, 0.8);
    log.push({ step: "close", snap: getBalanceSnapshot() });
    const wd = simulatePrincipalWithdraw(50, "q3_principal_demo");
    log.push({ step: "withdraw", payload: wd, snap: getBalanceSnapshot() });
    log.push({
      step: "final",
      inv_d06: checkInvD06(),
      inv_d07: checkInvD07(),
      inv_d09: checkInvD09(),
      snap: getBalanceSnapshot(),
    });
    console.table(
      log.map(function (row) {
        return {
          step: row.step,
          balance: row.snap ? row.snap.current : null,
          principal: row.snap ? row.snap.principal : null,
        };
      }),
    );
    return log;
  }

  /** 手動確認: 3 open → 順次 close（Q3-MOCK.4） */
  function runQ3BalanceDemo() {
    const sizes = [5.5, 6.0, 4.5];
    const pnls = [1.2, -0.8, 0.5];
    const log = [];
    const snap0 = getBalanceSnapshot();
    log.push({ step: "initial", balance: snap0.current });
    const opens = sizes.map(function (sz) {
      return simulatePositionOpened(sz, "YES");
    });
    opens.forEach(function (o, i) {
      log.push({
        step: "open " + (i + 1),
        trade_id: o.trade_id,
        balance: getBalanceSnapshot().current,
      });
    });
    opens.forEach(function (o, i) {
      simulatePositionClosed(o.trade_id, pnls[i]);
      log.push({
        step: "close " + (i + 1),
        trade_id: o.trade_id,
        balance: getBalanceSnapshot().current,
      });
    });
    log.push({
      step: "final",
      balance: getBalanceSnapshot().current,
      inv_d06: checkInvD06(),
    });
    console.table(log);
    return log;
  }

  function getScenarioId() {
    return parseScenarioFromUrl();
  }

  function getData() {
    const id = getScenarioId();
    CURRENT_SCENARIO = id;
    const base = SCENARIOS[id] || SCENARIOS.normal;
    const clone = JSON.parse(JSON.stringify(base));
    const ledger = ensureRuntimeLedger(id, clone.balance, base);
    clone.balance.current = ledger.balance;
    clone.balance.initial = ledger.initial;
    const locked = effectiveLocked(clone);
    clone.principal = principalDerived(
      ledger.balance,
      ledger.principal,
      locked,
    );
    clone.principal_transactions = JSON.parse(
      JSON.stringify(ledger.principalTxns),
    );
    if (id === "winning_streak" && base.recent_trades.length === 0) {
      const t = buildTrades(58, 0.72, 1.4);
      clone.recent_trades = t.slice(0, 5);
      clone.all_trades = t;
    }
    if (id === "drawdown" && base.all_trades.length === 0) {
      const t = buildTrades(58, 0.41, 1.0);
      clone.recent_trades = t.slice(0, 5);
      clone.all_trades = t;
    }
    return clone;
  }

  function setScenario(id) {
    if (!SCENARIOS[id]) {
      return false;
    }
    CURRENT_SCENARIO = id;
    runtimeLedger = null;
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

  /**
   * SSE payload fixtures — ch10 §10.5.3 / ch8 §8.9 SSOT (§F T4.1 / B1).
   * Call sites pass overrides only; do not duplicate full shapes inline.
   */
  const SSE_PAYLOADS = {
    state_changed: {
      from: "TRADING",
      to: "MONITORING_POSITION",
      timestamp: "2026-05-27T14:32:48+09:00",
      reason: "position_opened",
      severity: "INFO",
    },
    markov_update: {
      computed_at: "2026-05-27T14:35:00+09:00",
      window_size: 20,
      matrix: {
        p_up_up: 0.578,
        p_up_down: 0.422,
        p_down_up: 0.388,
        p_down_down: 0.612,
      },
      rolling_persistence: 0.578,
      last_direction: "UP",
      threshold_met: false,
      wait_reason: "persistence",
      severity: "INFO",
    },
    health_degraded: {
      component: "polymarket_ws",
      reason: "disconnected",
      retry_count: 2,
      timestamp: "2026-05-27T14:32:48+09:00",
      severity: "WARN",
    },
    health_recovered: {
      component: "polymarket_ws",
      reason: "reconnected",
      recovery_duration_sec: 8,
      timestamp: "2026-05-27T14:32:48+09:00",
      severity: "INFO",
    },
    position_opened: {
      trade_id: 71,
      market: "BTC_5MIN_UPDOWN",
      side: "YES",
      size_usd: 7.1,
      entry_price: 0.62,
      expires_at: "2026-05-27T14:37:00+09:00",
      edge_at_entry: 0.071,
      persistence_at_entry: 0.72,
      severity: "INFO",
    },
    position_closed: {
      trade_id: 71,
      exit_price: 1.0,
      pnl: 4.35,
      win: true,
      closed_at: "2026-05-27T14:37:00+09:00",
      severity: "INFO",
    },
    nightly_report_ready: {
      report_date: "2026-05-27",
      report_id: 7,
      summary_url: "/api/v1/reports/7",
      severity: "INFO",
    },
    mode_changed: {
      from: "PAPER",
      to: "SIMMER",
      timestamp: "2026-05-27T14:32:48+09:00",
      severity: "INFO",
    },
    emergency_stop_triggered: {
      trigger: "dashboard_button",
      timestamp: "2026-05-27T14:32:48+09:00",
      open_positions_closed: 1,
      severity: "CRITICAL",
    },
    alert_added: {
      id: 143,
      code: "W_HEALTH_001",
      severity: "WARN",
      message: "WebSocket reconnected after 8s",
      created_at: "2026-05-27T14:32:48+09:00",
    },
    strategy_applied: {
      new_version: 4,
      previous_version: 3,
      applied_by: "NIGHTLY_REVIEW",
      rationale: "勝率 60.9% のため MIN_PROB を 0.87→0.89 に微増",
      applied_at: "2026-05-28T04:15:00+09:00",
      diff: { MIN_PROB: [0.87, 0.89] },
      severity: "INFO",
    },
    principal_changed: {
      kind: "DEPOSIT",
      amount: 500.0,
      balance_before: 1042.18,
      balance_after: 1542.18,
      principal_before: 1000.0,
      principal_after: 1500.0,
      locked_principal: 7.1,
      withdrawable_principal: 1492.9,
      total_assets: 1549.28,
      cumulative_pnl: 49.28,
      ts_utc: "2026-05-28T05:30:00+00:00",
      note: "mock_deposit",
      severity: "INFO",
    },
  };

  function ssePayload(eventName, overrides) {
    const base = SSE_PAYLOADS[eventName];
    if (!base) {
      return overrides ? JSON.parse(JSON.stringify(overrides)) : {};
    }
    const out = JSON.parse(JSON.stringify(base));
    if (overrides) {
      Object.keys(overrides).forEach(function (key) {
        out[key] = overrides[key];
      });
    }
    return out;
  }


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

  function mockSSE(eventName, payload, delayMs) {
    const detail = ssePayload(eventName, payload);
    const delay = delayMs || 0;
    setTimeout(function () {
      const scenarioId = getScenarioId();
      const base = SCENARIOS[scenarioId] || SCENARIOS.normal;
      if (eventName === "position_opened") {
        const data = getData();
        ensureRuntimeLedger(scenarioId, data.balance, base);
        applyPositionOpened(detail);
        global.document.dispatchEvent(
          new CustomEvent("balance_updated", {
            detail: getBalanceSnapshot(),
          }),
        );
      } else if (eventName === "position_closed") {
        const data = getData();
        ensureRuntimeLedger(scenarioId, data.balance, base);
        applyPositionClosed(detail);
        global.document.dispatchEvent(
          new CustomEvent("balance_updated", {
            detail: getBalanceSnapshot(),
          }),
        );
      } else if (eventName === "principal_changed") {
        const data = getData();
        ensureRuntimeLedger(scenarioId, data.balance, base);
        applyPrincipalChange(detail);
        global.document.dispatchEvent(
          new CustomEvent("balance_updated", {
            detail: getBalanceSnapshot(),
          }),
        );
      }
      global.document.dispatchEvent(
        new CustomEvent(eventName, { detail: detail }),
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

  function getPrincipalSnapshot() {
    return JSON.parse(JSON.stringify(getData().principal));
  }

  function getPrincipalTransactions() {
    return JSON.parse(JSON.stringify(getData().principal_transactions));
  }

  function getFxRate() {
    const stale = getScenarioId() === "drawdown";
    return JSON.parse(
      JSON.stringify(stale ? FX_USD_JPY_STALE_MOCK : FX_USD_JPY_MOCK),
    );
  }

  function formatMoney(valueUsd, currency, fxRate) {
    const cur = (currency || "USD").toUpperCase();
    if (cur === "JPY" && fxRate && Number.isFinite(fxRate.rate)) {
      const jpy = Math.round(Number(valueUsd) * fxRate.rate);
      return "¥" + jpy.toLocaleString("ja-JP");
    }
    const v = Number(valueUsd);
    const sign = v >= 0 ? "" : "-";
    return sign + "$" + Math.abs(v).toFixed(2);
  }

  /**
   * Lab OHLC bars (mirrors src/yoruu/infra/ohlc_provider.py seed).
   */
  function labOhlcBars(limit) {
    var n = limit || 60;
    var bars = [];
    var price = 68250;
    var i;
    for (i = 0; i < n; i += 1) {
      var drift = Math.sin(i / 8) * 120 + ((i % 7) - 3) * 15;
      var open = price;
      var close = price + drift;
      var high = Math.max(open, close) + Math.abs(drift) * 0.15;
      var low = Math.min(open, close) - Math.abs(drift) * 0.15;
      bars.push({
        ts: "2026-05-28T12:" + String(i % 60).padStart(2, "0") + ":00+00:00",
        open: Math.round(open * 100) / 100,
        high: Math.round(high * 100) / 100,
        low: Math.round(low * 100) / 100,
        close: Math.round(close * 100) / 100,
        volume: 12.5 + (i % 5),
      });
      price = close;
    }
    return bars;
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
    SSE_PAYLOADS: SSE_PAYLOADS,
    ssePayload: ssePayload,
    setScenario: setScenario,
    mockSSE: mockSSE,
    dispatchSseEvent: dispatchSseEvent,
    getBalanceSnapshot: getBalanceSnapshot,
    simulatePositionOpened: simulatePositionOpened,
    simulatePositionClosed: simulatePositionClosed,
    runQ3BalanceDemo: runQ3BalanceDemo,
    runQ3PrincipalDemo: runQ3PrincipalDemo,
    simulatePrincipalDeposit: simulatePrincipalDeposit,
    simulatePrincipalWithdraw: simulatePrincipalWithdraw,
    checkInvD06: checkInvD06,
    checkInvD07: checkInvD07,
    checkInvD09: checkInvD09,
    getPrincipalSnapshot: getPrincipalSnapshot,
    getPrincipalTransactions: getPrincipalTransactions,
    getFxRate: getFxRate,
    formatMoney: formatMoney,
    FX_USD_JPY_MOCK: FX_USD_JPY_MOCK,
    FX_USD_JPY_STALE_MOCK: FX_USD_JPY_STALE_MOCK,
    formatPnl: formatPnl,
    formatPct: formatPct,
    BASE_TIME: BASE_TIME,
    labOhlcBars: labOhlcBars,
  };
})(typeof window !== "undefined" ? window : globalThis);
