// Test file: Has some signals but missing critical ones
// Has: latency_ms, status, error_code
// Missing: request_id, trace_id, hw_ts_ms (critical)

export function processPartialRequest(data: any) {
  const latency_ms = 150;
  const status = 200;
  const error_code = 0;
  
  // Missing critical: request_id, trace_id, hw_ts_ms
  console.log(`Request processed in ${latency_ms}ms with status ${status}`);
  
  return { data, latency_ms, status, error_code };
}


// <CC_OBS_SNIPPET>
logger.info({
  latency_ms: duration,
  status: statusCode,
  error_code: errorCode || 0,
  request_id: reqId,
  trace_id: traceId,
  hw_ts_ms: Date.now()
}, 'Request processed');
// </CC_OBS_SNIPPET>



// <CC_OBS_SNIPPET>
function getCorrelationIds(input:any){ return { request_id:"<REQUEST_ID>", trace_id:"<TRACE_ID>" }; }
// </CC_OBS_SNIPPET>
