// Test file: Contains endpoint definitions (for endpoint discovery)
// Also missing signals

import express from 'express';

const router = express.Router();

// Endpoint 1: Missing all signals
router.get('/orders/:id', (req, res) => {
  const orderId = req.params.id;
  // Missing: latency_ms, status, error_code, request_id, trace_id, hw_ts_ms
  res.json({ orderId });
});

// Endpoint 2: Missing all signals
router.post('/orders', (req, res) => {
  // Missing all signals
  res.status(201).json({ created: true });
});

// Endpoint 3: Missing all signals
router.put('/orders/:id', (req, res) => {
  // Missing all signals
  res.status(200).json({ updated: true });
});

export default router;

