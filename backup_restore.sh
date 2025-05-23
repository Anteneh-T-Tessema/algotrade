#!/bin/bash
#
# Backup and Recovery Script for Strategy Analysis System
# This script manages system data backups and restoration
#
# Features:
# - Complete and incremental backups
# - Automatic retention management
# - Data verification
# - Restoration capabilities
#

# Strict error handling
set -e

# Configuration
PROJECT_ROOT=$(dirname "$(readlink -f "$0")")
DATA_DIR="${PROJECT_ROOT}/data"
BACKUP_DIR="${PROJECT_ROOT}/backups"
LOG_DIR="${PROJECT_ROOT}/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_RETENTION=30  # Number of days to keep backups
VERIFY_BACKUPS=true  # Whether to verify backups after creation

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Log function
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1"
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" >> "${LOG_DIR}/backup_${TIMESTAMP}.log"
}

# Create a complete backup
create_backup() {
    log "Creating complete system backup..."
    
    # Create backup filename
    BACKUP_FILE="${BACKUP_DIR}/system_backup_${TIMESTAMP}.tar.gz"
    
    # Create a list of directories to back up
    BACKUP_DIRS=(
        "$DATA_DIR"
        "${PROJECT_ROOT}/config"
    )
    
    # Create tar archive
    tar -czf "$BACKUP_FILE" ${BACKUP_DIRS[@]} 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log "Backup created successfully: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"
        
        # Verify backup if enabled
        if [ "$VERIFY_BACKUPS" = true ]; then
            verify_backup "$BACKUP_FILE"
        fi
    else
        log "ERROR: Backup creation failed!"
        return 1
    fi
    
    return 0
}

# Verify backup integrity
verify_backup() {
    local backup_file="$1"
    log "Verifying backup integrity: $(basename "$backup_file")"
    
    # Test tar archive integrity
    if tar -tzf "$backup_file" >/dev/null 2>&1; then
        log "Backup verification successful"
        return 0
    else
        log "ERROR: Backup verification failed! The archive may be corrupted."
        return 1
    fi
}

# Restore from backup
restore_backup() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        # If no backup specified, use the most recent one
        backup_file=$(ls -t "${BACKUP_DIR}/system_backup_"*.tar.gz 2>/dev/null | head -1)
        
        if [ -z "$backup_file" ]; then
            log "ERROR: No backup files found!"
            return 1
        fi
    elif [ ! -f "$backup_file" ]; then
        log "ERROR: Specified backup file doesn't exist: $backup_file"
        return 1
    fi
    
    log "Restoring from backup: $(basename "$backup_file")"
    
    # Verify backup before restoring
    verify_backup "$backup_file"
    if [ $? -ne 0 ]; then
        log "ERROR: Cannot restore from corrupted backup!"
        return 1
    fi
    
    # Stop running services
    if [ -f "${PROJECT_ROOT}/production_deploy.sh" ]; then
        log "Stopping services before restore..."
        "${PROJECT_ROOT}/production_deploy.sh" stop >/dev/null 2>&1 || true
    fi
    
    # Create a temporary directory for extraction
    local temp_dir="${BACKUP_DIR}/temp_restore_${TIMESTAMP}"
    mkdir -p "$temp_dir"
    
    # Extract backup
    log "Extracting backup..."
    tar -xzf "$backup_file" -C "$temp_dir"
    
    # Restore data files
    log "Restoring data files..."
    if [ -d "${temp_dir}${DATA_DIR}" ]; then
        rsync -a "${temp_dir}${DATA_DIR}/" "${DATA_DIR}/"
        log "Data files restored"
    else
        log "WARNING: No data files found in backup"
    fi
    
    # Restore config files
    if [ -d "${temp_dir}${PROJECT_ROOT}/config" ]; then
        rsync -a "${temp_dir}${PROJECT_ROOT}/config/" "${PROJECT_ROOT}/config/"
        log "Configuration files restored"
    else
        log "WARNING: No configuration files found in backup"
    fi
    
    # Clean up
    rm -rf "$temp_dir"
    
    log "Restore completed successfully"
    log "You can now restart the system with: ./production_deploy.sh start"
    
    return 0
}

# Clean up old backups
cleanup_old_backups() {
    log "Cleaning up backups older than $BACKUP_RETENTION days..."
    
    find "$BACKUP_DIR" -type f -name "system_backup_*.tar.gz" -mtime +$BACKUP_RETENTION | while read -r old_backup; do
        log "Removing old backup: $(basename "$old_backup")"
        rm -f "$old_backup"
    done
    
    return 0
}

# List available backups
list_backups() {
    log "Available backups:"
    local count=0
    
    # Get sorted list (newest first)
    local backups=$(ls -t "${BACKUP_DIR}/system_backup_"*.tar.gz 2>/dev/null)
    
    if [ -z "$backups" ]; then
        log "No backups found."
        return 0
    fi
    
    printf "%-4s %-20s %-15s %-30s\n" "No." "Date" "Size" "Filename"
    printf "%-4s %-20s %-15s %-30s\n" "----" "--------------------" "---------------" "------------------------------"
    
    echo "$backups" | while read -r backup; do
        count=$((count + 1))
        local date_str=$(echo "$(basename "$backup")" | grep -o '[0-9]\{8\}_[0-9]\{6\}' | sed 's/\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)_\([0-9]\{2\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)/\1-\2-\3 \4:\5:\6/')
        local size=$(du -h "$backup" | cut -f1)
        printf "%-4s %-20s %-15s %-30s\n" "$count" "$date_str" "$size" "$(basename "$backup")"
    done
    
    return 0
}

# Show usage help
show_help() {
    echo "Usage: $0 [command] [options]"
    echo
    echo "Commands:"
    echo "  backup           Create a complete system backup"
    echo "  restore [file]   Restore from a backup (most recent or specified file)"
    echo "  verify [file]    Verify a backup file's integrity"
    echo "  list             List available backups"
    echo "  cleanup          Remove backups older than retention period"
    echo "  help             Show this help message"
    echo
    echo "Examples:"
    echo "  $0 backup        # Create a new backup"
    echo "  $0 restore       # Restore from the most recent backup"
    echo "  $0 list          # List all available backups"
    echo
}

# Main execution
mkdir -p "$LOG_DIR"

case "$1" in
    backup)
        create_backup
        cleanup_old_backups
        ;;
    restore)
        restore_backup "$2"
        ;;
    verify)
        if [ -z "$2" ]; then
            echo "ERROR: Please specify a backup file to verify"
            exit 1
        fi
        verify_backup "$2"
        ;;
    list)
        list_backups
        ;;
    cleanup)
        cleanup_old_backups
        ;;
    help|*)
        show_help
        ;;
esac

exit 0
