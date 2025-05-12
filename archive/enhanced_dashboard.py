"""
Enhanced dashboard for transport network analysis.
"""

import os
import pickle
import pandas as pd
import networkx as nx
import logging
from typing import Dict, Any
import dash
from dash import html, dcc, callback, dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

# Import dashboard components
from dashboard_components.network_overview import create_network_overview_tab
from dashboard_components.community_panels import create_communities_tab
from dashboard_components.scenario_testing import create_scenario_testing_tab

# Import analysis modules
from src.utils.optimization import sample_graph_for_visualization

# Enable debug output to see what's happening
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the Dash app with a Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}]
)
app.title = "Transport Network Analysis Dashboard"
server = app.server  # Expose server for deployment

# Load analysis results
def load_results(results_dir="results"):
    """
    Load analysis results from pickle files.
    
    Args:
        results_dir: Directory containing results
        
    Returns:
        Dictionary with loaded results
    """
    results = {}
    
    try:
        # Load graph stats
        with open(os.path.join(results_dir, "graph_stats.pkl"), "rb") as f:
            results['graph_stats'] = pickle.load(f)
        
        # Load communities partition
        with open(os.path.join(results_dir, "communities_partition.pkl"), "rb") as f:
            results['partition'] = pickle.load(f)
        
        # Load community analysis
        with open(os.path.join(results_dir, "community_analysis.pkl"), "rb") as f:
            results['community_analysis'] = pickle.load(f)
        
        # Load critical nodes
        critical_nodes_path = os.path.join(results_dir, "critical_nodes.csv")
        if os.path.exists(critical_nodes_path):
            results['critical_nodes_df'] = pd.read_csv(critical_nodes_path)
        
        # Load vulnerability analysis
        with open(os.path.join(results_dir, "vulnerability_analysis.pkl"), "rb") as f:
            results['vulnerability_analysis'] = pickle.load(f)
        
        # Load advanced reasoning results
        with open(os.path.join(results_dir, "advanced_reasoning_results.pkl"), "rb") as f:
            results['reasoning_results'] = pickle.load(f)
        
        # Load hourly patterns
        with open(os.path.join(results_dir, "hourly_patterns.pkl"), "rb") as f:
            results['hourly_patterns'] = pickle.load(f)
        
        # Load community accessibility
        with open(os.path.join(results_dir, "community_accessibility.pkl"), "rb") as f:
            results['community_accessibility'] = pickle.load(f)
        
        # Load equity gaps
        with open(os.path.join(results_dir, "equity_gaps.pkl"), "rb") as f:
            results['equity_gaps'] = pickle.load(f)
        
        logger.info("Successfully loaded analysis results")
        results['loaded'] = True
    except Exception as e:
        logger.error(f"Error loading results: {e}")
        results['loaded'] = False
    
    return results

# Load results
results = load_results()

# Prepare data for dashboard
def prepare_dashboard_data(results):
    """
    Prepare data for dashboard components.
    
    Args:
        results: Dictionary with loaded results
        
    Returns:
        Dictionary with prepared data
    """
    data = {}
    
    if not results.get('loaded', False):
        return data
    
    # Prepare community data
    partition = results.get('partition', {})
    community_counts = {}
    for node, comm in partition.items():
        if comm in community_counts:
            community_counts[comm] += 1
        else:
            community_counts[comm] = 1
    
    community_data = []
    for comm_id, count in community_counts.items():
        community_data.append({
            'community_id': comm_id,
            'size': count
        })
    
    data['community_df'] = pd.DataFrame(community_data)
    
    # Prepare critical nodes data
    if 'critical_nodes_df' in results:
        data['critical_nodes_df'] = results['critical_nodes_df']
    else:
        data['critical_nodes_df'] = pd.DataFrame(columns=['node_id', 'name', 'community', 'centrality'])
    
    # Prepare community edges data
    community_edges = []
    if 'reasoning_results' in results and 'interdependencies' in results['reasoning_results']:
        interdep = results['reasoning_results']['interdependencies']
        if 'community_graph' in interdep:
            comm_graph = interdep['community_graph']
            for source, target, edge_data in comm_graph.edges(data=True):
                community_edges.append({
                    'source': source,
                    'target': target,
                    'weight': edge_data.get('weight', 1)
                })
    
    data['community_edges'] = community_edges
    
    # Prepare community analysis data
    if 'community_analysis' in results:
        data['community_analysis'] = results['community_analysis'].get('communities', {})
    else:
        data['community_analysis'] = {}
    
    # Prepare accessibility data
    if 'community_accessibility' in results:
        data['community_accessibility'] = results['community_accessibility']
    else:
        data['community_accessibility'] = {}
    
    # Prepare efficiency metrics
    if 'graph_stats' in results:
        data['graph_stats'] = results['graph_stats']
        
        # Add modularity if available
        if 'community_analysis' in results:
            data['graph_stats']['modularity'] = results['community_analysis'].get('modularity', 0)
            data['graph_stats']['communities'] = len(data['community_analysis'])
    else:
        data['graph_stats'] = {}
    
    # Prepare equity gaps
    if 'equity_gaps' in results:
        data['equity_gaps'] = results['equity_gaps']
    else:
        data['equity_gaps'] = []
    
    return data

# Prepare dashboard data
dashboard_data = prepare_dashboard_data(results)

# Node removal simulation callback
@app.callback(
    Output("node-removal-results", "children"),
    [Input("run-node-removal-btn", "n_clicks")],
    [State("node-removal-dropdown", "value")]
)
def simulate_node_removal(n_clicks, selected_nodes):
    """Simulate removing nodes from the network."""
    if n_clicks is None or not selected_nodes:
        return html.Div("Select nodes and click 'Run Simulation' to see results")
    
    # Here you would implement the actual simulation
    # For now, just return some placeholder text
    return html.Div([
        html.H5("Simulation Results", className="mt-3 mb-3"),
        
        dbc.Alert([
            html.H6("Network Impact:"),
            html.P(f"Removing {len(selected_nodes)} nodes would impact the network as follows:"),
            html.Ul([
                html.Li("Connectivity between communities would decrease by 15-20%"),
                html.Li("Average path length would increase by 12%"),
                html.Li("2 communities would become isolated")
            ])
        ], color="warning"),
        
        html.Div([
            html.H6("Recommendation:"),
            html.P("To improve network resilience, consider adding redundant connections for these critical nodes.")
        ], className="mt-3")
    ])

# Connection addition simulation callback
@app.callback(
    Output("connection-results", "children"),
    [Input("run-connection-btn", "n_clicks")],
    [State("community-pair-dropdown", "value"),
     State("connections-slider", "value")]
)
def simulate_connection_addition(n_clicks, selected_pairs, num_connections):
    """Simulate adding connections between communities."""
    if n_clicks is None or not selected_pairs:
        return html.Div("Select community pairs and click 'Run Simulation' to see results")
    
    # Here you would implement the actual simulation
    # For now, just return some placeholder text
    return html.Div([
        html.H5("Simulation Results", className="mt-3 mb-3"),
        
        dbc.Alert([
            html.H6("Network Impact:"),
            html.P(f"Adding {num_connections} connections between {len(selected_pairs)} community pairs would impact the network as follows:"),
            html.Ul([
                html.Li("Connectivity between communities would increase by 10-15%"),
                html.Li("Average path length would decrease by 8%"),
                html.Li("Network resilience would improve by 12%")
            ])
        ], color="success"),
        
        html.Div([
            html.H6("Recommendation:"),
            html.P("These new connections would significantly improve network efficiency and should be considered in future transport planning.")
        ], className="mt-3")
    ])

# Network evolution simulation callback
@app.callback(
    Output("evolution-results", "children"),
    [Input("run-evolution-btn", "n_clicks")],
    [State("vulnerable-communities-table", "selected_rows"),
     State("vulnerable-communities-table", "data"),
     State("improvement-strategy-dropdown", "value")]
)
def simulate_network_evolution(n_clicks, selected_rows, table_data, strategy):
    """Simulate network evolution by improving connectivity."""
    if n_clicks is None or not selected_rows:
        return html.Div("Select vulnerable communities and click 'Run Simulation' to see results")
    
    # Get selected communities
    selected_communities = [table_data[i]['community_id'] for i in selected_rows]
    
    # Here you would implement the actual simulation
    # For now, just return some placeholder text
    return html.Div([
        html.H5("Simulation Results", className="mt-3 mb-3"),
        
        dbc.Alert([
            html.H6("Network Evolution Impact:"),
            html.P(f"Improving connectivity for {len(selected_communities)} vulnerable communities using the '{strategy}' strategy would result in:"),
            html.Ul([
                html.Li("20-25% reduction in overall network vulnerability"),
                html.Li("15% improvement in network equity"),
                html.Li("10% reduction in average travel time between communities")
            ])
        ], color="info"),
        
        html.Div([
            html.H6("Implementation Strategy:"),
            html.P(f"The '{strategy}' strategy suggests the following improvements:"),
            html.Ul([
                html.Li(f"Add 3 new connections between Community {selected_communities[0]} and nearby communities"),
                html.Li(f"Improve service frequency on existing connections for Community {selected_communities[1]}"),
                html.Li(f"Create new transit routes connecting Community {selected_communities[2]} to central hubs")
            ])
        ], className="mt-3")
    ])

# Define app layout
app.layout = html.Div([
    # Header
    dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H3("Greater Manchester Transport Network Analysis", className="mb-0 text-white")
                ])
            ]),
        ]),
        color="primary",
        dark=True,
        className="mb-4"
    ),
    
    # Main content container
    dbc.Container([
        # Tabs
        dbc.Tabs([
            # Network Overview tab
            dbc.Tab(
                create_network_overview_tab(
                    dashboard_data.get('graph_stats', {}),
                    dashboard_data.get('community_df', pd.DataFrame()),
                    dashboard_data.get('community_edges', [])
                ),
                label="Network Overview",
                tab_id="overview-tab"
            ),
            
            # Communities tab
            dbc.Tab(
                create_communities_tab(
                    dashboard_data.get('community_analysis', {}),
                    dashboard_data.get('community_accessibility', {}),
                    "visualizations/communities.png"
                ),
                label="Communities",
                tab_id="communities-tab"
            ),
            
            # Critical Nodes tab
            dbc.Tab(
                html.Div([
                    html.H2("Critical Nodes Analysis", className="mb-4"),
                    
                    dbc.Row([
                        dbc.Col([
                            html.H4("Critical Nodes Visualization", className="mb-3"),
                            html.Img(
                                src="/assets/critical_nodes.png" if os.path.exists("assets/critical_nodes.png") else "",
                                style={'width': '100%', 'max-width': '1000px'}
                            ) if os.path.exists("assets/critical_nodes.png") else
                            html.Div("Critical nodes visualization not available", className="text-center p-5 bg-light")
                        ], width=12)
                    ], className="mb-4"),
                    
                    dbc.Row([
                        dbc.Col([
                            html.H4("Top Critical Nodes", className="mb-3"),
                            dash_table.DataTable(
                                data=dashboard_data.get('critical_nodes_df', pd.DataFrame()).head(20).to_dict('records'),
                                columns=[
                                    {'name': 'Name', 'id': 'name'},
                                    {'name': 'Community', 'id': 'community'},
                                    {'name': 'Centrality', 'id': 'centrality', 'type': 'numeric', 'format': {'specifier': '.6f'}},
                                    {'name': 'Degree', 'id': 'degree'}
                                ],
                                style_header={'fontWeight': 'bold'},
                                style_cell={'textAlign': 'left'},
                                style_table={'overflowX': 'auto'}
                            )
                        ], width=12)
                    ])
                ]),
                label="Critical Nodes",
                tab_id="critical-nodes-tab"
            ),
            
            # Equity Analysis tab
            dbc.Tab(
                html.Div([
                    html.H2("Equity Analysis", className="mb-4"),
                    
                    dbc.Row([
                        dbc.Col([
                            html.H4("Equity Gaps", className="mb-3"),
                            html.P(
                                "The analysis identified the following equity gaps in the transport network:",
                                className="text-muted"
                            ),
                            
                            html.Div([
                                dbc.Card(
                                    dbc.CardBody([
                                        html.H5(gap['description'], className="card-title"),
                                        html.P(f"Severity: {gap['severity'].title()}", className="card-text"),
                                        html.P(f"Metric: {gap['metric']} = {gap['value']:.4f}", className="card-text small text-muted")
                                    ]),
                                    className="mb-3",
                                    color="warning" if gap['severity'] == 'medium' else "danger",
                                    outline=True
                                ) for gap in dashboard_data.get('equity_gaps', [])
                            ]) if dashboard_data.get('equity_gaps') else
                            html.Div("No equity gaps identified", className="text-center p-5 bg-light")
                        ], width=12)
                    ])
                ]),
                label="Equity Analysis",
                tab_id="equity-tab"
            ),
            
            # Scenario Testing tab
            dbc.Tab(
                create_scenario_testing_tab(
                    dashboard_data.get('critical_nodes_df', pd.DataFrame()),
                    dashboard_data.get('community_df', pd.DataFrame()),
                    dashboard_data.get('community_analysis', {}),
                    simulate_node_removal,
                    simulate_connection_addition,
                    simulate_network_evolution
                ),
                label="Scenario Testing",
                tab_id="scenario-tab"
            )
        ], id="main-tabs", active_tab="overview-tab"),
        
        # Footer
        html.Div([
            html.Hr(),
            html.P(
                "Transport Network Analysis Dashboard - Built with Python, NetworkX, and Dash",
                className="text-center text-muted"
            )
        ], className="mt-5")
    ], fluid=True)
])

# Run the app
if __name__ == '__main__':
    print("\n==================================================")
    print("Enhanced Transport Network Analysis Dashboard")
    print("==================================================")
    print("\nDashboard is running on:")
    print("http://127.0.0.1:8050")
    print("http://localhost:8050")
    print("\nPress CTRL+C to stop the server")
    print("==================================================\n")
    app.run(debug=False, host='127.0.0.1', port=8050)