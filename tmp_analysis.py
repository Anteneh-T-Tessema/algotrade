#!/usr/bin/env python
# coding: utf-8

# # 1. Import Required Libraries
# 
# Import libraries for data manipulation, file operations, and JSON parsing.

# In[1]:


import pandas as pd
import os
import json
import glob

# Directory containing JSON result files
RESULTS_DIR = os.path.join('data', 'results')


# # 2. Load JSON Result Files
# 
# Load all backtest JSON result files into Python structures.

# In[2]:


results_list = []
for filepath in glob.glob(os.path.join(RESULTS_DIR, '*.json')):
    with open(filepath, 'r') as f:
        data = json.load(f)
        results_list.append(data)

len(results_list)  # Number of files loaded


# # 3. Aggregate Results into a DataFrame
# 
# Combine the loaded JSON results into a pandas DataFrame for analysis.

# In[3]:


records = []
for res in results_list:
    # Each JSON file contains a single strategy-market result
    records.append({
        'strategy': res.get('strategy_name'),
        'market_type': res.get('market_type'),
        'total_return': res.get('total_return'),
        'win_rate': res.get('win_rate'),
        'sharpe_ratio': res.get('sharpe_ratio'),
        'max_drawdown_pct': res.get('max_drawdown_pct', None)
    })

df = pd.DataFrame(records)
df.head()


# # 4. Generate Summary Report
# 
# Create pivot tables for key metrics across strategies and market types.

# In[4]:


metrics = ['total_return', 'win_rate', 'sharpe_ratio', 'max_drawdown_pct']
pivots = {}
for metric in metrics:
    pivots[metric] = df.pivot(index='strategy', columns='market_type', values=metric)
    display(pivots[metric])


# ## 4.b Compute Dynamic Weight Table
# 
# Based on the Sharpe ratio pivot, calculate strategy weights per market by normalizing performance scores, and export to a JSON file for use in the EnsembleStrategy.

# In[5]:


# Normalize Sharpe ratios to get weights per market type
sharpe_df = pivots['sharpe_ratio'].fillna(0)
# Convert negative Sharpe to zero to avoid negative weights
sharpe_df[sharpe_df < 0] = 0
# Normalize columns so weights sum to 1 per market
weight_df = sharpe_df.div(sharpe_df.sum(axis=0), axis=1).fillna(0)

# Convert to nested dict and write to JSON
weights = weight_df.to_dict()
with open('data/weight_table.json', 'w') as f:
    json.dump(weights, f, indent=2)

weights


# ## 4.a Visualization: Heatmaps and Bar Charts
# Use Plotly Express to visualize key metrics across strategies and market types.

# In[6]:


import plotly.express as px


# In[7]:


for metric, pivot in pivots.items():
    fig = px.imshow(
        pivot,
        text_auto=True,
        aspect='auto',
        color_continuous_scale='Viridis',
        labels=dict(x="Market Type", y="Strategy", color=metric.replace('_', ' ').title()),
        x=pivot.columns,
        y=pivot.index,
        title=f"{metric.replace('_', ' ').title()} Heatmap"
    )
    fig.show()


# In[8]:


for metric, pivot in pivots.items():
    df_long = pivot.reset_index().melt(id_vars='strategy', var_name='market_type', value_name=metric)
    fig = px.bar(
        df_long,
        x='strategy',
        y=metric,
        color='market_type',
        barmode='group',
        title=f"{metric.replace('_', ' ').title()} by Strategy and Market",
        labels={"strategy": "Strategy", metric: metric.replace('_', ' ').title(), "market_type": "Market Type"}
    )
    fig.show()


# # 5. Export Summary Report
# 
# Save the aggregated DataFrame and pivot tables to CSV and generate a Markdown version.

# In[9]:


# Ensure summaries directory exists and export CSV
os.makedirs('data', exist_ok=True)
df.to_csv('data/summary_report.csv', index=False)

# Markdown version of total_return pivot
try:
    import tabulate  # ensure dependency
    total_return_md = pivots['total_return'].to_markdown()
    print(total_return_md)
except Exception:
    print("Could not generate markdown table. Displaying raw DataFrame:")
    display(pivots['total_return'])


# # 6. Optional: Integration with Web Dashboard or CI
# 
# - **Web Dashboard**: In `web_dashboard/src/`, create a component to fetch and display the generated `data/summary_report.csv` or embed the interactive Plotly charts.
# - **CI Pipeline**: In your CI (e.g., GitHub Actions), add a step to run this notebook headlessly (using `nbconvert --execute`) and commit `data/summary_report.csv` and any updated visual outputs on each push.
