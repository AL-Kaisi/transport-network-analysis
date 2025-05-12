"""
Network overview component for the transport network dashboard.
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import networkx as nx

def create_community_size_chart(community_data):
    """
    Create a histogram of community sizes.
    
    Args:
        community_data: DataFrame or dictionary with community information
    
    Returns:
        Plotly figure object
    """
    import plotly.express as px
    import pandas as pd
    
    # Check if community_data is empty
    if community_data is None or (isinstance(community_data, dict) and not community_data):
        # Return an empty chart with a message
        fig = px.bar(
            x=["No Data"], 
            y=[0],
            labels={"x": "Status", "y": "Count"},
            title="Community Size Distribution (No Data Available)"
        )
        fig.update_layout(
            annotations=[{
                "text": "No community data available. Run analysis first.",
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False
            }]
        )
        return fig
    
    # Check the structure of community_data and convert to dataframe if needed
    if isinstance(community_data, dict):
        # If it's a dictionary of community information
        if 'sizes' in community_data:
            # If it has a 'sizes' key that contains community sizes
            df = pd.DataFrame({"community": list(community_data['sizes'].keys()), 
                             "size": list(community_data['sizes'].values())})
        else:
            # If it's a partition dictionary {node_id: community_id}
            # Count occurrences of each community
            community_counts = {}
            for node, comm in community_data.items():
                if comm not in community_counts:
                    community_counts[comm] = 0
                community_counts[comm] += 1
            
            df = pd.DataFrame({"community": list(community_counts.keys()), 
                             "size": list(community_counts.values())})
    elif isinstance(community_data, pd.DataFrame):
        # If already a DataFrame, check for required columns
        if 'size' not in community_data.columns:
            # If no 'size' column, check for alternatives or assume it needs to be aggregated
            if 'community' in community_data.columns:
                # Count nodes per community
                df = community_data.groupby('community').size().reset_index()
                df.columns = ['community', 'size']
            else:
                # If we can't find usable data, create an empty dataframe with right columns
                df = pd.DataFrame({"community": [], "size": []})
        else:
            # DataFrame already has right structure
            df = community_data
    else:
        # Fallback: create empty dataframe with right structure
        df = pd.DataFrame({"community": [], "size": []})
    
    # Now create the histogram with the properly structured data
    if len(df) > 0:
        fig = px.histogram(
            df,
            x="size",
            nbins=20,
            labels={"size": "Number of Stops", "count": "Number of Communities"},
            title="Community Size Distribution"
        )
        
        fig.update_layout(
            xaxis_title="Community Size (Number of Stops)",
            yaxis_title="Number of Communities",
            bargap=0.1
        )
    else:
        # If dataframe is empty, return message
        fig = px.bar(
            x=["No Data"], 
            y=[0],
            labels={"x": "Status", "y": "Count"},
            title="Community Size Distribution (No Data Available)"
        )
        fig.update_layout(
            annotations=[{
                "text": "No community data available. Run analysis first.",
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False
            }]
        )
    
    return fig

def create_network_metrics_cards(graph_stats):
    """
    Create cards displaying key network metrics.
    
    Args:
        graph_stats: Dictionary with graph statistics
        
    Returns:
        Dash component
    """
    if not graph_stats:
        return html.Div([
            html.H4("Network Metrics", className="mb-3"),
            html.P("No network data available. Run analysis to see metrics.")
        ], className="p-3 border rounded bg-light")
    
    # Create cards for key metrics
    metrics = [
        {"name": "Nodes", "value": graph_stats.get("num_nodes", 0), "description": "Total stops in network"},
        {"name": "Edges", "value": graph_stats.get("num_edges", 0), "description": "Connections between stops"},
        {"name": "Density", "value": f"{graph_stats.get('density', 0):.6f}", "description": "Network connectivity ratio"},
        {"name": "Communities", "value": graph_stats.get("communities", 0), "description": "Distinct network regions"},
        {"name": "Modularity", "value": f"{graph_stats.get('modularity', 0):.4f}", "description": "Community structure strength"}
    ]
    
    cards = []
    for metric in metrics:
        cards.append(
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(metric["name"], className="card-title"),
                        html.H2(metric["value"], className="text-primary"),
                        html.P(metric["description"], className="text-muted small")
                    ])
                ], className="mb-3 text-center")
            ], width=12 // len(metrics))
        )
    
    return html.Div([
        html.H4("Network Metrics", className="mb-3"),
        dbc.Row(cards)
    ])

def create_community_network_graph(community_edges):
    """
    Create a network graph visualization showing communities and their connections.
    
    Args:
        community_edges: List of edges between communities
        
    Returns:
        Plotly figure object
    """
    if not community_edges:
        fig = go.Figure()
        fig.update_layout(
            title="Community Network (No Data Available)",
            annotations=[{
                "text": "No community network data available.",
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False
            }]
        )
        return fig
    
    # Create networkx graph from edges
    G = nx.Graph()
    for edge in community_edges:
        source = edge.get('source')
        target = edge.get('target')
        weight = edge.get('weight', 1)
        G.add_edge(source, target, weight=weight)
    
    # Use spring layout for positioning
    pos = nx.spring_layout(G, seed=42)
    
    # Create edge traces
    edge_traces = []
    for edge in G.edges(data=True):
        source, target, data = edge
        x0, y0 = pos[source]
        x1, y1 = pos[target]
        weight = data.get('weight', 1)
        
        edge_trace = go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            line=dict(width=weight, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        edge_traces.append(edge_trace)
    
    # Create node trace
    node_trace = go.Scatter(
        x=[pos[node][0] for node in G.nodes()],
        y=[pos[node][1] for node in G.nodes()],
        text=[f"Community {node}<br>Connections: {G.degree[node]}" for node in G.nodes()],
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='Viridis',
            size=10,
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left'
            ),
            color=[G.degree[node] for node in G.nodes()],
            line_width=2
        )
    )
    
    # Create figure
    fig = go.Figure(data=edge_traces + [node_trace])
    fig.update_layout(
        title="Community Network",
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )
    
    return fig

def create_network_overview_tab(graph_stats, community_df, community_edges):
    """
    Create the Network Overview tab content.
    
    Args:
        graph_stats: Dictionary with graph statistics
        community_df: DataFrame with community information
        community_edges: List of edges between communities
        
    Returns:
        Dash component
    """
    return html.Div([
        html.H2("Network Overview", className="mb-4"),
        
        # Network metrics section
        dbc.Card([
            dbc.CardBody([
                create_network_metrics_cards(graph_stats)
            ])
        ], className="mb-4"),
        
        # Community size distribution and community network
        dbc.Row([
            # Community size distribution
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Community Size Distribution"),
                        dcc.Graph(figure=create_community_size_chart(community_df))
                    ])
                ])
            ], width=6),
            
            # Community network graph
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Community Network"),
                        dcc.Graph(figure=create_community_network_graph(community_edges))
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        
        # Network summary
        dbc.Card([
            dbc.CardBody([
                html.H4("Network Summary"),
                html.P([
                    "This analysis examines the transport network structure of Greater Manchester, ",
                    "identifying communities of well-connected stops and critical nodes that serve as key connection points."
                ]),
                html.P([
                    "The network contains ", 
                    html.Strong(f"{graph_stats.get('num_nodes', 0):,}"), 
                    " stops with ",
                    html.Strong(f"{graph_stats.get('num_edges', 0):,}"),
                    " connections between them, organized into ",
                    html.Strong(f"{graph_stats.get('communities', 0)}"),
                    " distinct communities."
                ]) if graph_stats else html.P("Run the analysis to see network details.")
            ])
        ])
    ], className="p-3")