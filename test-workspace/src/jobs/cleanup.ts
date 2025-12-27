// Test file: Background job (for job discovery)
// Missing signals

// Cron job scheduled to run daily
export function dailyCleanupJob() {
  console.log('Running daily cleanup job');
  // Missing: latency_ms, status, error_code, request_id, trace_id, hw_ts_ms
  // This is a background job that should also have observability
}

// Scheduled task
export function scheduledTask() {
  // Missing all signals
  console.log('Scheduled task executed');
}

