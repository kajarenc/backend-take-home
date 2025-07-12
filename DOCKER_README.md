# Docker Setup for Baseten Backend Take Home

This setup allows you to run the complete application stack using Docker Compose with optimized multi-stage builds.

## Services

- **main-app**: The main FastAPI application (runs on port 8000)
  - GraphQL API available at `/graphql`
  - HTTP API available at `/invoke`
  - Home page available at `/`
  - Health check endpoint at `/`

- **mock-server**: The worklet mock server (runs on port 8001)
  - Mock invoke endpoint available at `/invoke`
  - Health check endpoint at `/`

- **prometheus**: Metrics collection service (runs on port 9090)
  - Metrics dashboard available at `/`
  - Configuration loaded from `prometheus.yml`

- **grafana**: Metrics visualization dashboard (runs on port 3000)
  - Username: admin, Password: admin
  - Dashboards pre-configured for application metrics

## Optimizations

- **Multi-stage builds**: Reduced image size by separating build dependencies from runtime
- **Health checks**: Built-in health monitoring for all services
- **Restart policies**: Automatic service recovery on failure
- **Security**: Non-root user execution for application containers
- **Dependency management**: Efficient Poetry installation with `--no-root` flag

## Quick Start

1. **Build and run all services:**
   ```bash
   docker-compose up --build
   ```

2. **Run in detached mode:**
   ```bash
   docker-compose up -d --build
   ```

3. **Stop the services:**
   ```bash
   docker-compose down
   ```

4. **Stop services and remove volumes:**
   ```bash
   docker-compose down -v
   ```

## Accessing the Services

- **Main Application**: http://localhost:8000
- **GraphQL Playground**: http://localhost:8000/graphql
- **Mock Server**: http://localhost:8001 (internal communication)
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## Development

For development, you can rebuild specific services:

```bash
# Rebuild only the main app
docker-compose up --build main-app

# Rebuild only the mock server
docker-compose up --build mock-server

# Rebuild without cache
docker-compose build --no-cache
```

## Monitoring

### Logs

View logs for all services:
```bash
docker-compose logs -f
```

View logs for a specific service:
```bash
docker-compose logs -f main-app
docker-compose logs -f mock-server
docker-compose logs -f prometheus
docker-compose logs -f grafana
```

### Health Checks

Check service health:
```bash
# Check all services
docker-compose ps

# Check specific service health
docker-compose exec main-app curl -f http://localhost:8000/
docker-compose exec mock-server curl -f http://localhost:8001/
```

## Network Communication

The services communicate within a Docker network:
- The main app connects to the mock server using the service name: `http://mock-server:8001`
- All services are accessible from your host machine on their respective ports
- Health checks ensure services are ready before dependent services start

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 8000, 8001, 9090, and 3000 are not in use
2. **Build failures**: Try rebuilding without cache: `docker-compose build --no-cache`
3. **Service startup**: Check health status with `docker-compose ps`

### Debugging

```bash
# Enter a running container
docker-compose exec main-app bash

# Check container logs
docker-compose logs main-app

# Restart a specific service
docker-compose restart main-app
``` 