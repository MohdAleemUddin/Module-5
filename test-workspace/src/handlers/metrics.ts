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

