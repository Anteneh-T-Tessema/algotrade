# Strategy Analysis System - Production Documentation

## Overview

The Strategy Analysis System is a comprehensive platform for analyzing trading strategy backtests, generating performance reports, and providing a web dashboard for strategy comparison and ensemble weighting.

This document provides detailed information for operating the system in a production environment.

## System Components

The system consists of four primary components:

1. **Data Pipeline** - Processes backtest results and generates summary metrics and weights
2. **API Server** - Provides access to analysis data through RESTful endpoints
3. **Web Dashboard** - User interface for visualizing and comparing strategy performance
4. **Monitoring System** - Ensures system health and reliability

## System Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│                     │     │                     │
│   Backtest Results  │────▶│   Data Pipeline     │
│                     │     │                     │
└─────────────────────┘     └──────────┬──────────┘
                                       │
                                       │ writes
                                       ▼
┌─────────────────────┐     ┌─────────────────────┐
│                     │     │                     │
│   Web Dashboard     │◀───▶│   API Server        │◀────┐
│                     │     │                     │     │
└─────────────────────┘     └─────────────────────┘     │
                                                         │
┌─────────────────────┐                                  │
│                     │                                  │
│   Monitoring System │──────────────────────────────────┘
│                     │
└─────────────────────┘
```

## Installation & Setup

### System Requirements

- Python 3.9 or higher
- Node.js 16 or higher (for web dashboard)
- 4GB RAM minimum, 8GB recommended
- 2 CPU cores minimum, 4 cores recommended

### Installation

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd strategy-analysis-system
   ```

2. Setup the environment:
   ```bash
   # Create and activate a virtual environment
   python -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. Install web dashboard dependencies (if needed):
   ```bash
   cd web_dashboard
   npm install
   cd ..
   ```

4. Verify system configuration:
   ```bash
   # Run the production deploy script in check mode
   ./production_deploy.sh status
   ```

## Production Deployment

The system includes a comprehensive deployment script that manages all aspects of the production environment.

### Starting the System

```bash
./production_deploy.sh start
```

This command will:
1. Check the environment and install dependencies
2. Run the data pipeline to generate analysis files
3. Start the API server
4. Start the web dashboard (if available)
5. Perform health checks
6. Save the system state

### Managing Individual Components

```bash
# Run only the data pipeline
./production_deploy.sh pipeline

# Start only the API server
./production_deploy.sh api

# Start only the dashboard
./production_deploy.sh dashboard
```

### Stopping the System

```bash
./production_deploy.sh stop
```

### Checking System Status

```bash
./production_deploy.sh status
```

## API Reference

The API server provides the following endpoints:

### Health Check

```
GET /health
```

Returns the health status of the API server, including uptime and version.

### Summary Report

```
GET /v1/analysis/summary
```

Returns the strategy summary report, containing performance metrics for each strategy across different market types.

Example response:
```json
[
  {
    "strategy": "TrendFollowing",
    "market_type": "sideways market",
    "total_return": 0.0,
    "win_rate": 0.0,
    "sharpe_ratio": 0.0,
    "max_drawdown_pct": null
  },
  {
    "strategy": "GridTrading",
    "market_type": "normal market",
    "total_return": 1.47,
    "win_rate": 1.0,
    "sharpe_ratio": 0.38,
    "max_drawdown_pct": null
  }
]
```

### Strategy Weights

```
GET /v1/analysis/weights
```

Returns the strategy weights for the ensemble strategy, organized by market type.

Example response:
```json
{
  "normal market": {
    "Arbitrage": 0.5869565217391305,
    "DCA": 0.0,
    "GridTrading": 0.41304347826086957,
    "MeanReversion": 0.0,
    "Scalping": 0.0,
    "TrendFollowing": 0.0
  },
  "volatile market": {
    "Arbitrage": 0.038461538461538464,
    "DCA": 0.34615384615384615,
    "GridTrading": 0.0,
    "MeanReversion": 0.0,
    "Scalping": 0.6153846153846154,
    "TrendFollowing": 0.0
  }
}
```

### API Documentation

```
GET /docs
```

Interactive API documentation using Swagger UI.

## Monitoring

The system includes a comprehensive monitoring script that checks the health and performance of all components.

### Running the Monitor

```bash
./system_monitor.py
```

This will:
1. Check the API server health and response time
2. Check the dashboard status
3. Validate data files
4. Monitor system resources (CPU, memory, disk)
5. Check for errors in log files
6. Generate alerts for any issues

### Monitoring Options

```bash
# Output results as JSON
./system_monitor.py --json

# Enable email alerts
./system_monitor.py --alerts

# Set custom API server host and port
./system_monitor.py --host localhost --port 8000
```

### Monitoring Integration

The monitoring script can be integrated with external monitoring systems like Prometheus, Nagios, or CloudWatch by using the JSON output and exit codes:

- Exit code 0: System is healthy
- Exit code 1: System is degraded
- Exit code 2: System is critical
- Exit code 3: Monitoring error

## Troubleshooting

### Common Issues

#### API Server 500 Errors

If the API server returns HTTP 500 errors, check the following:

1. **Data Format Issues**:
   Check the log file for specific errors. NaN/Infinity values in the summary report can cause JSON serialization errors.

2. **Missing Data Files**:
   Ensure that `data/summary_report.csv` and `data/weight_table.json` exist and are valid.

3. **Insufficient Resources**:
   Check system resource usage with the monitoring tool. The API server may fail if resources are exhausted.

#### Data Pipeline Failures

If the data pipeline fails:

1. **Check Input Data**:
   Ensure that strategy backtest result files exist in the `data/results` directory.

2. **Check Log Files**:
   Look for specific error messages in the data pipeline logs.

3. **Verify Python Environment**:
   Ensure all required packages are installed and up to date.

#### Dashboard Connection Issues

If the dashboard cannot connect to the API:

1. **Cross-Origin Issues**:
   Check that CORS is properly configured in the API server.

2. **Network Issues**:
   Verify that the dashboard can reach the API server at the configured URL.

3. **API Endpoint Errors**:
   Check that the API endpoints are functioning correctly using a tool like curl.

### Log File Locations

- API Server Logs: `logs/api_server_*.log`
- Data Pipeline Logs: `logs/data_pipeline_*.log`
- Dashboard Logs: `logs/dashboard_*.log`
- System Run Logs: `logs/system_run_*.log`
- Monitor Logs: `logs/monitor_*.log`

## Maintenance Procedures

### Backup and Recovery

The system includes a comprehensive backup and restore script for data protection.

#### Creating Backups

```bash
# Create a complete system backup
./backup_restore.sh backup
```

This will:
1. Create a timestamped compressed archive (.tar.gz)
2. Include all data and configuration files
3. Verify the backup integrity
4. Clean up old backups beyond the retention period (default: 30 days)

#### Listing Backups

```bash
# View available backups
./backup_restore.sh list
```

#### Restoring from Backup

```bash
# Restore from the most recent backup
./backup_restore.sh restore

# Restore from a specific backup file
./backup_restore.sh restore backups/system_backup_20250520_120000.tar.gz
```

The restore process:
1. Verifies backup integrity
2. Stops running services
3. Restores data and configuration files
4. Provides instructions for restarting the system

### Updating the System

To update the system:

1. **Pull the latest code**:
   ```bash
   git pull origin main
   ```

2. **Update dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Restart the system**:
   ```bash
   ./production_deploy.sh restart
   ```

### Log Rotation

The system provides two options for log rotation:

1. **Using logrotate** (Linux/Unix systems):
   
   A configuration file (`logrotate.conf`) is provided that can be used with the system's logrotate utility:
   
   ```bash
   # Copy to system logrotate directory
   sudo cp logrotate.conf /etc/logrotate.d/strategy-analysis
   
   # Test the configuration
   sudo logrotate -d /etc/logrotate.d/strategy-analysis
   ```
   
   The configuration rotates:
   - API server logs: daily, keeping 7 rotations
   - Data pipeline logs: weekly, keeping 4 rotations
   - Dashboard logs: daily, keeping 7 rotations
   - Monitor logs: weekly, keeping 4 rotations

2. **Manual rotation script**:
   
   A standalone script (`rotate_logs.sh`) is provided for systems without logrotate:
   
   ```bash
   # Configure rotation settings
   vi rotate_logs.sh  # Edit ROTATION_MODE, SIZE_THRESHOLD, and MAX_AGE_DAYS
   
   # Run manually
   ./rotate_logs.sh
   
   # Or add to crontab to run daily at midnight
   # 0 0 * * * /path/to/rotate_logs.sh
   ```
   
   The script supports two rotation modes:
   - Size-based: Rotates logs when they exceed a certain size
   - Date-based: Archives all logs with a timestamp pattern

### Running as a System Service

For production deployments on Linux, you can run the system components as systemd services.
See [SYSTEMD_SETUP.md](SYSTEMD_SETUP.md) for detailed instructions on:

- Setting up API server as a systemd service
- Running the monitoring system as a service
- Using systemd timers for scheduled tasks
- Viewing service logs

## Integration Points

### Adding New Strategies

To add new strategies to the analysis:

1. Place the strategy backtest results in `data/results/`
2. Run the data pipeline to update the analysis

### External System Integration

The system can be integrated with external systems through:

1. **API endpoints** - Other systems can fetch analysis data
2. **Webhooks** - Configure notifications on system events
3. **Data exports** - Analysis results can be exported to CSV/JSON

## Support & Contact

For support or questions, contact:

- Technical Support: support@example.com
- System Administrator: admin@example.com

## Appendix

### Environment Variables

The system supports the following environment variables:

- `PORT` - API server port (default: 8000)
- `HOST` - API server host (default: 0.0.0.0)
- `DEBUG` - Enable debug mode (default: false)
- `ARCHIVE_RESULTS` - Archive result files after processing (default: false)

### Deployment Checklist

- [ ] Python 3.9+ installed
- [ ] Node.js 16+ installed (for dashboard)
- [ ] Required ports are open
- [ ] Sufficient disk space
- [ ] Production deploy script is executable
- [ ] Monitoring is configured
- [ ] Backup procedure is established
