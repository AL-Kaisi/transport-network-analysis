"""
Community analysis components for the dashboard.
"""

import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import base64
from typing import Dict, Any, List, Optional

def community_statistics_panel(community_analysis: Dict[int, Dict[str, Any]]) -> html.Div:
    """
    Create a panel with community statistics.
    
    Args:
        community_analysis: Dictionary with community analysis results
        
    Returns:
        Dash HTML component
    """
    # Create DataFrame for table
    data = []
    for comm_id, metrics in community_analysis.items():
        data.append({
            'Community ID': comm_id,
            'Size': metrics.get('size', 0),
            'Density': f"{metrics.get('density', 0):.4f}",
            'Avg. Degree': f"{metrics.get('avg_degree', 0):.2f}",
            'Largest CC Ratio': f"{metrics.get('largest_cc_ratio', 0):.2f}" if 'largest_cc_ratio' in metrics else 'N/A'
        })
    
    df = pd.DataFrame(data)
    df = df.sort_values('Size', ascending=False)
    
    return html.Div([
        html.H4("Community Statistics", className="mb-3"),
        
        dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[
                {'name': col, 'id': col} for col in df.columns
            ],
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_cell={
                'textAlign': 'left',
                'padding': '10px'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(248, 248, 248)'
                }
            ],
            page_size=10,
            sort_action='native',
            filter_action='native',
            style_table={'overflowX': 'auto'}
        )
    ])

def community_heatmap(community_data: pd.DataFrame) -> dcc.Graph:
    """
    Create a heatmap of community metrics.
    
    Args:
        community_data: DataFrame with community metrics
        
    Returns:
        Dash Graph component
    """
    # Select columns for heatmap
    cols = ['size', 'avg_degree', 'density']
    
    if 'accessibility_score' in community_data.columns:
        cols.append('accessibility_score')
    
    if 'external_connectivity' in community_data.columns:
        cols.append('external_connectivity')
    
    # Normalize data for better visualization
    df = community_data.copy()
    for col in cols:
        max_val = df[col].max()
        if max_val > 0:
            df[f"{col}_norm"] = df[col] / max_val
    
    # Sort by size
    df = df.sort_values('size', ascending=False).head(20)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=df[[f"{col}_norm" for col in cols]].values,
        x=cols,
        y=df['community_id'].astype(str),
        colorscale='Viridis',
        hoverongaps=False
    ))
    
    fig.update_layout(
        title="Community Metrics Heatmap",
        xaxis_title="Metric",
        yaxis_title="Community ID",
        yaxis_categoryorder='total ascending'
    )
    
    return dcc.Graph(figure=fig)

def community_map_panel(image_path: Optional[str] = None) -> html.Div:
    """
    Create a panel with the community map.
    
    Args:
        image_path: Path to the community visualization image
        
    Returns:
        Dash HTML component
    """
    content = []
    
    if image_path and os.path.exists(image_path):
        # Read image file
        with open(image_path, 'rb') as f:
            encoded_image = base64.b64encode(f.read()).decode('utf-8')
            
        content.append(html.Img(
            src=f"data:image/png;base64,{encoded_image}",
            style={'width': '100%', 'max-width': '1000px'}
        ))
    else:
        content.append(html.Div(
            "Community visualization not available",
            className="text-center p-5 bg-light"
        ))
    
    return html.Div([
        html.H4("Community Map", className="mb-3"),
        html.Div(content, className="text-center")
    ])

def community_accessibility_chart(accessibility_data: Dict[int, Dict[str, Any]]) -> dcc.Graph:
    """
    Create a chart showing community accessibility.
    
    Args:
        accessibility_data: Dictionary with community accessibility metrics
        
    Returns:
        Dash Graph component
    """
    # Create DataFrame
    data = []
    for comm_id, metrics in accessibility_data.items():
        data.append({
            'community_id': comm_id,
            'size': metrics.get('size', 0),
            'accessibility_score': metrics.get('accessibility_score', 0),
            'external_connectivity': metrics.get('external_connectivity', 0),
            'connected_communities': metrics.get('connected_communities', 0)
        })
    
    df = pd.DataFrame(data)
    
    # Sort by accessibility score
    df = df.sort_values('accessibility_score', ascending=False).head(20)
    
    # Create figure
    fig = px.scatter(
        df,
        x='external_connectivity',
        y='accessibility_score',
        size='size',
        color='connected_communities',
        hover_name='community_id',
        title="Community Accessibility Analysis",
        labels={
            'external_connectivity': 'External Connectivity',
            'accessibility_score': 'Accessibility Score',
            'size': 'Community Size',
            'connected_communities': 'Connected Communities'
        }
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=40, b=40),
        hovermode='closest'
    )
    
    return dcc.Graph(figure=fig)

def create_communities_tab(
    community_analysis: Dict[int, Dict[str, Any]],
    community_accessibility: Dict[int, Dict[str, Any]],
    image_path: Optional[str] = None
) -> html.Div:
    """
    Create the communities analysis tab.
    
    Args:
        community_analysis: Dictionary with community analysis results
        community_accessibility: Dictionary with community accessibility metrics
        image_path: Path to the community visualization image
        
    Returns:
        Dash HTML component
    """
    # Create DataFrames
    analysis_df = pd.DataFrame.from_dict(
        {k: v for k, v in community_analysis.items() if isinstance(v, dict)},
        orient='index'
    ).reset_index().rename(columns={'index': 'community_id'})
    
    accessibility_df = pd.DataFrame.from_dict(
        {k: v for k, v in community_accessibility.items() if isinstance(v, dict)},
        orient='index'
    ).reset_index().rename(columns={'index': 'community_id'})
    
    return html.Div([
        html.H2("Community Analysis", className="mb-4"),
        
        # Community map
        dbc.Row([
            dbc.Col([
                community_map_panel(image_path)
            ], width=12)
        ], className="mb-4"),
        
        # Community statistics
        dbc.Row([
            dbc.Col([
                community_statistics_panel(community_analysis)
            ], width=12)
        ], className="mb-4"),
        
        # Community metrics
        dbc.Row([
            dbc.Col([
                html.H4("Community Metrics Comparison", className="mb-3"),
                community_heatmap(analysis_df)
            ], width=12, lg=6),
            
            dbc.Col([
                html.H4("Community Accessibility", className="mb-3"),
                community_accessibility_chart(community_accessibility)
            ], width=12, lg=6)
        ])
    ])