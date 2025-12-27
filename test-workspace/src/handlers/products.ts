// Test file: Missing some signals (should trigger WARN)
// Has: status
// Missing: latency_ms, error_code, request_id, trace_id, hw_ts_ms

export function getProduct(productId: string) {
  const product = { id: productId, name: 'Example Product', price: 99.99 };
  // Present: status (in return)
  console.log(`Fetched product ${productId} with status 200`); // Contains 'status'
  return { ...product, status: 200 };
}

export function listProducts() {
  // Missing all signals
  return { products: [] };
}

