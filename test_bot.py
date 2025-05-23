#!/usr/bin/env python3
"""
Test script to verify that our trading bot components work correctly.
This script checks for common errors and validates that all modules can be imported.
"""

import os
import sys
import importlib
import logging
from datetime import datetime

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("bot_tester")

def check_imports():
    """Check if all required modules can be imported."""
    logger.info("Testing module imports...")
    
    required_modules = [
        "pandas", "numpy", "matplotlib", "binance.client", "dotenv", 
        "yaml", "schedule", "ta"
    ]
    
    success = True
    for module_name in required_modules:
        try:
            importlib.import_module(module_name)
            logger.info(f"✅ Successfully imported {module_name}")
        except ImportError as e:
            logger.error(f"❌ Failed to import {module_name}: {str(e)}")
            success = False
    
    return success

def check_project_structure():
    """Check if all required project files and directories exist."""
    logger.info("Checking project structure...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    required_files = [
        "bot.py", "backtest.py", "README.md", "requirements.txt",
        os.path.join("config", "config.yaml"),
        os.path.join("strategies", "scalping_strategy.py"),
        os.path.join("utils", "indicators.py"),
        os.path.join("utils", "logger.py"),
        os.path.join("utils", "risk_management.py"),
        os.path.join("utils", "telegram_notifications.py")
    ]
    
    required_dirs = [
        "config", "data", "logs", "strategies", "utils"
    ]
    
    # Check directories
    for directory in required_dirs:
        dir_path = os.path.join(base_dir, directory)
        if not os.path.isdir(dir_path):
            logger.error(f"❌ Missing directory: {directory}")
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"✅ Created directory: {directory}")
        else:
            logger.info(f"✅ Directory exists: {directory}")
    
    # Check files
    success = True
    for file_path in required_files:
        full_path = os.path.join(base_dir, file_path)
        if not os.path.isfile(full_path):
            logger.error(f"❌ Missing file: {file_path}")
            success = False
        else:
            logger.info(f"✅ File exists: {file_path}")
    
    return success

def check_env_file():
    """Check if the .env file has all required variables."""
    logger.info("Checking .env file...")
    
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", ".env")
    
    if not os.path.isfile(env_path):
        logger.error("❌ .env file doesn't exist")
        return False
    
    required_vars = ["API_KEY", "API_SECRET", "TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID"]
    
    # Read .env file
    with open(env_path, 'r') as f:
        env_content = f.read()
    
    success = True
    for var in required_vars:
        if var not in env_content:
            logger.error(f"❌ Missing environment variable: {var}")
            success = False
        else:
            logger.info(f"✅ Environment variable found: {var}")
    
    return success

def check_config_file():
    """Check if the config.yaml file has all required sections."""
    logger.info("Checking config.yaml file...")
    
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "config.yaml")
    
    if not os.path.isfile(config_path):
        logger.error("❌ config.yaml file doesn't exist")
        return False
    
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        required_sections = ["trading_pairs", "risk_management", "strategy", "exchange", "general"]
        
        success = True
        for section in required_sections:
            if section not in config:
                logger.error(f"❌ Missing config section: {section}")
                success = False
            else:
                logger.info(f"✅ Config section found: {section}")
                
        # Check for specific required keys
        if "exchange" in config and "testnet" not in config["exchange"]:
            logger.error("❌ Missing 'testnet' setting in exchange section")
            success = False
            
        if "strategy" in config and "timeframe" not in config["strategy"]:
            logger.error("❌ Missing 'timeframe' setting in strategy section")
            success = False
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Error parsing config.yaml: {str(e)}")
        return False

def test_bot_imports():
    """Test importing the TradingBot class."""
    logger.info("Testing bot imports...")
    
    try:
        from bot import TradingBot
        logger.info("✅ Successfully imported TradingBot class")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to import TradingBot: {str(e)}")
        return False

def test_backtest_imports():
    """Test importing the backtest functions."""
    logger.info("Testing backtest imports...")
    
    try:
        from backtest import backtest_strategy, plot_backtest_results
        logger.info("✅ Successfully imported backtest functions")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to import backtest functions: {str(e)}")
        return False

def run_all_tests():
    """Run all tests."""
    logger.info("=== Starting trading bot validation ===")
    
    tests = [
        ("Import Check", check_imports),
        ("Project Structure Check", check_project_structure),
        ("Environment File Check", check_env_file),
        ("Config File Check", check_config_file),
        ("Bot Import Test", test_bot_imports),
        ("Backtest Import Test", test_backtest_imports)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n=== Running: {test_name} ===")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"Test '{test_name}' raised an exception: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    logger.info("\n=== Test Results Summary ===")
    all_passed = True
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        logger.info(f"{test_name}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        logger.info("\n✅ All tests passed! Your trading bot should work correctly.")
    else:
        logger.info("\n❌ Some tests failed. Please fix the issues before running the bot.")

if __name__ == "__main__":
    run_all_tests()
