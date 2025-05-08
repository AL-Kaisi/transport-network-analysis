"""
Scenario testing components for the dashboard.
"""

import dash
from dash import html, dcc, dash_table, callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import networkx as nx
import numpy as np
from typing import Dict, Any, List, Callable

def create_node_removal_panel(
    critical_nodes_df: pd.DataFrame,
    simulate_callback: Callable
) -> html.Div:
    """
    Create a panel for testing node removal scenarios.
    
    Args:
        critical_nodes_df: DataFrame with critical nodes data
        simulate_callback: Callback function to simulate node removal
        
    Returns:
        Dash HTML component
    """
    return html.Div([
        html.H4("Node Removal Simulation", className="mb-3"),
        
        html.P(
            "Test how removing critical nodes affects the network. "
            "Select nodes to remove and run the simulation.",
            className="text-muted"
        ),
        
        dbc.Row([
            dbc.Col([
                # Dropdown to select nodes
                html.Label("Select nodes to remove:"),
                dcc.Dropdown(
                    id='node-removal-dropdown',
                    options=[
                        {'label': f"{row['name']} (ID: {row['node_id']})", 'value': row['node_id']}
                        for _, row in critical_nodes_df.iterrows()
                    ],
                    placeholder="Select nodes to remove",
                    multi=True,
                    className="mb-3"
                ),
                
                # Simulation button
                dbc.Button(
                    "Run Simulation",
                    id="run-node-removal-btn",
                    color="primary",
                    className="mt-2"
                )
            ], width=12)
        ]),
        
        # Results container
        html.Div(id="node-removal-results", className="mt-4")
    ])

def create_connection_addition_panel(
    community_data: pd.DataFrame,
    simulate_callback: Callable
) -> html.Div:
    """
    Create a panel for testing new connection scenarios.
    
    Args:
        community_data: DataFrame with community data
        simulate_callback: Callback function to simulate new connections
        
    Returns:
        Dash HTML component
    """
    # Create options for community pairs
    community_ids = community_data['community_id'].unique()
    pair_options = []
    
    for i, c1 in enumerate(community_ids):
        for c2 in community_ids[i+1:]:
            pair_options.append({
                'label': f"Community {c1} - Community {c2}",
                'value': f"{c1}-{c2}"
            })
    
    return html.Div([
        html.H4("Connection Addition Simulation", className="mb-3"),
        
        html.P(
            "Test how adding new connections between communities affects the network. "
            "Select community pairs to connect and run the simulation.",
            className="text-muted"
        ),
        
        dbc.Row([
            dbc.Col([
                # Dropdown to select community pairs
                html.Label("Select community pairs to connect:"),
                dcc.Dropdown(
                    id='community-pair-dropdown',
                    options=pair_options,
                    placeholder="Select community pairs to connect",
                    multi=True,
                    className="mb-3"
                ),
                
                # Number of connections to add
                html.Label("Number of connections to add per pair:"),
                dcc.Slider(
                    id='connections-slider',
                    min=1,
                    max=5,
                    step=1,
                    value=2,
                    marks={i: str(i) for i in range(1, 6)},
                    className="mb-3"
                ),
                
                # Simulation button
                dbc.Button(
                    "Run Simulation",
                    id="run-connection-btn",
                    color="success",
                    className="mt-2"
                )
            ], width=12)
        ]),
        
        # Results container
        html.Div(id="connection-results", className="mt-4")
    ])

def create_network_evolution_panel(
    community_metrics: Dict[int, Dict[str, Any]],
    simulate_callback: Callable
) -> html.Div:
    """
    Create a panel for testing network evolution scenarios.
    
    Args:
        community_metrics: Dictionary with community metrics
        simulate_callback: Callback function to simulate network evolution
        
    Returns:
        Dash HTML component
    """
    # Sort communities by vulnerability
    vulnerability = []
    for comm_id, metrics in community_metrics.items():
        vulnerability.append({
            'community_id': comm_id,
            'vulnerability': metrics.get('vulnerability', 0),
            'size': metrics.get('size', 0)
        })
    
    vulnerability_df = pd.DataFrame(vulnerability)
    vulnerability_df = vulnerability_df.sort_values('vulnerability', ascending=False)
    
    return html.Div([
        html.H4("Network Evolution Simulation", className="mb-3"),
        
        html.P(
            "Test how improving connectivity for vulnerable communities affects the network. "
            "Select communities to improve and run the simulation.",
            className="text-muted"
        ),
        
        dbc.Row([
            dbc.Col([
                # Table of vulnerable communities
                html.Label("Vulnerable Communities:"),
                dash_table.DataTable(
                    id='vulnerable-communities-table',
                    columns=[
                        {'name': 'Community ID', 'id': 'community_id'},
                        {'name': 'Vulnerability', 'id': 'vulnerability', 'type': 'numeric', 'format': {'specifier': '.4f'}},
                        {'name': 'Size', 'id': 'size'}
                    ],
                    data=vulnerability_df.head(10).to_dict('records'),
                    row_selectable='multi',
                    selected_rows=[0, 1, 2],  # Select top 3 by default
                    style_cell={'textAlign': 'left'},
                    style_header={'fontWeight': 'bold'},
                    style_table={'overflowX': 'auto'}
                ),
                
                # Improvement strategy dropdown
                html.Label("Improvement Strategy:", className="mt-3"),
                dcc.Dropdown(
                    id='improvement-strategy-dropdown',
                    options=[
                        {'label': 'Connect to nearest communities', 'value': 'nearest'},
                        {'label': 'Connect to largest communities', 'value': 'largest'},
                        {'label': 'Connect to central communities', 'value': 'central'}
                    ],
                    value='nearest',
                    className="mb-3"
                ),
                
                # Simulation button
                dbc.Button(
                    "Run Simulation",
                    id="run-evolution-btn",
                    color="info",
                    className="mt-2"
                )
            ], width=12)
        ]),
        
        # Results container
        html.Div(id="evolution-results", className="mt-4")
    ])

def create_scenario_testing_tab(
    critical_nodes_df: pd.DataFrame,
    community_data: pd.DataFrame,
    community_metrics: Dict[int, Dict[str, Any]],
    node_removal_callback: Callable,
    connection_callback: Callable,
    evolution_callback: Callable
) -> html.Div:
    """
    Create the scenario testing tab.
    
    Args:
        critical_nodes_df: DataFrame with critical nodes data
        community_data: DataFrame with community data
        community_metrics: Dictionary with community metrics
        node_removal_callback: Callback for node removal simulation
        connection_callback: Callback for connection addition simulation
        evolution_callback: Callback for network evolution simulation
        
    Returns:
        Dash HTML component
    """
    return html.Div([
        html.H2("Scenario Testing", className="mb-4"),
        
        dbc.Tabs([
            dbc.Tab(
                create_node_removal_panel(critical_nodes_df, node_removal_callback),
                label="Node Removal",
                tab_id="node-removal-tab"
            ),
            
            dbc.Tab(
                create_connection_addition_panel(community_data, connection_callback),
                label="Add Connections",
                tab_id="add-connections-tab"
            ),
            
            dbc.Tab(
                create_network_evolution_panel(community_metrics, evolution_callback),
                label="Network Evolution",
                tab_id="network-evolution-tab"
            )
        ], id="scenario-tabs")
    ])