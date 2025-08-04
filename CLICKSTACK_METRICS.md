# OpenTelemetry Metrics Integration with ClickStack

This document describes the OpenTelemetry metrics integration that has been added to send telemetry data from the `/invoke` endpoint to ClickStack.

## What Was Added

### 1. Dependencies
Added the following OpenTelemetry packages to `pyproject.toml`:
- `opentelemetry-api==1.22.0`
- `opentelemetry-sdk==1.22.0`
- `opentelemetry-exporter-otlp-proto-http==1.22.0`
- `opentelemetry-instrumentation-fastapi==0.43b0`

### 2. OpenTelemetry Setup
- Configured OpenTelemetry SDK with MeterProvider
- Set up OTLP HTTP exporter for ClickStack
- Added automatic FastAPI instrumentation
- Configured periodic metric export (every 10 seconds)

### 3. Custom Metrics
The following metrics are collected for the `/invoke` endpoint:

#### `invoke_requests_total` (Counter)
- **Description**: Total number of invoke requests
- **Labels**: `model_id`
- **Use Case**: Track request volume per model

#### `invoke_request_duration_seconds` (Histogram)
- **Description**: Duration of invoke requests in seconds
- **Labels**: `model_id`, `status` (success/error)
- **Use Case**: Monitor request latency and performance

#### `invoke_errors_total` (Counter)
- **Description**: Total number of invoke request errors
- **Labels**: `model_id`, `error_type`
- **Use Case**: Track error rates and types

#### `invoke_success_total` (Counter)
- **Description**: Total number of successful invoke requests
- **Labels**: `model_id`
- **Use Case**: Track success rates

## Configuration

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `OTEL_SERVICE_NAME` | Service name for metrics | `baseten-backend-take-home` | `my-service` |
| `CLICKSTACK_OTLP_ENDPOINT` | ClickStack OTLP endpoint | `http://localhost:4318` | `https://clickstack.example.com:4318` |
| `CLICKSTACK_OTLP_HEADERS` | Authentication headers | `""` | `"authorization=Bearer token,x-api-key=key"` |

### Example Configuration

```bash
# Basic configuration
export OTEL_SERVICE_NAME="baseten-backend-take-home"
export CLICKSTACK_OTLP_ENDPOINT="http://localhost:4318"

# With authentication
export CLICKSTACK_OTLP_HEADERS="authorization=Bearer your-api-token"
```

## Installation & Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # or with poetry/uv
   uv install
   ```

2. Configure environment variables (see above)

3. Start the application:
   ```bash
   python -m baseten_backend_take_home.main
   # or
   uvicorn baseten_backend_take_home.main:app --reload
   ```

## Testing Metrics

1. Send requests to the `/invoke` endpoint:
   ```bash
   curl -X POST http://localhost:8000/invoke \
     -H "Content-Type: application/json" \
     -d '{
       "worklet_input": {
         "model_id": "test-model",
         "input": [1, 2, 3, 4, 5]
       }
     }'
   ```

2. Metrics will be automatically exported to ClickStack every 10 seconds

3. Check your ClickStack dashboard to see the metrics:
   - Request counts per model
   - Response time distributions
   - Error rates and types
   - Success rates

## ClickStack Integration

The metrics are sent to ClickStack using the OpenTelemetry Protocol (OTLP) over HTTP. ClickStack will automatically:

1. Receive the metrics data
2. Store it in ClickHouse
3. Make it available for querying and visualization
4. Enable alerting and dashboards

## Troubleshooting

1. **Metrics not appearing in ClickStack**:
   - Check that `CLICKSTACK_OTLP_ENDPOINT` is correct
   - Verify authentication headers if required
   - Check application logs for export errors

2. **Import errors**:
   - Ensure all OpenTelemetry packages are installed
   - Run `pip install -r requirements.txt` or `uv install`

3. **Connection issues**:
   - Verify ClickStack endpoint is accessible
   - Check firewall/network configuration
   - Test connectivity with curl to the metrics endpoint

## Metrics Schema

All metrics include the following resource attributes:
- `service.name`: Service identifier
- `service.version`: Application version
- `service.namespace`: Service namespace (baseten)

Individual metrics include relevant labels for filtering and aggregation in ClickStack.