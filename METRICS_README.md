# Model Invocation Metrics System

This document describes the comprehensive metrics system implemented for monitoring model invocation performance and statistics.

## Overview

The metrics system provides:
- **Real-time monitoring** of model invocations
- **Historical tracking** of invocation success/failure rates
- **Performance metrics** including latency and throughput
- **Visualization** through Grafana dashboards
- **Prometheus integration** for metrics collection

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │───▶│   Prometheus    │───▶│    Grafana      │
│   (Port 8000)   │    │   (Port 9090)   │    │   (Port 3000)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│ Metrics Storage │
│ (In-Memory)     │
└─────────────────┘
```

## API Endpoints

### 1. Enhanced `/invoke` Endpoint

The original `/invoke` endpoint now automatically collects and stores metrics:

**Request:**
```json
{
  "worklet_input": {
    "model_id": "gpt-3.5",
    "input": [1, 2, 3, 4, 5]
  }
}
```

**Response:**
```json
{
  "worklet_output": [6, 7, 8, 9, 10],
  "success": true,
  "latency_ms": 150,
  "error_log": ""
}
```

### 2. `/metrics/history` - Invocation History

Get detailed history of model invocations with optional filtering and pagination.

**Parameters:**
- `model_id` (optional): Filter by specific model
- `limit` (optional): Number of records to return (default: 100)
- `offset` (optional): Number of records to skip (default: 0)

**Example Request:**
```bash
curl "http://localhost:8000/metrics/history?model_id=gpt-3.5&limit=10"
```

**Example Response:**
```json
{
  "history": [
    {
      "id": 1,
      "model_id": "gpt-3.5",
      "timestamp": "2024-01-15T10:30:00Z",
      "success": true,
      "latency_ms": 150,
      "error_log": "",
      "input_size": 5,
      "output_size": 5
    }
  ],
  "total_count": 1,
  "offset": 0,
  "limit": 10
}
```

### 3. `/metrics/stats` - Success/Failure Statistics

Get comprehensive statistics for model performance.

**Parameters:**
- `model_id` (optional): Get stats for specific model

**Example Request:**
```bash
curl "http://localhost:8000/metrics/stats?model_id=gpt-3.5"
```

**Example Response:**
```json
{
  "stats": {
    "gpt-3.5": {
      "model_id": "gpt-3.5",
      "total_invocations": 100,
      "successful_invocations": 95,
      "failed_invocations": 5,
      "success_rate": 95.0,
      "failure_rate": 5.0,
      "average_latency_ms": 145.5,
      "total_latency_ms": 14550,
      "min_latency_ms": 50,
      "max_latency_ms": 300,
      "last_invocation": "2024-01-15T10:30:00Z"
    }
  }
}
```

### 4. `/metrics` - Prometheus Metrics

Exposes Prometheus-compatible metrics for scraping.

**Example Metrics:**
```
# HELP model_invocations_total Total number of model invocations
# TYPE model_invocations_total counter
model_invocations_total{model_id="gpt-3.5",status="success"} 95
model_invocations_total{model_id="gpt-3.5",status="failure"} 5

# HELP model_invocation_latency_seconds Latency of model invocations in seconds
# TYPE model_invocation_latency_seconds histogram
model_invocation_latency_seconds_bucket{model_id="gpt-3.5",le="0.1"} 10
model_invocation_latency_seconds_bucket{model_id="gpt-3.5",le="0.5"} 80
model_invocation_latency_seconds_bucket{model_id="gpt-3.5",le="1.0"} 95
```

## Prometheus Metrics

The system exposes the following metrics:

| Metric Name | Type | Description | Labels |
|-------------|------|-------------|--------|
| `model_invocations_total` | Counter | Total number of invocations | `model_id`, `status` |
| `model_invocation_latency_seconds` | Histogram | Latency distribution | `model_id` |
| `model_active_invocations` | Gauge | Currently active invocations | `model_id` |
| `model_total_invocations` | Gauge | Total invocations per model | `model_id` |
| `model_success_rate` | Gauge | Success rate as percentage | `model_id` |

## Grafana Dashboard

The included Grafana dashboard provides:

### Visualizations:
1. **Total Invocations per Model** - Real-time counters
2. **Success Rate by Model** - Percentage success rates
3. **Invocation Rate** - Requests per minute over time
4. **Response Time Percentiles** - 50th, 95th, 99th percentiles
5. **Active Invocations** - Current concurrent requests
6. **Success vs Failure Pie Chart** - Overall success/failure ratio
7. **Error Rate Over Time** - Failure percentage trends

### Features:
- **Real-time updates** (30-second refresh)
- **Model filtering** - Filter by specific model ID
- **Time range selection** - Custom time periods
- **Interactive charts** - Zoom, pan, and drill-down

## Setup and Installation

### 1. Install Dependencies

```bash
poetry install
```

### 2. Start the Complete Stack

```bash
docker-compose up -d
```

This will start:
- **Main Application** (localhost:8000)
- **Mock Server** (localhost:8001)
- **Prometheus** (localhost:9090)
- **Grafana** (localhost:3000)

### 3. Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Main API | http://localhost:8000 | - |
| Swagger UI | http://localhost:8000/docs | - |
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3000 | admin/admin |

### 4. Configure Grafana

1. Login to Grafana (admin/admin)
2. The Prometheus datasource is automatically configured
3. The "Model Invocation Metrics" dashboard is automatically loaded

## Usage Examples

### Testing the System

1. **Generate some test invocations:**
```bash
# Successful invocation
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "worklet_input": {
      "model_id": "gpt-3.5",
      "input": [1, 2, 3, 4, 5]
    }
  }'

# Another model
curl -X POST "http://localhost:8000/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "worklet_input": {
      "model_id": "bert-base",
      "input": [10, 20, 30]
    }
  }'
```

2. **Check metrics:**
```bash
# View history
curl "http://localhost:8000/metrics/history"

# View stats
curl "http://localhost:8000/metrics/stats"

# View Prometheus metrics
curl "http://localhost:8000/metrics"
```

3. **View in Grafana:**
   - Open http://localhost:3000
   - Navigate to "Model Invocation Metrics" dashboard
   - Watch real-time metrics update

### Load Testing

Use the provided `load_test.js` script to generate load and observe metrics:

```bash
node baseten_backend_take_home/load_test.js
```

## Monitoring and Alerting

### Recommended Alerts

1. **High Error Rate:**
   - Trigger when error rate > 5% for 5 minutes
   - Query: `rate(model_invocations_total{status="failure"}[5m]) / rate(model_invocations_total[5m]) * 100 > 5`

2. **High Latency:**
   - Trigger when 95th percentile > 2 seconds
   - Query: `histogram_quantile(0.95, rate(model_invocation_latency_seconds_bucket[5m])) > 2`

3. **No Activity:**
   - Trigger when no invocations for 10 minutes
   - Query: `rate(model_invocations_total[10m]) == 0`

### Performance Optimization

Monitor these metrics for optimization opportunities:

- **Latency Distribution** - Identify slow requests
- **Error Patterns** - Analyze failure causes
- **Load Distribution** - Balance across models
- **Resource Usage** - Track concurrent requests

## Troubleshooting

### Common Issues

1. **Prometheus not scraping:**
   - Check if `/metrics` endpoint is accessible
   - Verify Prometheus configuration in `prometheus.yml`

2. **Grafana shows no data:**
   - Confirm Prometheus datasource is configured
   - Check if metrics are being generated

3. **High memory usage:**
   - Metrics are stored in-memory
   - Consider implementing data retention policies

### Debug Commands

```bash
# Check if metrics endpoint works
curl http://localhost:8000/metrics

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# View Grafana logs
docker logs grafana
```

## Best Practices

1. **Model ID Consistency:** Use consistent model IDs across invocations
2. **Error Handling:** Ensure all errors are properly logged
3. **Resource Monitoring:** Monitor memory usage with large datasets
4. **Dashboard Maintenance:** Regular dashboard updates and optimization
5. **Alert Configuration:** Set up appropriate alerting thresholds

## Future Enhancements

1. **Persistent Storage:** Move from in-memory to database storage
2. **Advanced Analytics:** Add trend analysis and predictions
3. **Custom Metrics:** Support for business-specific metrics
4. **Multi-tenant Support:** Metrics isolation per organization
5. **Export Capabilities:** Data export for external analysis 