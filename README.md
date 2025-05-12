# Transport Network Analysis

A comprehensive framework for analyzing public transportation networks using graph theory, community detection, and symbolic AI.

## Overview

This project provides tools to analyze GTFS (General Transit Feed Specification) data for transport networks. It constructs graph representations of transport systems, identifies critical nodes and communities, analyzes service equity, and provides insights through advanced visualization and symbolic reasoning.

The framework is specifically optimized for large-scale transport networks with thousands of nodes, utilizing parallel processing and memory-efficient algorithms.

## Features

- **Graph Construction**: Build transport network graphs from GTFS data
- **Community Detection**: Identify and analyze transport communities using Louvain method
- **Critical Node Analysis**: Detect key transfer points and vulnerabilities
- **Temporal Analysis**: Study network changes across hours and days
- **Symbolic AI Integration**: Convert network properties to knowledge bases for reasoning
- **Equity Analysis**: Evaluate service distribution and accessibility
- **Transport Efficiency**: Measure network efficiency and connection quality
- **Advanced Visualization**: Generate static and interactive network visualizations

## Requirements

- Python 3.9+
- NetworkX
- Pandas
- Matplotlib
- Plotly
- Numpy
- python-dotenv

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/username/transport-network-analysis.git
   cd transport-network-analysis
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Project Structure

```
transport-network-analysis/
├── dashboard_components/        # Dashboard visualization components
├── data/                        # GTFS data storage
├── docs/                        # Static HTML for GitHub Pages deployment
├── notebooks/                   # Jupyter notebooks for exploration
├── results/                     # Analysis results storage
├── scripts/                     # Analysis scripts
│   └── run_analysis.py          # Main analysis script
├── src/                         # Source code
│   ├── data_processing/         # GTFS data loading and processing
│   ├── domain_analysis/         # Domain-specific analysis modules
│   ├── graph_analysis/          # Graph algorithms and analysis
│   ├── symbolic_ai/             # Symbolic reasoning modules
│   ├── utils/                   # Utility functions
│   └── visualizations/          # Visualization tools
├── visualizations/              # Generated visualizations
├── .env                         # Environment variables
├── enhanced_dashboard.py        # Interactive dashboard
├── export_dashboard_to_html.py  # HTML exporter for GitHub Pages
└── requirements.txt             # Dependencies
```

## Usage

### Basic Analysis

Run the complete analysis pipeline:

```bash
python scripts/run_analysis.py
```

### Performance-Optimized Analysis

For faster processing with reduced sample size:

```bash
python scripts/run_analysis.py --sample-size=500
```

### Interactive Dashboard

Launch the enhanced dashboard for interactive visualization:

```bash
python enhanced_dashboard.py
```

The dashboard will be available at http://127.0.0.1:9090 in your web browser.

### Static HTML Export

To create a static HTML version for deployment to GitHub Pages:

```bash
python export_dashboard_to_html.py
```

This creates the necessary files in the `docs/` directory suitable for GitHub Pages deployment.

### Customizing Analysis

The script supports various options:

```bash
python scripts/run_analysis.py --help
```

Key parameters:
- `--data-dir`: Directory containing GTFS data
- `--gtfs-url`: URL to download GTFS data
- `--output-dir`: Directory to save results
- `--sample-size`: Number of trips to sample (default: 500)
- `--parallel`: Enable parallel processing (default: True)
- `--num-workers`: Number of parallel workers
- `--cache`: Use cached results when available (default: True)
- `--skip-steps`: Comma-separated steps to skip (e.g., "temporal,symbolic")
- `--visualize`: Generate visualizations
- `--optimize`: Optimize graph for memory usage
- `--enhance-geocoding`: Enhance node coordinates using geocoding

## Analysis Steps

1. **Loading GTFS Data**: Loads and processes GTFS feeds
2. **Building Graph**: Constructs a network graph from transport data
3. **Community Detection**: Identifies communities within the network
4. **Critical Node Analysis**: Identifies important transfer points
5. **Vulnerability Assessment**: Analyzes network vulnerability
6. **Symbolic AI Analysis**: Creates knowledge base for advanced reasoning
7. **Temporal Analysis**: Studies network patterns across time
8. **Domain Analysis**: Analyzes transport efficiency and equity
9. **Visualization**: Generates static and interactive visualizations

## Performance Optimizations

This framework includes several optimizations for handling large transport networks:

- **Graph Construction Sampling**: Reduces computation by sampling from all trips
- **Parallel Processing**: Uses multiprocessing for compute-intensive tasks
- **Memory-Efficient Algorithms**: Uses NetworkX views instead of full graph copies
- **Result Caching**: Caches intermediate results to speed up subsequent runs
- **Selective Execution**: Allows skipping specific analysis steps
- **Approximation Algorithms**: Uses faster approximations for betweenness centrality and clustering

## Example Visualizations

The framework generates several visualization types:

- Community maps showing transport regions
- Critical node identification
- Interactive network graphs
- Transport density heatmaps
- Community network visualizations

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Transport for Greater Manchester for GTFS data
- NetworkX team for the graph analysis library
- The researchers behind the Louvain method for community detection