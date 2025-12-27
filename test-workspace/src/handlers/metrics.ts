// Test file: Contains dynamic keys (for cardinality/dynamic key detection)
// Also missing signals

export function logUserActivity(userId: string, activity: string) {
  // Dynamic keys - should trigger HARD block
  const labels = {
    [`user.${userId}`]: activity,  // Dynamic key
    [`order.${activity}`]: userId,  // Dynamic key
    'static_key': 'static_value'   // OK
  };
  
  // High cardinality values
  const userUUID = '12345678-1234-1234-1234-123456789012';
  const longHexToken = 'abcdef1234567890abcdef1234567890';
  
  console.log('User activity logged', labels);
  // Missing: latency_ms, status, error_code, request_id, trace_id, hw_ts_ms
}

export function trackMetrics(endpoint: string) {
  // More dynamic keys
  const tags = {
    [`endpoint.${endpoint}`]: 'value',  // Dynamic key
    'method': 'GET'
  };
  
  return tags;
}


// <CC_OBS_SNIPPET>
// sample_rate=1
// labels=[endpoint,method,status]
// counter:<name>
// histogram:<name>
// timer:<name>
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
