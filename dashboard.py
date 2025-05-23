#!/usr/bin/env python3
"""
Trading Performance Dashboard

This script creates an interactive dashboard for monitoring the performance
of the trading bot using Streamlit.

Usage:
    streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
import json
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Define constants
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

def load_trade_history():
    """Load the most recent trade history file"""
    trade_files = [f for f in os.listdir(DATA_DIR) if f.startswith('trade_history_') and f.endswith('.csv')]
    
    if not trade_files:
        return pd.DataFrame(columns=['symbol', 'entry_price', 'exit_price', 'quantity', 
                                    'entry_time', 'exit_time', 'profit', 'profit_percentage',
                                    'status', 'exit_reason'])
    
    # Get the most recent file based on timestamp in filename
    latest_file = sorted(trade_files)[-1]
    
    # Load the CSV into a DataFrame
    df = pd.read_csv(os.path.join(DATA_DIR, latest_file))
    
    # Convert time columns to datetime
    if 'entry_time' in df.columns:
        df['entry_time'] = pd.to_datetime(df['entry_time'])
    if 'exit_time' in df.columns:
        df['exit_time'] = pd.to_datetime(df['exit_time'])
        
    return df

def load_backtest_results():
    """Load backtest results from the results directory"""
    results_dir = os.path.join(DATA_DIR, 'results')
    if not os.path.exists(results_dir):
        return []
        
    result_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
    
    results = []
    for file in result_files:
        try:
            with open(os.path.join(results_dir, file), 'r') as f:
                result = json.load(f)
                results.append(result)
        except FileNotFoundError as e:
            st.error(f"File not found {file}: {str(e)}")
        except PermissionError as e:
            st.error(f"Permission denied for {file}: {str(e)}")
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON format in {file}: {str(e)}")
        except IOError as e:
            st.error(f"I/O error reading {file}: {str(e)}")
        except Exception as e:
            st.error(f"Unexpected error loading {file}: {str(e)}")
            
    return results

def dashboard_overview(trade_history):
    """Display the dashboard overview section"""
    st.subheader("Trading Bot Performance Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate metrics
    total_trades = len(trade_history)
    closed_trades = trade_history[trade_history['status'] == 'CLOSED'].shape[0]
    open_trades = trade_history[trade_history['status'] == 'OPEN'].shape[0]
    
    # Calculate profit metrics for closed trades
    if closed_trades > 0:
        closed_df = trade_history[trade_history['status'] == 'CLOSED']
        total_profit = closed_df['profit'].sum()
        win_rate = (closed_df['profit'] > 0).mean() * 100
        avg_profit_pct = closed_df['profit_percentage'].mean()
    else:
        total_profit = 0
        win_rate = 0
        avg_profit_pct = 0
    
    # Display metrics
    col1.metric("Total Trades", total_trades)
    col2.metric("Open Positions", open_trades)
    col3.metric("Total Profit", f"${total_profit:.2f}")
    col4.metric("Win Rate", f"{win_rate:.1f}%")
    
    # Additional metrics
    if closed_trades > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate advanced metrics
        winning_trades = closed_df[closed_df['profit'] > 0]
        losing_trades = closed_df[closed_df['profit'] <= 0]
        
        avg_win = winning_trades['profit'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['profit'].mean() if len(losing_trades) > 0 else 0
        
        profit_factor = abs(winning_trades['profit'].sum() / losing_trades['profit'].sum()) if len(losing_trades) > 0 and losing_trades['profit'].sum() != 0 else float('inf')
        
        col1.metric("Avg Profit %", f"{avg_profit_pct:.2f}%")
        col2.metric("Avg Win", f"${avg_win:.2f}")
        col3.metric("Avg Loss", f"${avg_loss:.2f}")
        col4.metric("Profit Factor", f"{profit_factor:.2f}")

def plot_equity_curve(trade_history):
    """Plot the equity curve based on trade history"""
    st.subheader("Equity Curve")
    
    if len(trade_history) == 0:
        st.info("No trade history available.")
        return
    
    # Filter closed trades
    closed_trades = trade_history[trade_history['status'] == 'CLOSED'].copy()
    
    if len(closed_trades) == 0:
        st.info("No closed trades available to plot equity curve.")
        return
    
    # Sort by exit time
    closed_trades = closed_trades.sort_values('exit_time')
    
    # Calculate cumulative profit
    initial_capital = 10000  # Default initial capital
    closed_trades['cumulative_profit'] = closed_trades['profit'].cumsum()
    closed_trades['equity'] = initial_capital + closed_trades['cumulative_profit']
    
    # Calculate drawdown
    closed_trades['peak'] = closed_trades['equity'].cummax()
    closed_trades['drawdown'] = (closed_trades['equity'] - closed_trades['peak']) / closed_trades['peak'] * 100
    
    # Create plots using Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=closed_trades['exit_time'], 
        y=closed_trades['equity'],
        mode='lines',
        name='Equity'
    ))
    
    fig.update_layout(
        title='Equity Curve',
        xaxis_title='Date',
        yaxis_title='Equity ($)',
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Drawdown plot
    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(
        x=closed_trades['exit_time'], 
        y=closed_trades['drawdown'],
        mode='lines',
        name='Drawdown',
        fill='tozeroy',
        line=dict(color='red')
    ))
    
    fig_dd.update_layout(
        title='Drawdown (%)',
        xaxis_title='Date',
        yaxis_title='Drawdown (%)',
        height=250,
        template='plotly_white'
    )
    
    st.plotly_chart(fig_dd, use_container_width=True)

def plot_trade_distribution(trade_history):
    """Plot trade distribution by symbol and outcome"""
    st.subheader("Trade Analysis")
    
    if len(trade_history) == 0:
        st.info("No trade history available.")
        return
    
    # Only look at closed trades
    closed_trades = trade_history[trade_history['status'] == 'CLOSED']
    
    if len(closed_trades) == 0:
        st.info("No closed trades available for analysis.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Trades by symbol
        symbol_counts = closed_trades['symbol'].value_counts()
        
        fig = px.pie(
            values=symbol_counts.values,
            names=symbol_counts.index,
            title='Trades by Symbol'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Win/loss distribution
        closed_trades['outcome'] = closed_trades['profit'].apply(lambda x: 'Win' if x > 0 else 'Loss')
        outcome_counts = closed_trades['outcome'].value_counts()
        
        fig = px.pie(
            values=outcome_counts.values,
            names=outcome_counts.index,
            title='Win/Loss Distribution',
            color_discrete_map={'Win': 'green', 'Loss': 'red'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Trade profit distribution
    st.subheader("Profit Distribution")
    
    fig = px.histogram(
        closed_trades,
        x='profit_percentage',
        nbins=20,
        title='Profit Distribution (%)',
        color='outcome',
        color_discrete_map={'Win': 'green', 'Loss': 'red'}
    )
    
    fig.update_layout(
        xaxis_title='Profit (%)',
        yaxis_title='Number of Trades',
        bargap=0.1
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_trade_table(trade_history):
    """Display the trade history table"""
    st.subheader("Trade History")
    
    if len(trade_history) == 0:
        st.info("No trade history available.")
        return
    
    # Create a copy to avoid modifying the original
    trades_display = trade_history.copy()
    
    # Format columns for display
    if 'entry_time' in trades_display.columns:
        trades_display['entry_time'] = trades_display['entry_time'].dt.strftime('%Y-%m-%d %H:%M')
    if 'exit_time' in trades_display.columns:
        trades_display['exit_time'] = trades_display['exit_time'].dt.strftime('%Y-%m-%d %H:%M')
    
    # Add profit_color for styling
    trades_display['profit_color'] = trades_display['profit'].apply(
        lambda x: 'color: green' if x > 0 else ('color: red' if x < 0 else '')
    )
    
    # Columns to display
    columns_to_display = ['symbol', 'entry_time', 'exit_time', 'entry_price', 'exit_price', 
                         'quantity', 'profit', 'profit_percentage', 'status', 'exit_reason']
    
    # Filter columns that exist in the dataframe
    available_columns = [col for col in columns_to_display if col in trades_display.columns]
    
    # Display the table with styled profit column
    st.dataframe(trades_display[available_columns].style.apply(
        lambda _: trades_display['profit_color'], 
        subset=['profit']
    ))

def compare_backtest_results(results):
    """Compare results from different backtest runs"""
    st.subheader("Backtest Results Comparison")
    
    if not results:
        st.info("No backtest results available.")
        return
    
    # Extract key metrics from each backtest result
    metrics = []
    for result in results:
        strategy_name = result.get('strategy', 'Unknown')
        metrics.append({
            'Strategy': strategy_name,
            'Total Return (%)': result.get('total_return', 0),
            'Sharpe Ratio': result.get('sharpe_ratio', 0),
            'Max Drawdown (%)': result.get('max_drawdown_pct', 0),
            'Win Rate (%)': result.get('win_rate', 0) * 100,
            'Profit Factor': result.get('profit_factor', 0),
            'Total Trades': result.get('total_trades', 0)
        })
    
    # Convert to DataFrame
    metrics_df = pd.DataFrame(metrics)
    
    # Display comparison table
    st.dataframe(metrics_df)
    
    # Comparative bar chart
    st.subheader("Strategy Return Comparison")
    
    fig = px.bar(
        metrics_df,
        x='Strategy',
        y='Total Return (%)',
        color='Strategy',
        title='Total Return by Strategy'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Risk-adjusted return comparison
    st.subheader("Risk-Adjusted Return Comparison")
    
    fig = px.scatter(
        metrics_df,
        x='Max Drawdown (%)',
        y='Total Return (%)',
        size='Sharpe Ratio',
        color='Strategy',
        hover_name='Strategy',
        size_max=30,
        title='Risk vs. Return by Strategy'
    )
    
    fig.update_layout(
        xaxis_title='Risk (Max Drawdown %)',
        yaxis_title='Return (%)'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def strategy_comparison_view(backtest_results):
    """
    Interactive view for comparing different trading strategies
    
    Parameters:
    -----------
    backtest_results : list
        List of backtest result dictionaries
    """
    st.subheader("Strategy Comparison")
    
    if not backtest_results:
        st.info("No backtest results available. Please run backtest first.")
        return
        
    # Extract strategy names and market types
    strategies = sorted(list(set([result['strategy_name'] for result in backtest_results])))
    market_types = sorted(list(set([result['market_type'] for result in backtest_results])))
    
    # Filters
    col1, col2 = st.columns(2)
    selected_strategies = col1.multiselect("Select Strategies", strategies, default=strategies[:3] if len(strategies) > 3 else strategies)
    selected_markets = col2.multiselect("Select Market Types", market_types, default=['normal', 'trending'] if 'normal' in market_types and 'trending' in market_types else market_types[:2] if len(market_types) > 1 else market_types)
    
    # Filter results
    filtered_results = [r for r in backtest_results 
                       if r['strategy_name'] in selected_strategies 
                       and r['market_type'] in selected_markets]
    
    if not filtered_results:
        st.warning("No results match the selected filters.")
        return
    
    # Select comparison metrics
    metrics = ['total_return', 'win_rate', 'sharpe_ratio', 'max_drawdown_pct', 'profit_factor']
    metric_names = {
        'total_return': 'Total Return (%)',
        'win_rate': 'Win Rate (%)',
        'sharpe_ratio': 'Sharpe Ratio',
        'max_drawdown_pct': 'Maximum Drawdown (%)',
        'profit_factor': 'Profit Factor'
    }
    
    selected_metric = st.selectbox("Select Metric for Comparison", 
                                 list(metric_names.keys()),
                                 format_func=lambda x: metric_names[x],
                                 index=0)
    
    # Create dataframe for visualization
    data = []
    for result in filtered_results:
        # Format metric value
        if selected_metric == 'win_rate':
            metric_value = result.get(selected_metric, 0) * 100  # Convert to percentage
        elif selected_metric == 'total_return':
            metric_value = result.get(selected_metric, 0)  # Already in percentage
        else:
            metric_value = result.get(selected_metric, 0)
            
        data.append({
            'Strategy': result['strategy_name'],
            'Market Type': result['market_type'],
            'Metric': metric_value
        })
    
    df = pd.DataFrame(data)
    
    # Create visualization based on the data
    if not df.empty:
        # Plot heatmap
        df_pivot = df.pivot(index='Strategy', columns='Market Type', values='Metric')
        
        fig = px.imshow(df_pivot, 
                       labels=dict(x="Market Type", y="Strategy", color=metric_names[selected_metric]),
                       text_auto=True,
                       aspect="auto",
                       color_continuous_scale=px.colors.diverging.RdYlGn)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Bar chart comparison
        st.subheader(f"{metric_names[selected_metric]} by Strategy and Market Type")
        fig = px.bar(df, 
                   x='Strategy', 
                   y='Metric', 
                   color='Market Type', 
                   barmode='group',
                   labels={'Metric': metric_names[selected_metric]})
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display raw data
        with st.expander("Show Raw Data"):
            st.dataframe(df_pivot)
    
def performance_by_market_type(backtest_results):
    """
    Show how different strategies perform in each market type
    
    Parameters:
    -----------
    backtest_results : list
        List of backtest result dictionaries
    """
    st.subheader("Performance by Market Type")
    
    if not backtest_results:
        st.info("No backtest results available. Please run backtest first.")
        return
        
    # Extract market types
    market_types = sorted(list(set([result['market_type'] for result in backtest_results])))
    
    # Select market type
    selected_market = st.selectbox("Select Market Type", market_types, 
                                  index=market_types.index('trending') if 'trending' in market_types else 0)
    
    # Filter results for selected market
    market_results = [r for r in backtest_results if r['market_type'] == selected_market]
    
    if not market_results:
        st.warning(f"No results available for {selected_market} market.")
        return
    
    # Sort by total return
    market_results.sort(key=lambda x: x.get('total_return', 0), reverse=True)
    
    # Create dataframe with performance metrics
    data = []
    for result in market_results:
        data.append({
            'Strategy': result['strategy_name'],
            'Total Return (%)': result.get('total_return', 0),
            'Win Rate (%)': result.get('win_rate', 0) * 100,
            'Sharpe Ratio': result.get('sharpe_ratio', 0),
            'Max Drawdown (%)': result.get('max_drawdown_pct', 0),
            'Profit Factor': result.get('profit_factor', 0)
        })
    
    df = pd.DataFrame(data)
    
    # Plot bar chart for total return
    fig = px.bar(df, 
               x='Strategy', 
               y='Total Return (%)',
               color='Total Return (%)',
               color_continuous_scale=px.colors.diverging.RdYlGn)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show detailed metrics
    st.dataframe(df.set_index('Strategy'), use_container_width=True)

def main():
    """Main dashboard function"""
    st.set_page_config(
        page_title="Trading Performance Dashboard",
        page_icon="📈",
        layout="wide",
    )
    
    st.title("Algorithmic Trading Bot - Performance Dashboard")
    
    # Load data
    trade_history = load_trade_history()
    backtest_results = load_backtest_results()
    
    # Sidebar filters
    st.sidebar.title("Filters")
    
    # Date range filter
    if len(trade_history) > 0 and 'entry_time' in trade_history.columns:
        min_date = trade_history['entry_time'].min().date()
        max_date = datetime.now().date()
        
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            # Filter by entry time
            mask = (trade_history['entry_time'].dt.date >= start_date) & \
                   (trade_history['entry_time'].dt.date <= end_date)
            trade_history = trade_history[mask]
    
    # Symbol filter
    if len(trade_history) > 0 and 'symbol' in trade_history.columns:
        symbols = ['All'] + sorted(trade_history['symbol'].unique().tolist())
        selected_symbol = st.sidebar.selectbox("Symbol", symbols)
        
        if selected_symbol != 'All':
            trade_history = trade_history[trade_history['symbol'] == selected_symbol]
    
    # Show only profitable trades
    if st.sidebar.checkbox("Show only profitable trades"):
        trade_history = trade_history[trade_history['profit'] > 0]
    
    # Main dashboard sections
    try:
        dashboard_overview(trade_history)
        plot_equity_curve(trade_history)
        plot_trade_distribution(trade_history)
        display_trade_table(trade_history)
        
        # Show backtest comparison if results are available
        if backtest_results:
            compare_backtest_results(backtest_results)
            strategy_comparison_view(backtest_results)
            performance_by_market_type(backtest_results)
    except Exception as e:
        st.error(f"Error rendering dashboard: {str(e)}")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.info(
        "This dashboard provides real-time insights into the performance of "
        "the algorithmic trading bot. Data is sourced from actual trades "
        "and backtest results."
    )

if __name__ == "__main__":
    main()
