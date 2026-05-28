/**
 * Live SSE client — connects to FastAPI /api/v1/events/stream (M4.2).
 */
(function (global) {
  "use strict";

  const SSE_EVENTS = [
    "state_changed",
    "markov_update",
    "health_degraded",
    "health_recovered",
    "position_opened",
    "position_closed",
    "nightly_report_ready",
    "mode_changed",
    "emergency_stop_triggered",
    "alert_added",
    "strategy_applied",
  ];

  let eventSource = null;
  let connected = false;

  function useMockMode() {
    const params = new URLSearchParams(global.location.search);
    return params.get("mock") === "1";
  }

  function notifyConnection(state) {
    connected = state;
    global.document.dispatchEvent(
      new CustomEvent("sse_connection_changed", { detail: { connected: state } }),
    );
  }

  function handlePayload(eventName, detail) {
    if (global.YoRuuMockData && global.YoRuuMockData.dispatchSseEvent) {
      global.YoRuuMockData.dispatchSseEvent(eventName, detail);
      return;
    }
    global.document.dispatchEvent(new CustomEvent(eventName, { detail: detail }));
  }

  function connect(streamUrl) {
    if (useMockMode() || eventSource) {
      return;
    }
    eventSource = new EventSource(streamUrl);
    eventSource.onopen = function () {
      notifyConnection(true);
    };
    eventSource.onerror = function () {
      notifyConnection(false);
    };
    SSE_EVENTS.forEach(function (name) {
      eventSource.addEventListener(name, function (ev) {
        try {
          const detail = JSON.parse(ev.data);
          handlePayload(name, detail);
        } catch (err) {
          console.error("[YoRuu SSE] parse error", name, err);
        }
      });
    });
  }

  function disconnect() {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
    notifyConnection(false);
  }

  function isLive() {
    return connected && !useMockMode();
  }

  function autoConnect() {
    if (useMockMode()) {
      return;
    }
    connect("/api/v1/events/stream");
  }

  global.YoRuuSse = {
    connect: connect,
    disconnect: disconnect,
    isLive: isLive,
    useMockMode: useMockMode,
    autoConnect: autoConnect,
  };

  if (global.document.readyState === "loading") {
    global.document.addEventListener("DOMContentLoaded", autoConnect);
  } else {
    autoConnect();
  }
})(typeof window !== "undefined" ? window : globalThis);
