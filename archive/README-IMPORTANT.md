# Transport Network Analysis

This application analyzes transport networks using GTFS data. If you're experiencing long load times, please follow these troubleshooting steps.

## Dependencies

First, ensure all the required Python packages are installed:

```bash
pip3 install -r requirements.txt
```

If the requirements.txt file doesn't exist, install these key dependencies:

```bash
pip3 install pandas networkx matplotlib dash dash-bootstrap-components plotly python-louvain python-dotenv requests
```

## Troubleshooting Long Load Times

The application may take a long time to start because it's processing large GTFS datasets and performing computationally intensive graph analysis operations.

### Solution 1: Use the Fixed Dashboard

We've created a fixed version of the dashboard with better loading indicators:

```bash
python3 fixed_dashboard.py
```

This version:
- Shows a loading progress bar
- Lets you adjust the sample size (smaller = faster load)
- Only loads data when you click the "Load Data" button
- Displays detailed loading logs so you can see what's happening

### Solution 2: Run the Performance Check

To identify which specific parts of the analysis are causing slowdowns:

```bash
python3 check_performance.py
```

This script will measure the time taken by each component and help identify bottlenecks.

### Solution 3: Reduce Sample Size

The original dashboard is trying to load a large sample size (1000 trips). You can edit `dashboard.py` to reduce this:

1. Open `dashboard.py`
2. Find the line: `load_data(sample_size=1000)`
3. Change it to a smaller value: `load_data(sample_size=200)`

### Solution 4: Run the Analysis Script

For faster testing, run the analysis script directly instead of the dashboard:

```bash
python3 analyze_critical_nodes.py
```

This script only performs critical nodes analysis without the full dashboard visualization.

## Data Structure

- The GTFS data is stored in `data/tfgm_gtfs/`
- The visualizations are saved to `visualizations/`
- Analysis results are saved to `results/`

## Typical Bottlenecks

1. **GTFS Data Loading**: Initial loading of large transit data files
2. **Graph Building**: Converting transit data into a network graph
3. **Betweenness Centrality**: Calculating critical nodes (CPU-intensive)
4. **Community Detection**: Identifying communities using Louvain method
5. **Visualization**: Creating and saving large network visualizations

If you're still experiencing issues, try using a machine with more RAM and CPU cores, as some of these operations are highly resource-intensive.