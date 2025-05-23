#!/usr/bin/env python3
"""
Strategy Analysis System Monitoring Tool

This script provides comprehensive monitoring of the strategy analysis system:
1. System component health checks
2. Performance metrics
3. Data quality metrics
4. System alerts
5. Status reporting

Can be run on a schedule or as a service.
"""
import os
import sys
import json
import time
import logging
import requests
import pandas as pd
import psutil
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("system-monitor")

# Get the project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
MONITOR_STATE_FILE = os.path.join(PROJECT_ROOT, ".monitor_state.json")

# Configuration
API_PID_FILE = os.path.join(PROJECT_ROOT, ".api_server.pid")
DASHBOARD_PID_FILE = os.path.join(PROJECT_ROOT, ".dashboard.pid")
SYSTEM_STATE_FILE = os.path.join(PROJECT_ROOT, ".system_state")
DEFAULT_API_PORT = 8000
DEFAULT_API_HOST = "localhost"
DEFAULT_DASHBOARD_PORT = 3000

# Monitoring thresholds
THRESHOLDS = {
    "api_response_time": 2.0,  # seconds
    "cpu_usage": 80.0,  # percent
    "memory_usage": 85.0,  # percent
    "disk_usage": 90.0,  # percent
    "log_file_size": 100 * 1024 * 1024,  # 100MB
    "data_freshness": 24 * 60 * 60  # 24 hours in seconds
}

# Alert recipients (if email alerts are enabled)
ALERT_RECIPIENTS = os.environ.get("ALERT_RECIPIENTS", "admin@example.com").split(",")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.example.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

# Helper class for colored terminal output
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"

class SystemMonitor:
    """Strategy Analysis System Monitor"""
    
    def __init__(self, api_host=DEFAULT_API_HOST, api_port=DEFAULT_API_PORT, 
                 dashboard_port=DEFAULT_DASHBOARD_PORT, enable_alerts=False, verbose=False):
        self.api_host = api_host
        self.api_port = api_port
        self.dashboard_port = dashboard_port
        self.api_base_url = f"http://{api_host}:{api_port}"
        self.dashboard_url = f"http://{api_host}:{dashboard_port}"
        self.enable_alerts = enable_alerts
        self.verbose = verbose
        self.alerts = []
        self.status = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "status": "unknown",
                "api_server": {
                    "status": "unknown",
                    "response_time": None,
                    "uptime": None
                },
                "dashboard": {
                    "status": "unknown"
                },
                "data_pipeline": {
                    "status": "unknown",
                    "data_freshness": None
                }
            },
            "resources": {
                "cpu": None,
                "memory": None,
                "disk": None
            },
            "data_quality": {
                "summary_report": {
                    "status": "unknown",
                    "record_count": None,
                    "last_modified": None
                },
                "weight_table": {
                    "status": "unknown",
                    "market_types": None,
                    "last_modified": None
                }
            },
            "alerts": []
        }
    
    def run_checks(self):
        """Run all system checks"""
        logger.info("Starting system checks...")
        
        # Check system components
        self.check_api_server()
        self.check_dashboard()
        self.check_data_files()
        
        # Check system resources
        self.check_system_resources()
        
        # Check logs
        self.check_log_files()
        
        # Determine overall system status
        self._determine_overall_status()
        
        # Save monitoring state
        self._save_state()
        
        # Send alerts if needed
        if self.enable_alerts and self.alerts:
            self._send_alerts()
        
        logger.info("System checks completed")
        return self.status
    
    def check_api_server(self):
        """Check API server health and performance"""
        logger.info("Checking API server...")
        
        try:
            # Check if process is running by PID
            api_pid = self._get_pid_from_file(API_PID_FILE)
            if api_pid and self._is_process_running(api_pid):
                self.status["system"]["api_server"]["status"] = "running"
                logger.info(f"API server process is running (PID: {api_pid})")
            else:
                self.status["system"]["api_server"]["status"] = "stopped"
                logger.warning("API server process is not running")
                self._add_alert("API server is not running", "high")
                return
            
            # Check health endpoint
            start_time = time.time()
            try:
                response = requests.get(f"{self.api_base_url}/health", timeout=5)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    health_data = response.json()
                    self.status["system"]["api_server"]["response_time"] = response_time
                    self.status["system"]["api_server"]["uptime"] = health_data.get("uptime")
                    
                    logger.info(f"API health check: OK (Response time: {response_time:.2f}s)")
                    
                    # Check response time against threshold
                    if response_time > THRESHOLDS["api_response_time"]:
                        logger.warning(f"API response time ({response_time:.2f}s) exceeds threshold ({THRESHOLDS['api_response_time']}s)")
                        self._add_alert(f"API response time is slow: {response_time:.2f}s", "medium")
                else:
                    self.status["system"]["api_server"]["status"] = "degraded"
                    logger.warning(f"API health check failed with status code: {response.status_code}")
                    self._add_alert(f"API health check failed: HTTP {response.status_code}", "high")
            except requests.RequestException as e:
                self.status["system"]["api_server"]["status"] = "degraded"
                logger.warning(f"Error connecting to API server: {str(e)}")
                self._add_alert(f"Cannot connect to API server: {str(e)}", "high")
        
        except Exception as e:
            logger.error(f"Error checking API server: {str(e)}")
            self.status["system"]["api_server"]["status"] = "unknown"
            self._add_alert(f"API server check failed: {str(e)}", "high")
    
    def check_dashboard(self):
        """Check dashboard status"""
        logger.info("Checking dashboard...")
        
        try:
            # Check if process is running by PID
            dashboard_pid = self._get_pid_from_file(DASHBOARD_PID_FILE)
            if dashboard_pid and self._is_process_running(dashboard_pid):
                self.status["system"]["dashboard"]["status"] = "running"
                logger.info(f"Dashboard process is running (PID: {dashboard_pid})")
            else:
                self.status["system"]["dashboard"]["status"] = "stopped"
                logger.warning("Dashboard process is not running")
                self._add_alert("Dashboard is not running", "medium")
                return
            
            # Try to connect to dashboard (simple connection test)
            try:
                response = requests.get(f"http://{self.api_host}:{self.dashboard_port}", timeout=5)
                if response.status_code == 200:
                    logger.info("Dashboard connection: OK")
                else:
                    self.status["system"]["dashboard"]["status"] = "degraded"
                    logger.warning(f"Dashboard connection test failed with status code: {response.status_code}")
                    self._add_alert(f"Dashboard connection test failed: HTTP {response.status_code}", "medium")
            except requests.RequestException as e:
                self.status["system"]["dashboard"]["status"] = "degraded"
                logger.warning(f"Error connecting to dashboard: {str(e)}")
                self._add_alert(f"Cannot connect to dashboard: {str(e)}", "medium")
        
        except Exception as e:
            logger.error(f"Error checking dashboard: {str(e)}")
            self.status["system"]["dashboard"]["status"] = "unknown"
            self._add_alert(f"Dashboard check failed: {str(e)}", "medium")
    
    def check_data_files(self):
        """Check data files for quality and freshness"""
        logger.info("Checking data files...")
        
        try:
            # Check summary report
            summary_path = os.path.join(DATA_DIR, "summary_report.csv")
            if os.path.exists(summary_path):
                # Check last modified time
                last_modified = os.path.getmtime(summary_path)
                last_modified_dt = datetime.fromtimestamp(last_modified)
                self.status["data_quality"]["summary_report"]["last_modified"] = last_modified_dt.isoformat()
                
                # Check data freshness
                data_age = time.time() - last_modified
                self.status["system"]["data_pipeline"]["data_freshness"] = data_age
                
                if data_age > THRESHOLDS["data_freshness"]:
                    logger.warning(f"Summary report data is stale: {data_age/3600:.1f} hours old")
                    self._add_alert(f"Summary report data is stale: {data_age/3600:.1f} hours old", "medium")
                
                # Check content
                try:
                    df = pd.read_csv(summary_path)
                    record_count = len(df)
                    self.status["data_quality"]["summary_report"]["record_count"] = record_count
                    self.status["data_quality"]["summary_report"]["status"] = "valid"
                    
                    logger.info(f"Summary report: Valid ({record_count} records)")
                    
                    # Check for empty data
                    if record_count == 0:
                        logger.warning("Summary report contains no records")
                        self.status["data_quality"]["summary_report"]["status"] = "empty"
                        self._add_alert("Summary report contains no records", "medium")
                    
                except Exception as e:
                    logger.warning(f"Error reading summary report: {str(e)}")
                    self.status["data_quality"]["summary_report"]["status"] = "invalid"
                    self._add_alert(f"Summary report is invalid: {str(e)}", "high")
            else:
                logger.warning("Summary report file not found")
                self.status["data_quality"]["summary_report"]["status"] = "missing"
                self._add_alert("Summary report file is missing", "high")
            
            # Check weight table
            weights_path = os.path.join(DATA_DIR, "weight_table.json")
            if os.path.exists(weights_path):
                # Check last modified time
                last_modified = os.path.getmtime(weights_path)
                last_modified_dt = datetime.fromtimestamp(last_modified)
                self.status["data_quality"]["weight_table"]["last_modified"] = last_modified_dt.isoformat()
                
                # Check content
                try:
                    with open(weights_path, 'r') as f:
                        weights = json.load(f)
                    
                    market_types = len(weights)
                    self.status["data_quality"]["weight_table"]["market_types"] = market_types
                    self.status["data_quality"]["weight_table"]["status"] = "valid"
                    
                    logger.info(f"Weight table: Valid ({market_types} market types)")
                    
                    # Check for empty data
                    if market_types == 0:
                        logger.warning("Weight table contains no market types")
                        self.status["data_quality"]["weight_table"]["status"] = "empty"
                        self._add_alert("Weight table contains no market types", "medium")
                    
                except Exception as e:
                    logger.warning(f"Error reading weight table: {str(e)}")
                    self.status["data_quality"]["weight_table"]["status"] = "invalid"
                    self._add_alert(f"Weight table is invalid: {str(e)}", "high")
            else:
                logger.warning("Weight table file not found")
                self.status["data_quality"]["weight_table"]["status"] = "missing"
                self._add_alert("Weight table file is missing", "high")
            
            # Determine data pipeline status
            if (self.status["data_quality"]["summary_report"]["status"] in ["valid", "empty"] and
                self.status["data_quality"]["weight_table"]["status"] in ["valid", "empty"]):
                self.status["system"]["data_pipeline"]["status"] = "operational"
            else:
                self.status["system"]["data_pipeline"]["status"] = "failed"
        
        except Exception as e:
            logger.error(f"Error checking data files: {str(e)}")
            self.status["system"]["data_pipeline"]["status"] = "unknown"
            self._add_alert(f"Data file check failed: {str(e)}", "high")
    
    def check_system_resources(self):
        """Check system resource usage"""
        logger.info("Checking system resources...")
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.status["resources"]["cpu"] = cpu_percent
            logger.info(f"CPU usage: {cpu_percent:.1f}%")
            
            if cpu_percent > THRESHOLDS["cpu_usage"]:
                logger.warning(f"High CPU usage: {cpu_percent:.1f}%")
                self._add_alert(f"High CPU usage: {cpu_percent:.1f}%", "medium")
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.status["resources"]["memory"] = memory_percent
            logger.info(f"Memory usage: {memory_percent:.1f}%")
            
            if memory_percent > THRESHOLDS["memory_usage"]:
                logger.warning(f"High memory usage: {memory_percent:.1f}%")
                self._add_alert(f"High memory usage: {memory_percent:.1f}%", "medium")
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            self.status["resources"]["disk"] = disk_percent
            logger.info(f"Disk usage: {disk_percent:.1f}%")
            
            if disk_percent > THRESHOLDS["disk_usage"]:
                logger.warning(f"High disk usage: {disk_percent:.1f}%")
                self._add_alert(f"High disk usage: {disk_percent:.1f}%", "high")
        
        except Exception as e:
            logger.error(f"Error checking system resources: {str(e)}")
            self._add_alert(f"System resource check failed: {str(e)}", "medium")
    
    def check_log_files(self):
        """Check log files for issues"""
        logger.info("Checking log files...")
        
        try:
            # Check log directory size
            total_size = 0
            for filename in os.listdir(LOG_DIR):
                if filename.endswith('.log'):
                    file_path = os.path.join(LOG_DIR, filename)
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    
                    # Check for large log files
                    if file_size > THRESHOLDS["log_file_size"]:
                        logger.warning(f"Large log file: {filename} ({file_size / 1024 / 1024:.1f} MB)")
                        self._add_alert(f"Large log file: {filename} ({file_size / 1024 / 1024:.1f} MB)", "low")
            
            logger.info(f"Log directory size: {total_size / 1024 / 1024:.1f} MB")
            
            # Check recent logs for errors
            error_count = 0
            for filename in os.listdir(LOG_DIR):
                if filename.endswith('.log'):
                    file_path = os.path.join(LOG_DIR, filename)
                    # Only check recent logs (modified in the last 24 hours)
                    if time.time() - os.path.getmtime(file_path) < 24 * 60 * 60:
                        try:
                            with open(file_path, 'r') as f:
                                for line in f:
                                    if 'ERROR' in line or 'error' in line.lower():
                                        error_count += 1
                                        if self.verbose and error_count <= 5:  # Show only first 5 errors
                                            logger.warning(f"Found error in {filename}: {line.strip()}")
                        except Exception as e:
                            logger.error(f"Error reading log file {filename}: {str(e)}")
            
            if error_count > 0:
                logger.warning(f"Found {error_count} errors in recent log files")
                self._add_alert(f"Found {error_count} errors in recent log files", "medium")
            else:
                logger.info("No errors found in recent log files")
        
        except Exception as e:
            logger.error(f"Error checking log files: {str(e)}")
            self._add_alert(f"Log file check failed: {str(e)}", "low")
    
    def _determine_overall_status(self):
        """Determine overall system status based on component statuses"""
        api_status = self.status["system"]["api_server"]["status"]
        dashboard_status = self.status["system"]["dashboard"]["status"]
        data_pipeline_status = self.status["system"]["data_pipeline"]["status"]
        
        # Define critical components and their weights
        component_weights = {
            "api_server": 0.5,      # API is most critical
            "data_pipeline": 0.3,   # Data pipeline is important
            "dashboard": 0.2        # Dashboard is less critical
        }
        
        # Map status to health score
        status_scores = {
            "running": 1.0,
            "operational": 1.0,
            "degraded": 0.5,
            "stopped": 0.0,
            "failed": 0.0,
            "unknown": 0.3
        }
        
        # Calculate weighted health score
        api_score = status_scores.get(api_status, 0.0) * component_weights["api_server"]
        dashboard_score = status_scores.get(dashboard_status, 0.0) * component_weights["dashboard"]
        data_score = status_scores.get(data_pipeline_status, 0.0) * component_weights["data_pipeline"]
        
        overall_score = api_score + dashboard_score + data_score
        
        # Assign overall status based on score
        if overall_score >= 0.8:
            self.status["system"]["status"] = "healthy"
        elif overall_score >= 0.5:
            self.status["system"]["status"] = "degraded"
        else:
            self.status["system"]["status"] = "critical"
        
        logger.info(f"Overall system status: {self.status['system']['status']} (Score: {overall_score:.2f})")
    
    def _add_alert(self, message, severity):
        """Add an alert to the list"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "severity": severity
        }
        self.alerts.append(alert)
        self.status["alerts"].append(alert)
    
    def _send_alerts(self):
        """Send email alerts if configured"""
        if not self.alerts:
            return
        
        try:
            # Only send if SMTP is configured
            if not SMTP_SERVER or not SMTP_USER:
                logger.warning("SMTP not configured for alerts")
                return
            
            # Create email
            msg = MIMEMultipart()
            msg['From'] = SMTP_USER
            msg['To'] = ", ".join(ALERT_RECIPIENTS)
            
            # Set subject based on highest severity
            highest_severity = max([a["severity"] for a in self.alerts], key=lambda s: {"low": 1, "medium": 2, "high": 3}["low"])
            msg['Subject'] = f"[{highest_severity.upper()}] Strategy Analysis System Alerts"
            
            # Create email body
            body = "Strategy Analysis System Monitoring Alerts\n\n"
            body += f"System Status: {self.status['system']['status'].upper()}\n"
            body += f"Time: {datetime.now().isoformat()}\n\n"
            
            body += "Alerts:\n"
            for alert in self.alerts:
                body += f"- [{alert['severity'].upper()}] {alert['message']}\n"
            
            body += "\n\nFull system status report is attached to this email."
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to server and send
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Sent alert email to {', '.join(ALERT_RECIPIENTS)}")
        
        except Exception as e:
            logger.error(f"Error sending alert email: {str(e)}")
    
    def _save_state(self):
        """Save the current monitoring state to file"""
        try:
            with open(MONITOR_STATE_FILE, 'w') as f:
                json.dump(self.status, f, indent=2)
            logger.info(f"Saved monitoring state to {MONITOR_STATE_FILE}")
        except Exception as e:
            logger.error(f"Error saving monitoring state: {str(e)}")
    
    def _get_pid_from_file(self, pid_file):
        """Get process ID from file"""
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    return int(f.read().strip())
            except Exception as e:
                logger.error(f"Error reading PID file {pid_file}: {str(e)}")
        return None
    
    def _is_process_running(self, pid):
        """Check if a process with the given PID is running"""
        try:
            process = psutil.Process(pid)
            return process.is_running()
        except psutil.NoSuchProcess:
            return False
        except Exception as e:
            logger.error(f"Error checking process {pid}: {str(e)}")
            return False
    
    def display_report(self):
        """Display a formatted system status report"""
        print("\n" + Colors.BOLD + "=" * 60 + Colors.RESET)
        print(Colors.BOLD + f"STRATEGY ANALYSIS SYSTEM STATUS REPORT" + Colors.RESET)
        print(Colors.BOLD + "=" * 60 + Colors.RESET)
        
        # Overall status
        status = self.status["system"]["status"]
        status_color = {
            "healthy": Colors.GREEN,
            "degraded": Colors.YELLOW,
            "critical": Colors.RED,
            "unknown": Colors.BLUE
        }.get(status, Colors.RESET)
        
        print(f"\nTimestamp: {self.status['timestamp']}")
        print(f"Overall System Status: {status_color}{status.upper()}{Colors.RESET}")
        
        # Component statuses
        print("\n" + Colors.BOLD + "Component Status:" + Colors.RESET)
        
        api_status = self.status["system"]["api_server"]["status"]
        api_color = {
            "running": Colors.GREEN,
            "degraded": Colors.YELLOW,
            "stopped": Colors.RED,
            "unknown": Colors.BLUE
        }.get(api_status, Colors.RESET)
        
        dashboard_status = self.status["system"]["dashboard"]["status"]
        dashboard_color = {
            "running": Colors.GREEN,
            "degraded": Colors.YELLOW,
            "stopped": Colors.RED,
            "unknown": Colors.BLUE
        }.get(dashboard_status, Colors.RESET)
        
        data_status = self.status["system"]["data_pipeline"]["status"]
        data_color = {
            "operational": Colors.GREEN,
            "degraded": Colors.YELLOW,
            "failed": Colors.RED,
            "unknown": Colors.BLUE
        }.get(data_status, Colors.RESET)
        
        print(f"  API Server:    {api_color}{api_status.upper()}{Colors.RESET}")
        if self.status["system"]["api_server"]["response_time"] is not None:
            print(f"    Response Time: {self.status['system']['api_server']['response_time']:.2f}s")
        if self.status["system"]["api_server"]["uptime"] is not None:
            uptime_hours = self.status["system"]["api_server"]["uptime"] / 3600
            print(f"    Uptime:        {uptime_hours:.1f} hours")
        
        print(f"  Dashboard:     {dashboard_color}{dashboard_status.upper()}{Colors.RESET}")
        print(f"  Data Pipeline: {data_color}{data_status.upper()}{Colors.RESET}")
        
        if self.status["system"]["data_pipeline"]["data_freshness"] is not None:
            freshness_hours = self.status["system"]["data_pipeline"]["data_freshness"] / 3600
            freshness_color = Colors.GREEN
            if freshness_hours > 24:
                freshness_color = Colors.RED
            elif freshness_hours > 12:
                freshness_color = Colors.YELLOW
            print(f"    Data Age:      {freshness_color}{freshness_hours:.1f} hours{Colors.RESET}")
        
        # Resource usage
        print("\n" + Colors.BOLD + "Resource Usage:" + Colors.RESET)
        
        if self.status["resources"]["cpu"] is not None:
            cpu = self.status["resources"]["cpu"]
            cpu_color = Colors.GREEN
            if cpu > THRESHOLDS["cpu_usage"]:
                cpu_color = Colors.RED
            elif cpu > THRESHOLDS["cpu_usage"] * 0.8:
                cpu_color = Colors.YELLOW
            print(f"  CPU:    {cpu_color}{cpu:.1f}%{Colors.RESET}")
        
        if self.status["resources"]["memory"] is not None:
            memory = self.status["resources"]["memory"]
            memory_color = Colors.GREEN
            if memory > THRESHOLDS["memory_usage"]:
                memory_color = Colors.RED
            elif memory > THRESHOLDS["memory_usage"] * 0.8:
                memory_color = Colors.YELLOW
            print(f"  Memory: {memory_color}{memory:.1f}%{Colors.RESET}")
        
        if self.status["resources"]["disk"] is not None:
            disk = self.status["resources"]["disk"]
            disk_color = Colors.GREEN
            if disk > THRESHOLDS["disk_usage"]:
                disk_color = Colors.RED
            elif disk > THRESHOLDS["disk_usage"] * 0.8:
                disk_color = Colors.YELLOW
            print(f"  Disk:   {disk_color}{disk:.1f}%{Colors.RESET}")
        
        # Data quality
        print("\n" + Colors.BOLD + "Data Quality:" + Colors.RESET)
        
        summary_status = self.status["data_quality"]["summary_report"]["status"]
        summary_color = {
            "valid": Colors.GREEN,
            "empty": Colors.YELLOW,
            "invalid": Colors.RED,
            "missing": Colors.RED,
            "unknown": Colors.BLUE
        }.get(summary_status, Colors.RESET)
        
        weights_status = self.status["data_quality"]["weight_table"]["status"]
        weights_color = {
            "valid": Colors.GREEN,
            "empty": Colors.YELLOW,
            "invalid": Colors.RED,
            "missing": Colors.RED,
            "unknown": Colors.BLUE
        }.get(weights_status, Colors.RESET)
        
        print(f"  Summary Report: {summary_color}{summary_status.upper()}{Colors.RESET}")
        if self.status["data_quality"]["summary_report"]["record_count"] is not None:
            print(f"    Records: {self.status['data_quality']['summary_report']['record_count']}")
        if self.status["data_quality"]["summary_report"]["last_modified"] is not None:
            print(f"    Last Modified: {self.status['data_quality']['summary_report']['last_modified']}")
        
        print(f"  Weight Table:   {weights_color}{weights_status.upper()}{Colors.RESET}")
        if self.status["data_quality"]["weight_table"]["market_types"] is not None:
            print(f"    Market Types: {self.status['data_quality']['weight_table']['market_types']}")
        if self.status["data_quality"]["weight_table"]["last_modified"] is not None:
            print(f"    Last Modified: {self.status['data_quality']['weight_table']['last_modified']}")
        
        # Alerts
        if self.alerts:
            print("\n" + Colors.BOLD + Colors.RED + "Alerts:" + Colors.RESET)
            for alert in self.alerts:
                severity = alert["severity"]
                severity_color = {
                    "high": Colors.RED,
                    "medium": Colors.YELLOW,
                    "low": Colors.CYAN
                }.get(severity, Colors.RESET)
                print(f"  {severity_color}[{severity.upper()}]{Colors.RESET} {alert['message']}")
        else:
            print("\n" + Colors.BOLD + Colors.GREEN + "No alerts detected" + Colors.RESET)
        
        print("\n" + Colors.BOLD + "=" * 60 + Colors.RESET)

def main():
    """Main function to run the monitor"""
    parser = argparse.ArgumentParser(description="Strategy Analysis System Monitor")
    parser.add_argument("--host", default=DEFAULT_API_HOST, help=f"API server host (default: {DEFAULT_API_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_API_PORT, help=f"API server port (default: {DEFAULT_API_PORT})")
    parser.add_argument("--dashboard-port", type=int, default=DEFAULT_DASHBOARD_PORT, help=f"Dashboard port (default: {DEFAULT_DASHBOARD_PORT})")
    parser.add_argument("--alerts", action="store_true", help="Enable email alerts")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    
    monitor = SystemMonitor(
        api_host=args.host,
        api_port=args.port,
        dashboard_port=args.dashboard_port,
        enable_alerts=args.alerts,
        verbose=args.verbose
    )
    
    status = monitor.run_checks()
    
    if args.json:
        print(json.dumps(status, indent=2))
    else:
        monitor.display_report()
    
    # Return exit code based on status
    if status["system"]["status"] == "critical":
        return 2
    elif status["system"]["status"] == "degraded":
        return 1
    else:
        return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nMonitoring interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}", exc_info=True)
        print(f"\n{Colors.RED}Error: {str(e)}{Colors.RESET}")
        sys.exit(3)
