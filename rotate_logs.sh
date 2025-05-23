#!/bin/bash
#
# Log Rotation Script for Strategy Analysis System
# This script rotates and compresses old log files to manage disk space
#
# Features:
# - Rotates all types of log files
# - Configurable retention period
# - Compression of rotated logs
# - Low-overhead execution
#

# Strict error handling
set -e

# Configuration
PROJECT_ROOT=$(dirname "$(readlink -f "$0")")
LOG_DIR="${PROJECT_ROOT}/logs"
ARCHIVE_DIR="${LOG_DIR}/archive"
MAX_AGE_DAYS=30       # Maximum age of logs to keep
COMPRESS=true         # Whether to compress rotated logs
ROTATION_MODE="size"  # Options: "size" or "date"
SIZE_THRESHOLD="10M"  # Rotate files larger than this

# Create archive directory if it doesn't exist
mkdir -p "$ARCHIVE_DIR"

# Timestamp for log rotation
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Log function
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1"
}

# Rotate logs by size
rotate_by_size() {
    log "Rotating logs based on size..."
    
    find "$LOG_DIR" -maxdepth 1 -type f -name "*.log" | while read -r log_file; do
        file_size=$(du -k "$log_file" | cut -f1)
        size_threshold_kb=$(echo "$SIZE_THRESHOLD" | sed 's/M/*1024/g' | bc)
        
        if [ "$file_size" -gt "$size_threshold_kb" ]; then
            base_name=$(basename "$log_file")
            archive_name="${base_name%.log}_${TIMESTAMP}.log"
            
            log "Rotating $base_name (${file_size}KB > ${size_threshold_kb}KB)"
            
            # Copy to archive and truncate original
            cp "$log_file" "${ARCHIVE_DIR}/${archive_name}"
            truncate -s 0 "$log_file"
            
            # Compress if enabled
            if [ "$COMPRESS" = true ]; then
                gzip "${ARCHIVE_DIR}/${archive_name}"
                log "Compressed ${archive_name}"
            fi
        fi
    done
}

# Rotate logs by date
rotate_by_date() {
    log "Rotating logs based on date pattern..."
    
    # Group by log type (api_server, data_pipeline, etc.)
    log_types=$(find "$LOG_DIR" -maxdepth 1 -type f -name "*.log" | sed 's/.*\/\([^_]*\)_.*/\1/g' | sort | uniq)
    
    for log_type in $log_types; do
        # Find logs of this type
        find "$LOG_DIR" -maxdepth 1 -type f -name "${log_type}_*.log" | while read -r log_file; do
            base_name=$(basename "$log_file")
            
            # Move to archive
            log "Archiving $base_name"
            mv "$log_file" "${ARCHIVE_DIR}/${base_name}"
            
            # Compress if enabled
            if [ "$COMPRESS" = true ]; then
                gzip "${ARCHIVE_DIR}/${base_name}"
                log "Compressed ${base_name}"
            fi
        done
    done
}

# Delete old logs
cleanup_old_logs() {
    log "Cleaning up logs older than $MAX_AGE_DAYS days..."
    
    find "$ARCHIVE_DIR" -type f -mtime +$MAX_AGE_DAYS | while read -r old_log; do
        log "Removing old log: $(basename "$old_log")"
        rm -f "$old_log"
    done
}

# Main execution
log "Starting log rotation..."

case "$ROTATION_MODE" in
    size)
        rotate_by_size
        ;;
    date)
        rotate_by_date
        ;;
    *)
        log "Error: Unknown rotation mode '$ROTATION_MODE'"
        exit 1
        ;;
esac

# Clean up old logs
cleanup_old_logs

log "Log rotation completed successfully"
exit 0
