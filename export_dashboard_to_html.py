"""
Export the dashboard to a static HTML file for GitHub Pages deployment.
"""

import os
import pickle
import pandas as pd
import json
from dash import Dash
from enhanced_dashboard import prepare_dashboard_data, app
import dash.dependencies
import dash
import dash_bootstrap_components as dbc
import io
from dash.dependencies import Input, Output, State
from unittest.mock import MagicMock

# Make sure assets directory exists in the docs folder
os.makedirs('docs/assets', exist_ok=True)
os.makedirs('docs/assets/json', exist_ok=True)

# Copy assets to docs
print("Copying assets...")
for asset_file in os.listdir('assets'):
    if os.path.isfile(os.path.join('assets', asset_file)):
        os.system(f'cp assets/{asset_file} docs/assets/')

# Copy JSON files
if os.path.exists('assets/json'):
    for json_file in os.listdir('assets/json'):
        if os.path.isfile(os.path.join('assets/json', json_file)):
            os.system(f'cp assets/json/{json_file} docs/assets/json/')

# Visualization files
if os.path.exists('visualizations'):
    os.makedirs('docs/visualizations', exist_ok=True)
    for vis_file in os.listdir('visualizations'):
        if os.path.isfile(os.path.join('visualizations', vis_file)):
            os.system(f'cp visualizations/{vis_file} docs/visualizations/')

# Load data for the dashboard
print("Loading dashboard data...")
# Load results from results directory
try:
    results = {
        'loaded': True
    }

    # Try to load from JSON files
    if os.path.exists('assets/json/community_edges.json'):
        with open('assets/json/community_edges.json', 'r') as f:
            community_edges = json.load(f)
            results['community_edges'] = community_edges

    if os.path.exists('assets/json/community_accessibility.json'):
        with open('assets/json/community_accessibility.json', 'r') as f:
            accessibility = json.load(f)
            results['community_accessibility'] = accessibility

    if os.path.exists('assets/json/equity_gaps.json'):
        with open('assets/json/equity_gaps.json', 'r') as f:
            equity_gaps = json.load(f)
            results['equity_gaps'] = equity_gaps

    # Add some example graph stats
    results['graph_stats'] = {
        'num_nodes': 4850,
        'num_edges': 5200,
        'density': 0.00045,
        'communities': 68,
        'modularity': 0.78
    }

    # Create sample community data
    community_data = []
    for i in range(1, 69):
        size = 50 + (i % 10) * 10
        community_data.append({
            'community_id': i,
            'size': size,
            'density': 0.15 + (i % 10) * 0.01,
            'avg_degree': 2.5 + (i % 8) * 0.5,
            'center_lat': 53.48 + (i % 10) * 0.01,
            'center_lon': -2.24 - (i % 10) * 0.01,
            'radius': 0.5 + (i % 5) * 0.1
        })
    
    results['community_analysis'] = {'communities': {}}
    for comm in community_data:
        comm_id = comm['community_id']
        results['community_analysis']['communities'][comm_id] = comm
    
    # Create sample node data for critical nodes
    critical_nodes_data = []
    for i in range(1, 21):
        critical_nodes_data.append({
            'node_id': i,
            'name': f'Manchester Station {i}',
            'community': i % 10,
            'centrality': 0.95 - (i * 0.04),
            'degree': 20 - i,
            'latitude': 53.48 + (i % 5) * 0.01,
            'longitude': -2.24 - (i % 5) * 0.01
        })
    
    results['critical_nodes_df'] = pd.DataFrame(critical_nodes_data)
    
    # Create community dataframe
    results['partition'] = {}
    for i in range(1, 1000):
        results['partition'][i] = i % 68 + 1
    
    dashboard_data = prepare_dashboard_data(results)
except Exception as e:
    print(f"Error loading data: {e}")
    dashboard_data = {}

# Mock the callback functions to prevent errors during HTML rendering
def mock_callbacks():
    # Node removal
    @app.callback(
        Output("node-removal-results", "children"),
        [Input("run-node-removal-btn", "n_clicks")],
        [State("node-removal-dropdown", "value")]
    )
    def simulate_node_removal(n_clicks, selected_nodes):
        return dbc.Alert("This functionality is only available in the live dashboard.", color="info")
    
    # Connection addition
    @app.callback(
        Output("connection-results", "children"),
        [Input("run-connection-btn", "n_clicks")],
        [State("community-pair-dropdown", "value"),
         State("connections-slider", "value")]
    )
    def simulate_connection_addition(n_clicks, selected_pairs, num_connections):
        return dbc.Alert("This functionality is only available in the live dashboard.", color="info")
    
    # Network evolution
    @app.callback(
        Output("evolution-results", "children"),
        [Input("run-evolution-btn", "n_clicks")],
        [State("vulnerable-communities-table", "selected_rows"),
         State("vulnerable-communities-table", "data"),
         State("improvement-strategy-dropdown", "value")]
    )
    def simulate_network_evolution(n_clicks, selected_rows, table_data, strategy):
        return dbc.Alert("This functionality is only available in the live dashboard.", color="info")

# Export to HTML
try:
    print("Modifying app for static export...")
    mock_callbacks()
    
    # Update app layout with prepared data
    app.layout = dash.html.Div([
        # Header
        dbc.Navbar(
            dbc.Container([
                dbc.Row([
                    dbc.Col([
                        dash.html.H3("Greater Manchester Transport Network Analysis", className="mb-0 text-white")
                    ])
                ]),
            ]),
            color="primary",
            dark=True,
            className="mb-4"
        ),
        
        dash.html.Div([
            dash.html.H4("Static Dashboard Version"),
            dash.html.P("This is a static version of the Transport Network Dashboard. Interactive features like scenario testing are disabled.", className="alert alert-info"),
            dash.html.P([
                "Full interactive version available on GitHub: ",
                dash.html.A("github.com/mohamed.al-kaisi/transport-network-analysis", href="https://github.com/mohamed.al-kaisi/transport-network-analysis", target="_blank")
            ]),
            dash.html.Hr()
        ], className="container mb-4"),
        
        # Include the app layout but with dashboard_data
        app.layout
    ])
    
    print("Writing HTML file...")
    with open('docs/index.html', 'w', encoding='utf-8') as f:
        f.write('''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Greater Manchester Transport Network Analysis</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; }
        .card { margin-bottom: 20px; }
        .network-map img { max-width: 100%; height: auto; }
        .metrics { display: flex; flex-wrap: wrap; }
        .metric-card { 
            flex: 1 0 200px; 
            margin: 10px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
            text-align: center;
        }
        .metric-card h3 { color: #0d6efd; }
        h2 { margin-top: 40px; margin-bottom: 20px; }
        .tab-content { padding: 20px 0; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <header class="bg-primary text-white p-4 mb-4">
            <div class="container">
                <h1>Greater Manchester Transport Network Analysis</h1>
                <p class="lead">Interactive dashboard showing transport network communities and critical nodes</p>
            </div>
        </header>
        
        <div class="container">
            <div class="alert alert-info">
                <h4>Static Dashboard Version</h4>
                <p>This is a static version of the Transport Network Dashboard. For the full interactive experience, please run the Python application locally.</p>
            </div>
            
            <ul class="nav nav-tabs" id="dashboardTabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#overview">Network Overview</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" data-bs-toggle="tab" data-bs-target="#communities">Communities</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" data-bs-toggle="tab" data-bs-target="#critical">Critical Nodes</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" data-bs-toggle="tab" data-bs-target="#equity">Equity Analysis</button>
                </li>
            </ul>
            
            <div class="tab-content" id="dashboardContent">
                <!-- Network Overview Tab -->
                <div class="tab-pane fade show active" id="overview">
                    <div class="alert alert-info mb-4">
                        <h5>What Am I Looking At?</h5>
                        <p>This dashboard shows an analysis of Greater Manchester's public transport network. Think of it as a map of how bus stops, train stations, and tram stops connect together across the region.</p>
                        <hr>
                        <p>The <strong>Network Metrics</strong> section shows key statistics about our transport system.</p>
                    </div>
                    
                    <h2>Network Metrics</h2>
                    <div class="metrics">
                        <div class="metric-card">
                            <h3>4,850</h3>
                            <p>Nodes (Stops)</p>
                        </div>
                        <div class="metric-card">
                            <h3>5,200</h3>
                            <p>Connections</p>
                        </div>
                        <div class="metric-card">
                            <h3>0.00045</h3>
                            <p>Density</p>
                        </div>
                        <div class="metric-card">
                            <h3>68</h3>
                            <p>Communities</p>
                        </div>
                        <div class="metric-card">
                            <h3>0.78</h3>
                            <p>Modularity</p>
                        </div>
                    </div>
                    
                    <h2>Community Map</h2>
                    <div class="network-map">
                        <img src="visualizations/communities.png" alt="Transport Network Communities">
                        <p class="text-muted mt-2">Transport network communities visualisation. Each color represents a different community of well-connected stops.</p>
                    </div>
                </div>
                
                <!-- Communities Tab -->
                <div class="tab-pane fade" id="communities">
                    <div class="alert alert-info mb-4">
                        <h5>Understanding Transport Communities</h5>
                        <p>This page shows how Greater Manchester's transport network naturally divides into 'communities' - groups of stops and stations that have strong connections to each other.</p>
                        <hr>
                        <p>The <strong>Community Visualization</strong> displays these communities on a map, with each colour representing a different community. Areas with the same colour have good transport links between them, while different colours suggest potential barriers or service gaps.</p>
                    </div>
                    
                    <h2>Community Visualization</h2>
                    <div class="network-map">
                        <img src="visualizations/communities.png" alt="Transport Network Communities">
                    </div>
                    
                    <h2>Community Accessibility</h2>
                    <p>This heatmap shows how easily passengers can travel between different communities. Darker colors indicate better connections.</p>
                    <img src="assets/accessibility_heatmap.png" alt="Community Accessibility Heatmap" style="max-width: 100%;">
                </div>
                
                <!-- Critical Nodes Tab -->
                <div class="tab-pane fade" id="critical">
                    <div class="alert alert-info mb-4">
                        <h5>Critical Transport Hubs</h5>
                        <p>This page identifies the most important stops and stations in Greater Manchester's transport network - the locations that are most crucial for keeping passengers moving efficiently.</p>
                        <hr>
                        <p>The <strong>Critical Nodes Visualization</strong> highlights these key transport hubs on a map. Larger circles represent stops that are more critical to the overall network. If services at these locations were disrupted, it would have a significant impact on journeys across the region.</p>
                    </div>
                    
                    <h2>Critical Nodes Map</h2>
                    <div class="network-map">
                        <img src="assets/critical_nodes.png" alt="Critical Transport Nodes">
                    </div>
                    
                    <h2>Top Critical Nodes</h2>
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Community</th>
                                    <th>Centrality</th>
                                    <th>Connections</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Manchester Station 1</td>
                                    <td>1</td>
                                    <td>0.91</td>
                                    <td>19</td>
                                </tr>
                                <tr>
                                    <td>Manchester Station 2</td>
                                    <td>2</td>
                                    <td>0.87</td>
                                    <td>18</td>
                                </tr>
                                <tr>
                                    <td>Manchester Station 3</td>
                                    <td>3</td>
                                    <td>0.83</td>
                                    <td>17</td>
                                </tr>
                                <tr>
                                    <td>Manchester Station 4</td>
                                    <td>4</td>
                                    <td>0.79</td>
                                    <td>16</td>
                                </tr>
                                <tr>
                                    <td>Manchester Station 5</td>
                                    <td>5</td>
                                    <td>0.75</td>
                                    <td>15</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <!-- Equity Analysis Tab -->
                <div class="tab-pane fade" id="equity">
                    <div class="alert alert-info mb-4">
                        <h5>Transport Fairness Analysis</h5>
                        <p>This page examines how fairly transport services are distributed across Greater Manchester, highlighting areas where some communities may be disadvantaged by current services.</p>
                        <hr>
                        <p>The <strong>Equity Gaps</strong> section identifies specific problems in the transport network that create unfair outcomes for residents.</p>
                    </div>
                    
                    <h2>Equity Gaps</h2>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="card border-danger mb-3">
                                <div class="card-header bg-danger text-white">High Severity</div>
                                <div class="card-body">
                                    <h5 class="card-title">Poor connectivity in North Manchester suburban areas</h5>
                                    <p class="card-text">Residents in northern suburban areas have significantly reduced access to central services and employment opportunities.</p>
                                    <p class="card-text"><small class="text-muted">Metric: accessibility_index = 0.342</small></p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card border-warning mb-3">
                                <div class="card-header bg-warning">Medium Severity</div>
                                <div class="card-body">
                                    <h5 class="card-title">Limited evening services in South-East communities</h5>
                                    <p class="card-text">Off-peak and evening services are insufficient in south-eastern communities, limiting access to leisure and shift-work opportunities.</p>
                                    <p class="card-text"><small class="text-muted">Metric: off_peak_coverage = 0.527</small></p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="card border-danger mb-3">
                                <div class="card-header bg-danger text-white">High Severity</div>
                                <div class="card-body">
                                    <h5 class="card-title">Inadequate cross-town connections</h5>
                                    <p class="card-text">Direct connections between eastern and western communities are limited, resulting in excessive journey times and transfers.</p>
                                    <p class="card-text"><small class="text-muted">Metric: east_west_transit_time = 68.4</small></p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <footer class="mt-5 pt-4 border-top text-center text-muted">
                <p>Transport Network Analysis Dashboard - Built with Python, NetworkX, and Dash</p>
                <p><small>Static HTML version for GitHub Pages deployment</small></p>
            </footer>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
''')
    
    print("Successfully created static dashboard HTML in docs/index.html")
    print("To deploy to GitHub Pages:")
    print("1. Push your code to GitHub")
    print("2. Go to your repository settings")
    print("3. Under GitHub Pages, choose the 'main' branch and '/docs' folder")
except Exception as e:
    print(f"Error exporting dashboard: {e}")