"""
Scenario testing component for the transport network dashboard.
"""

import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd

def create_scenario_testing_tab(critical_nodes_df, community_df, community_analysis, 
                              simulate_node_removal, simulate_connection_addition, 
                              simulate_network_evolution):
    """
    Create the Scenario Testing tab content.
    
    Args:
        critical_nodes_df: DataFrame with critical nodes data
        community_df: DataFrame with community data
        community_analysis: Dictionary with community analysis
        simulate_node_removal: Callback function for node removal simulation
        simulate_connection_addition: Callback function for connection addition simulation
        simulate_network_evolution: Callback function for network evolution simulation
        
    Returns:
        Dash component
    """
    # Prepare critical nodes dropdown options
    node_options = []
    if not critical_nodes_df.empty:
        node_options = [
            {"label": f"{row['name']} (Community {row['community']})", "value": row['node_id']}
            for _, row in critical_nodes_df.iterrows()
        ]
    
    # Prepare community pairs dropdown options
    community_pairs = []
    if not community_df.empty:
        communities = sorted(community_df['community_id'].unique())
        for i in range(len(communities)):
            for j in range(i+1, len(communities)):
                comm1 = communities[i]
                comm2 = communities[j]
                community_pairs.append({
                    "label": f"Community {comm1} ↔ Community {comm2}",
                    "value": f"{comm1}-{comm2}"
                })
    
    # Prepare vulnerable communities data
    vulnerable_communities = []
    
    if community_analysis:
        for comm_id, data in community_analysis.items():
            if 'avg_degree' in data and data['avg_degree'] < 2:
                vulnerability = "High"
            elif 'density' in data and data['density'] < 0.2:
                vulnerability = "Medium" 
            else:
                vulnerability = "Low"
                
            vulnerable_communities.append({
                "community_id": comm_id,
                "size": data.get("size", 0),
                "density": data.get("density", 0),
                "vulnerability": vulnerability
            })
    
    vulnerable_df = pd.DataFrame(vulnerable_communities)
    
    # Create the tab content
    return html.Div([
        html.H2("Scenario Testing", className="mb-4"),
        
        dbc.Tabs([
            # Node Removal Simulation
            dbc.Tab([
                html.Div([
                    html.H3("Critical Node Failure Simulation", className="mb-3"),
                    html.P([
                        "This tool simulates the impact of removing critical nodes from the network, ",
                        "which helps identify vulnerabilities and plan for contingencies."
                    ]),
                    
                    # Node selection
                    html.Div([
                        html.Label("Select nodes to remove:"),
                        dcc.Dropdown(
                            id="node-removal-dropdown",
                            options=node_options,
                            value=[],
                            multi=True,
                            style={"width": "100%"}
                        ),
                        html.Button(
                            "Run Simulation", 
                            id="run-node-removal-btn",
                            className="btn btn-primary mt-3"
                        )
                    ], className="mb-4"),
                    
                    # Results display area
                    html.Div(id="node-removal-results")
                ], className="p-3")
            ], label="Node Failure", tab_id="node-failure-tab"),
            
            # Connection Addition Simulation
            dbc.Tab([
                html.Div([
                    html.H3("Connection Enhancement Simulation", className="mb-3"),
                    html.P([
                        "This tool simulates the effect of adding new connections between communities, ",
                        "which helps plan network expansions and improvements."
                    ]),
                    
                    # Community pair selection
                    html.Div([
                        html.Label("Select community pairs to connect:"),
                        dcc.Dropdown(
                            id="community-pair-dropdown",
                            options=community_pairs,
                            value=[],
                            multi=True,
                            style={"width": "100%"}
                        ),
                        
                        html.Div([
                            html.Label("Number of connections to add:"),
                            dcc.Slider(
                                id="connections-slider",
                                min=1,
                                max=10,
                                step=1,
                                value=3,
                                marks={i: str(i) for i in range(1, 11)},
                                className="mb-4"
                            )
                        ], className="mt-3"),
                        
                        html.Button(
                            "Run Simulation", 
                            id="run-connection-btn",
                            className="btn btn-primary mt-3"
                        )
                    ], className="mb-4"),
                    
                    # Results display area
                    html.Div(id="connection-results")
                ], className="p-3")
            ], label="Connection Enhancement", tab_id="connection-tab"),
            
            # Network Evolution Simulation
            dbc.Tab([
                html.Div([
                    html.H3("Network Evolution Simulation", className="mb-3"),
                    html.P([
                        "This tool simulates long-term network evolution strategies aimed at ",
                        "improving overall connectivity, equity, and resilience."
                    ]),
                    
                    # Vulnerable communities table
                    html.Div([
                        html.Label("Select vulnerable communities to improve:"),
                        dash_table.DataTable(
                            id="vulnerable-communities-table",
                            columns=[
                                {"name": "Community ID", "id": "community_id"},
                                {"name": "Size", "id": "size"},
                                {"name": "Density", "id": "density", "type": "numeric", "format": {"specifier": ".4f"}},
                                {"name": "Vulnerability", "id": "vulnerability"}
                            ],
                            data=vulnerable_df.to_dict('records'),
                            style_cell={'textAlign': 'left'},
                            style_data_conditional=[
                                {
                                    'if': {'filter_query': '{vulnerability} = "High"'},
                                    'backgroundColor': '#FFCCCC'
                                },
                                {
                                    'if': {'filter_query': '{vulnerability} = "Medium"'},
                                    'backgroundColor': '#FFFFCC'
                                }
                            ],
                            style_header={'fontWeight': 'bold'},
                            row_selectable="multi",
                            selected_rows=[],
                            page_size=10
                        )
                    ], className="mb-4"),
                    
                    # Strategy selection
                    html.Div([
                        html.Label("Select improvement strategy:"),
                        dcc.Dropdown(
                            id="improvement-strategy-dropdown",
                            options=[
                                {"label": "Add new direct connections", "value": "direct_connections"},
                                {"label": "Improve service frequency", "value": "frequency"},
                                {"label": "Create hub-and-spoke structure", "value": "hub_spoke"},
                                {"label": "Balanced multi-modal approach", "value": "multi_modal"}
                            ],
                            value="balanced",
                            style={"width": "100%"}
                        ),
                        
                        html.Button(
                            "Run Simulation", 
                            id="run-evolution-btn",
                            className="btn btn-primary mt-3"
                        )
                    ], className="mb-4"),
                    
                    # Results display area
                    html.Div(id="evolution-results")
                ], className="p-3")
            ], label="Network Evolution", tab_id="evolution-tab")
        ], id="scenario-tabs", active_tab="node-failure-tab"),
    ], className="p-3")