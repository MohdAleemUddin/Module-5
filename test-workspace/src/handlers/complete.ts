// Test file: Has ALL required signals (should PASS)
// This file demonstrates proper observability implementation

export function handleRequest(req: any, res: any) {
  // All required signals present
  const latency_ms = Date.now() - req.startTime;
  const status = 200;
  const error_code = 0;
  const request_id = req.headers['x-request-id'] || generateId();
  const trace_id = req.headers['x-trace-id'] || generateId();
  const hw_ts_ms = Date.now();
  
  // Proper logging with all signals
  logger.info({
    latency_ms,
    status,
    error_code,
    request_id,
    trace_id,
    hw_ts_ms
  }, 'Request processed successfully');
  
  res.status(status).json({ success: true });
}

function generateId(): string {
  return Math.random().toString(36).substring(2, 15);
}

// Mock logger
const logger = {
  info: (data: any, message: string) => {
    console.log(message, data);
  }
};

