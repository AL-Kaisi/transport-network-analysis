"""
Community panels component for the transport network dashboard.
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import base64

def create_community_stats_table(community_data):
    """
    Create a table showing statistics for each community.
    
    Args:
        community_data: Dictionary with community analysis data
        
    Returns:
        Dash component
    """
    if not community_data:
        return html.Div([
            html.P("No community data available. Run analysis to see community statistics.")
        ], className="text-center p-3")
    
    # Convert to DataFrame for easier handling
    rows = []
    for comm_id, data in community_data.items():
        rows.append({
            "Community ID": comm_id,
            "Size": data.get("size", 0),
            "Density": f"{data.get('density', 0):.4f}",
            "Avg. Degree": f"{data.get('avg_degree', 0):.2f}",
            "Has Geographic Data": "Yes" if data.get("center_lat") is not None else "No"
        })
    
    if not rows:
        return html.Div([
            html.P("No community data available. Run analysis to see community statistics.")
        ], className="text-center p-3")
    
    # Create table
    df = pd.DataFrame(rows)
    
    return html.Div([
        html.H4("Community Statistics", className="mb-3"),
        dbc.Table.from_dataframe(
            df.sort_values("Size", ascending=False).head(15),
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            className="mb-3"
        ),
        html.P(f"Showing top 15 of {len(df)} communities by size", className="text-muted")
    ])

def create_accessibility_heatmap(accessibility_data):
    """
    Create a heatmap showing accessibility between communities.
    
    Args:
        accessibility_data: Dictionary with accessibility data
        
    Returns:
        Plotly figure object
    """
    if not accessibility_data:
        fig = go.Figure()
        fig.update_layout(
            title="Community Accessibility (No Data)",
            annotations=[{
                "text": "No accessibility data available.",
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False
            }]
        )
        return fig
    
    # Extract data for heatmap
    communities = sorted(list(accessibility_data.keys()))
    z_data = []
    
    for comm1 in communities:
        row = []
        for comm2 in communities:
            value = accessibility_data.get(comm1, {}).get(comm2, 0)
            row.append(value)
        z_data.append(row)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=[f"C{c}" for c in communities],
        y=[f"C{c}" for c in communities],
        colorscale='Viridis',
        colorbar=dict(title="Accessibility Score")
    ))
    
    fig.update_layout(
        title="Community Accessibility",
        xaxis_title="Destination Community",
        yaxis_title="Origin Community"
    )
    
    return fig

def encode_image(image_path):
    """
    Encode an image file as base64.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64 encoded image string
    """
    try:
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{encoded}"
    except Exception as e:
        return ""

def create_communities_tab(community_data, accessibility_data, visualization_path):
    """
    Create the Communities tab content.
    
    Args:
        community_data: Dictionary with community analysis data
        accessibility_data: Dictionary with accessibility data
        visualization_path: Path to the community visualization image
        
    Returns:
        Dash component
    """
    return html.Div([
        html.H2("Transport Network Communities", className="mb-4"),
        
        # Communities visualization and stats
        dbc.Row([
            # Community visualization
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Community Visualization"),
                        html.Img(
                            src=encode_image(visualization_path),
                            style={'width': '100%', 'max-width': '100%'},
                            className="img-fluid"
                        ) if visualization_path else html.P("No visualization available")
                    ])
                ])
            ], width=7),
            
            # Community statistics
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        create_community_stats_table(community_data)
                    ])
                ])
            ], width=5)
        ], className="mb-4"),
        
        # Community accessibility
        dbc.Card([
            dbc.CardBody([
                html.H4("Community Accessibility Analysis"),
                dcc.Graph(figure=create_accessibility_heatmap(accessibility_data))
            ])
        ], className="mb-4"),
        
        # Community analysis summary
        dbc.Card([
            dbc.CardBody([
                html.H4("Community Analysis Summary"),
                html.P([
                    "The transport network of Greater Manchester is divided into communities based on the strength of connections ",
                    "between stops. Each community represents a set of stops that are more densely connected to each other than ",
                    "to the rest of the network."
                ]),
                html.P([
                    "Communities typically represent geographic areas or transit corridors with strong internal connectivity. ",
                    "The analysis helps identify areas that may benefit from improved inter-community connections."
                ])
            ])
        ])
    ], className="p-3")