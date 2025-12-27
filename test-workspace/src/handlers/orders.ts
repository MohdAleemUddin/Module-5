// Test file: Missing all required signals (should trigger HARD block)
// This file has NO observability signals

export function processOrder(orderId: string, userId: string) {
  console.log(`Processing order ${orderId} for user ${userId}`);
  // Missing: latency_ms, status, error_code, request_id, trace_id, hw_ts_ms
  return { orderId, userId, status: 'received' };
}

export function getOrderDetails(orderId: string) {
  // Missing all signals
  return { id: orderId, items: [] };
}






// <CC_OBS_SNIPPET>
// TODO: Import logger if not already available
//import { logger } from './logger'; // or your logger module

const duration = Date.now() - startTime; // Calculate latency
const statusCode = 200; // HTTP status code
const errorCode = 0; // Error code (0 = success)
const reqId = req.headers['x-request-id'] || generateId(); // Request ID
const traceId = req.headers['x-trace-id'] || generateId(); // Trace ID

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
