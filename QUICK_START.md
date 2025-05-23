# Strategy Analysis System - Quick Start Guide

This guide provides essential information for quickly getting started with the Strategy Analysis System in a production environment.

## System Overview

The Strategy Analysis System analyzes trading strategy backtest results, calculates metrics, and provides visualization through a web dashboard. The system consists of:

1. **Data Pipeline** - Processes backtests and generates metrics
2. **API Server** - Serves analysis data through REST endpoints
3. **Web Dashboard** - User interface for visualization and comparison
4. **Monitoring** - Ensures system health and reliability

## Quick Start Commands

### 1. Start the Complete System

```bash
./production_deploy.sh start
```

This will run the data pipeline, start the API server, and launch the dashboard.

### 2. Check System Status

```bash
./production_deploy.sh status
```

### 3. Run System Health Check

```bash
./system_monitor.py
```

### 4. Stop the System

```bash
./production_deploy.sh stop
```

## Key URLs

Once the system is running:

- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health
- **Web Dashboard**: http://localhost:3000

## Key API Endpoints

- **Strategy Summary**: `GET /v1/analysis/summary`
- **Strategy Weights**: `GET /v1/analysis/weights`

## File Locations

- **Configuration**: `config/`
- **Data Files**: `data/`
- **Logs**: `logs/`
- **Backtest Results**: `data/results/`

## Workflow for Adding New Backtest Data

1. Place new backtest result files in `data/results/`
2. Run the data pipeline:
   ```bash
   ./production_deploy.sh pipeline
   ```
3. View updated results in the dashboard

## Monitoring and Alerts

The monitoring system checks:

- API server health and response time
- Dashboard availability
- Data quality and freshness
- System resources

Run with email alerts:
```bash
./system_monitor.py --alerts
```

## Log Management

To prevent logs from consuming too much disk space, use the built-in log rotation:

```bash
# Rotate logs using the built-in script
./production_deploy.sh logs

# Or run the rotation script directly
./rotate_logs.sh
```

## Backup and Recovery

The system includes built-in backup and recovery functionality:

```bash
# Create a complete system backup
./backup_restore.sh backup

# List available backups
./backup_restore.sh list

# Restore from the most recent backup
./backup_restore.sh restore
```

## Common Issues

1. **API Server 500 Errors**:
   - Check data files for NaN values
   - Verify API server logs

2. **Missing Data**:
   - Ensure backtest results exist in `data/results/`
   - Run the data pipeline

3. **Dashboard Connection Issues**:
   - Verify API server is running
   - Check dashboard logs

## Additional Resources

- [Full Production System Guide](PRODUCTION_SYSTEM_GUIDE.md)
- [API Documentation](api_docs/rest_api.md)
- [Troubleshooting Guide](not_created_yet.md)
