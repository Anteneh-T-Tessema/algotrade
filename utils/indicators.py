import pandas as pd
import numpy as np
import ta

def calculate_indicators(df, strategy_config):
    """
    Calculate technical indicators for the given dataframe
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Dataframe containing OHLCV data
    strategy_config : dict
        Strategy configuration parameters
        
    Returns:
    --------
    pandas.DataFrame
        Dataframe with added indicators
    """
    # Ensure float type for calculations
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['open'] = df['open'].astype(float)
    df['volume'] = df['volume'].astype(float)
    
    # Calculate EMAs
    ema_fast = strategy_config.get('ema_fast', 8)
    ema_slow = strategy_config.get('ema_slow', 21)
    
    df['ema_fast'] = ta.trend.ema_indicator(df['close'], window=ema_fast)
    df['ema_slow'] = ta.trend.ema_indicator(df['close'], window=ema_slow)
    
    # Calculate RSI
    rsi_period = strategy_config.get('rsi_period', 14)
    df['rsi'] = ta.momentum.rsi(df['close'], window=rsi_period)
    
    # Calculate Bollinger Bands
    bollinger_period = strategy_config.get('bollinger_period', 20)
    bollinger_std = strategy_config.get('bollinger_std', 2)
    
    indicator_bb = ta.volatility.BollingerBands(
        df['close'],
        window=bollinger_period,
        window_dev=bollinger_std
    )
    
    df['bb_upper'] = indicator_bb.bollinger_hband()
    df['bb_middle'] = indicator_bb.bollinger_mavg()
    df['bb_lower'] = indicator_bb.bollinger_lband()
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
    
    # Calculate MACD
    macd_indicator = ta.trend.MACD(df['close'])
    df['macd'] = macd_indicator.macd()
    df['macd_signal'] = macd_indicator.macd_signal()
    df['macd_diff'] = macd_indicator.macd_diff()
    
    # Calculate Volume Moving Average
    volume_ma_period = strategy_config.get('volume_ma_period', 20)
    df['volume_ma'] = ta.trend.sma_indicator(df['volume'], window=volume_ma_period)
    df['volume_ratio'] = df['volume'] / df['volume_ma']
    
    # Calculate ATR for volatility
    df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'])
    
    # Calculate price momentum
    df['price_momentum'] = df['close'].pct_change(3)
    
    # Calculate support and resistance
    df['support'] = df['low'].rolling(window=10).min()
    df['resistance'] = df['high'].rolling(window=10).max()
    
    # Calculate price distance from EMA
    df['dist_from_ema_fast'] = (df['close'] - df['ema_fast']) / df['close'] * 100
    df['dist_from_ema_slow'] = (df['close'] - df['ema_slow']) / df['close'] * 100
    
    return df
