// Test file: Contains PII/secrets (for PII redaction testing)
// Also missing all signals

export function processPayment(paymentId: string, amount: number) {
  // PII/Secrets in this file:
  const apiKey = "Bearer sk_live_abc123xyz789";
  const userEmail = "customer@example.com";
  const authToken = "<REDACTED:sha256:6d55ad8f4418>
  
  console.log(`Processing payment ${paymentId} for amount ${amount}`);
  // Missing: latency_ms, status, error_code, request_id, trace_id, hw_ts_ms
  
  // Use secrets (should be redacted)
  const headers = {
    'Authorization': apiKey,
    'X-User-Email': userEmail
  };
  
  return { paymentId, amount, headers };
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
function getCorrelationIds(input: any): { request_id: string; trace_id: string } {
    // Extract correlation IDs from request headers or generate new ones
    const request_id = input?.headers?.['x-request-id'] || input?.request_id || generateId();
    const trace_id = input?.headers?.['x-trace-id'] || input?.trace_id || generateId();
    return { request_id, trace_id };
}

function generateId(): string {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}
// </CC_OBS_SNIPPET>
