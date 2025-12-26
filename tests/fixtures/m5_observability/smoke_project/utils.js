// Utility functions
function getCurrentTimestamp() {
  return { hw_ts_ms: Date.now() };
}

function logError(error_code, message) {
  console.error({error_code, message});
}

module.exports = { getCurrentTimestamp, logError };

