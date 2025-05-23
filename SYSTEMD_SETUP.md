# Strategy Analysis System - Systemd Integration

This document describes how to set up the Strategy Analysis System to run as a system service using systemd on Linux.

## Available Service Files

The following service files are provided in this directory:

- `strategy-api.service` - API server service
- `strategy-monitor.service` - System monitoring service 
- `strategy-logrotate.service` - Log rotation service
- `strategy-logrotate.timer` - Weekly timer for log rotation

## Installation Instructions

### Setting Up System Services

1. Copy the service files to systemd directory:

```bash
sudo cp strategy-*.service strategy-*.timer /etc/systemd/system/
```

2. Reload systemd configuration:

```bash
sudo systemctl daemon-reload
```

3. Enable and start the services:

```bash
# API Server
sudo systemctl enable strategy-api.service
sudo systemctl start strategy-api.service

# Monitoring
sudo systemctl enable strategy-monitor.service
sudo systemctl start strategy-monitor.service

# Log rotation (timer)
sudo systemctl enable strategy-logrotate.timer
sudo systemctl start strategy-logrotate.timer
```

### Setting Up Scheduled Tasks with Cron

Alternatively, you can use cron for scheduled tasks:

1. Copy the cron file to cron.d directory:

```bash
sudo cp strategy-analysis.cron /etc/cron.d/strategy-analysis
```

2. Set proper permissions:

```bash
sudo chmod 644 /etc/cron.d/strategy-analysis
```

## Checking Service Status

```bash
# Check API server status
sudo systemctl status strategy-api

# Check monitoring service status
sudo systemctl status strategy-monitor

# Check log rotation timer status
sudo systemctl status strategy-logrotate.timer
```

## Viewing Service Logs

```bash
# View API server logs
sudo journalctl -u strategy-api

# View monitoring logs
sudo journalctl -u strategy-monitor 

# View log rotation logs
sudo journalctl -u strategy-logrotate
```

## Customizing Services

To modify environment variables or other service parameters:

1. Edit the service file:

```bash
sudo systemctl edit strategy-api.service
```

2. Reload and restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart strategy-api.service
```
