// Test file: Helper functions with mixed signal coverage
// Some functions have signals, some don't

export function helperWithSignals() {
  const latency_ms = 50;
  const status = 200;
  const error_code = 0;
  const request_id = 'req-123';
  const trace_id = 'trace-456';
  const hw_ts_ms = Date.now();
  
  // All signals present
  return { latency_ms, status, error_code, request_id, trace_id, hw_ts_ms };
}

export function helperWithoutSignals() {
  // Missing all signals
  return { data: 'some data' };
}

export function helperPartialSignals() {
  const status = 200;
  const error_code = 0;
  // Missing: latency_ms, request_id, trace_id, hw_ts_ms
  return { status, error_code };
}

