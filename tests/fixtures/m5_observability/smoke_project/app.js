// Sample app file
function handleRequest(req) {
  const request_id = req.headers['x-request-id'];
  const trace_id = req.headers['x-trace-id'];
  const latency_ms = Date.now() - req.startTime;
  const status = 200;
  console.log({request_id, trace_id, latency_ms, status});
  return {status, latency_ms};
}

