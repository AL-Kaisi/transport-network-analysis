"""
Dashboard for Transport Network Analysis.
Integrates community detection, critical nodes, and symbolic AI reasoning.
"""

import os
import base64
import io
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib
from dotenv import load_dotenv

# Import our project modules
from src.data_processing.gtfs_loader import EnhancedGTFSLoader as GTFSLoader
from src.graph_analysis.graph_builder import TransportGraphBuilder
from src.graph_analysis.community_detection import CommunityDetector
from src.symbolic_ai.knowledge_base import TransportKnowledgeBase

# Load environment variables
load_dotenv()

# Initialize the app
app = Dash(__name__)

# Initialize data containers
graph = None
partition = None
community_data = None
critical_nodes_data = None
symbolic_results = None

def load_data(sample_size=1000):
    """Load and process data."""
    global graph, partition, community_data, critical_nodes_data, symbolic_results
    
    # Get configuration from environment variables
    gtfs_url = os.getenv("GTFS_URL")
    data_dir = os.getenv("DATA_DIR")
    
    # Load GTFS data
    loader = GTFSLoader(gtfs_url, data_dir)
    
    # Check if data already exists, otherwise download it
    if not os.path.exists(os.path.join(data_dir, "stops.txt")):
        gtfs_data = loader.process()
    else:
        gtfs_data = loader.load_data()
    
    # Build graph
    builder = TransportGraphBuilder(gtfs_data)
    graph = builder.build_graph(sample_size=sample_size)
    
    # Detect communities
    detector = CommunityDetector(graph)
    partition = detector.detect_communities_louvain()
    
    # Analyze communities
    community_analysis = detector.analyze_communities()
    
    # Create community dataframe
    community_data = []
    for comm_id, data in community_analysis["communities"].items():
        community_data.append({
            "community_id": comm_id,
            "size": data["size"],
            "density": data["density"],
            "avg_degree": data["avg_degree"],
            "center_lat": data["center_lat"],
            "center_lon": data["center_lon"],
            "radius": data["radius"]
        })
    community_data = pd.DataFrame(community_data)
    
    # Identify critical nodes
    critical_nodes = detector.identify_critical_nodes(top_n=20)
    
    # Create critical nodes dataframe
    critical_nodes_data = []
    for node_id, score in critical_nodes:
        node_data = graph.nodes[node_id]
        critical_nodes_data.append({
            "node_id": node_id,
            "name": node_data.get("name", f"Stop_{node_id}"),
            "community": partition[node_id],
            "centrality": score,
            "latitude": node_data.get("lat"),
            "longitude": node_data.get("lon"),
            "degree": graph.degree[node_id]
        })
    critical_nodes_data = pd.DataFrame(critical_nodes_data)
    
    # Create symbolic knowledge base
    kb_creator = TransportKnowledgeBase(graph, partition)
    kb = kb_creator.create_knowledge_base(max_critical_nodes=50)
    
    # Perform symbolic reasoning
    symbolic_results = kb_creator.perform_symbolic_reasoning(critical_nodes)
    
    # Create images for later use
    create_visualizations()

def create_visualizations():
    """Create and save visualizations for use in the dashboard."""
    # Create directory for visualizations if it doesn't exist
    if not os.path.exists("visualizations"):
        os.makedirs("visualizations")
    
    # Create community visualization
    plt.figure(figsize=(15, 12))
    
    # Get positions for nodes
    pos = {}
    for node in graph.nodes():
        node_data = graph.nodes[node]
        if 'lat' in node_data and 'lon' in node_data:
            pos[node] = (node_data['lon'], node_data['lat'])
    
    # Colors for communities - using updated method
    communities = set(partition.values())
    # Fixed deprecation warning for get_cmap
    cmap = matplotlib.colormaps['tab20']
    
    # Draw nodes
    for com in communities:
        # List nodes in this community
        com_nodes = [node for node in graph.nodes() if partition[node] == com]
        nx.draw_networkx_nodes(
            graph, 
            pos, 
            nodelist=com_nodes,
            node_color=[cmap(com % 20)] * len(com_nodes),  # Limit to 20 colors and cycle
            node_size=30,
            alpha=0.8,
            label=f"Community {com}" if len(com_nodes) > 10 else "_nolegend_"  # Only show major communities
        )
    
    # Draw edges
    nx.draw_networkx_edges(graph, pos, alpha=0.1, width=0.5)
    
    plt.title("Greater Manchester Transport Network Communities")
    plt.axis('off')
    
    # Create a legend with fewer items
    largest_communities = sorted([(com, len([n for n in graph.nodes() if partition[n] == com])) 
                                 for com in communities], key=lambda x: x[1], reverse=True)[:10]
    handles, labels = plt.gca().get_legend_handles_labels()
    filtered_handles = []
    filtered_labels = []
    for com, _ in largest_communities:
        try:
            idx = labels.index(f"Community {com}")
            filtered_handles.append(handles[idx])
            filtered_labels.append(labels[idx])
        except ValueError:
            continue
    
    plt.legend(filtered_handles, filtered_labels, scatterpoints=1, frameon=False, labelspacing=1, loc='upper right')
    plt.tight_layout()
    plt.savefig("visualizations/communities.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    # Create critical nodes visualization
    plt.figure(figsize=(15, 12))
    
    # Draw regular nodes (small and transparent)
    for com in communities:
        com_nodes = [node for node in graph.nodes() if partition[node] == com]
        nx.draw_networkx_nodes(
            graph, 
            pos, 
            nodelist=com_nodes,
            node_color=[cmap(com % 20)] * len(com_nodes),  # Limit to 20 colors and cycle
            node_size=20,
            alpha=0.6
        )
    
    # Draw edges
    nx.draw_networkx_edges(graph, pos, alpha=0.1, width=0.5)
    
    # Draw critical nodes (larger and opaque)
    critical_ids = critical_nodes_data["node_id"].tolist()
    critical_colors = [cmap(partition[node_id] % 20) for node_id in critical_ids]  # Limit to 20 colors and cycle
    
    nx.draw_networkx_nodes(
        graph, 
        pos, 
        nodelist=critical_ids,
        node_color=critical_colors,
        node_size=150,
        edgecolors='black',
        linewidths=1.5,
        alpha=1.0
    )
    
    # Add labels for top critical nodes
    top_critical_ids = critical_ids[:10]
    critical_labels = {node_id: graph.nodes[node_id]['name'] for node_id in top_critical_ids}
    nx.draw_networkx_labels(
        graph, 
        pos, 
        labels=critical_labels,
        font_size=8,
        font_color='black',
        font_weight='bold',
        verticalalignment='bottom'
    )
    
    plt.title("Greater Manchester Transport Network Critical Nodes")
    plt.axis('off')
    plt.tight_layout()
    plt.savefig("visualizations/critical_nodes.png", dpi=300, bbox_inches='tight')
    plt.close()

def encode_image(image_file):
    """Encode image file to base64 for display in dashboard."""
    with open(image_file, "rb") as f:
        encoded = base64.b64encode(f.read())
    return f"data:image/png;base64,{encoded.decode()}"

# Define the layout of the app
def create_layout():
    if graph is None:
        return html.Div([
            html.H1("Transport Network Analysis Dashboard"),
            html.Button("Load Data", id="load-button"),
            html.Div(id="loading-message")
        ])
    
    return html.Div([
        html.H1("Greater Manchester Transport Network Analysis Dashboard"),
        
        # Network Overview Section
        html.Div([
            html.H2("Network Overview"),
            html.Div([
                html.Div([
                    html.H3("Graph Statistics"),
                    html.P(f"Nodes: {graph.number_of_nodes()}"),
                    html.P(f"Edges: {graph.number_of_edges()}"),
                    html.P(f"Density: {nx.density(graph):.6f}"),
                    html.P(f"Number of communities: {len(set(partition.values()))}"),
                    html.P(f"Modularity: {community_data['density'].mean():.4f}")
                ], style={'width': '30%', 'display': 'inline-block', 'vertical-align': 'top', 'padding': '10px'}),
                
                html.Div([
                    html.H3("Community Size Distribution"),
                    dcc.Graph(
                        id='community-size-histogram',
                        figure=px.histogram(
                            community_data, 
                            x="size", 
                            title="Distribution of Community Sizes",
                            labels={"size": "Number of Nodes", "count": "Frequency"},
                            nbins=20
                        )
                    )
                ], style={'width': '70%', 'display': 'inline-block', 'vertical-align': 'top'})
            ])
        ], style={'padding': '20px', 'border': '1px solid #ddd', 'margin-bottom': '20px'}),
        
        # Communities Section
        html.Div([
            html.H2("Communities"),
            html.Div([
                html.Div([
                    html.H3("Largest Communities"),
                    dcc.Graph(
                        id='largest-communities',
                        figure=px.bar(
                            community_data.nlargest(10, 'size'), 
                            x="community_id", 
                            y="size",
                            title="Top 10 Largest Communities",
                            labels={"community_id": "Community ID", "size": "Number of Nodes"}
                        )
                    )
                ], style={'width': '50%', 'display': 'inline-block', 'vertical-align': 'top'}),
                
                html.Div([
                    html.H3("Community Map"),
                    html.Img(src=encode_image("visualizations/communities.png"), style={'width': '100%'})
                ], style={'width': '50%', 'display': 'inline-block', 'vertical-align': 'top'})
            ])
        ], style={'padding': '20px', 'border': '1px solid #ddd', 'margin-bottom': '20px'}),
        
        # Critical Nodes Section
        html.Div([
            html.H2("Critical Nodes"),
            html.Div([
                html.Div([
                    html.H3("Top Critical Nodes"),
                    dcc.Graph(
                        id='critical-nodes-bar',
                        figure=px.bar(
                            critical_nodes_data.head(10), 
                            x="name", 
                            y="centrality",
                            title="Top 10 Critical Nodes by Betweenness Centrality",
                            labels={"name": "Node Name", "centrality": "Betweenness Centrality"}
                        ).update_layout(xaxis={'categoryorder':'total descending'})
                    )
                ], style={'width': '50%', 'display': 'inline-block', 'vertical-align': 'top'}),
                
                html.Div([
                    html.H3("Critical Nodes Map"),
                    html.Img(src=encode_image("visualizations/critical_nodes.png"), style={'width': '100%'})
                ], style={'width': '50%', 'display': 'inline-block', 'vertical-align': 'top'})
            ])
        ], style={'padding': '20px', 'border': '1px solid #ddd', 'margin-bottom': '20px'}),
        
        # Symbolic AI Insights
        html.Div([
            html.H2("Symbolic AI Insights"),
            
            html.Div([
                html.H3("Community Dependencies"),
                html.P("Communities with the most connections to other communities:"),
                html.Ul([
                    html.Li([
                        f"Community {comm_id}: Connected to {data['num_connections']} other communities"
                    ]) for comm_id, data in symbolic_results['community_dependencies'][:5]
                ])
            ], style={'padding': '10px', 'width': '50%', 'display': 'inline-block', 'vertical-align': 'top'}),
            
            html.Div([
                html.H3("Gateway Nodes"),
                html.P("Nodes that connect multiple communities:"),
                html.Ul([
                    html.Li([
                        f"{data['name']} (Community {data['community']}): Connects to {data['num_communities']} communities"
                    ]) for node_id, data in symbolic_results['gateway_nodes'][:5]
                ])
            ], style={'padding': '10px', 'width': '50%', 'display': 'inline-block', 'vertical-align': 'top'})
        ], style={'padding': '20px', 'border': '1px solid #ddd', 'margin-bottom': '20px'})
    ])

# Set the app layout - don't load data initially
app.layout = create_layout()

# We'll load data only when requested via button click

# Callback for loading data
@app.callback(
    Output("loading-message", "children"),
    Input("load-button", "n_clicks")
)
def load_data_callback(n_clicks):
    if n_clicks is None:
        return ""
    
    load_data()
    return "Data loaded successfully! Refresh the page to see the dashboard."

# Run the app with the updated method
if __name__ == '__main__':
    print("\n==================================================")
    print("Transport Network Analysis Dashboard")
    print("==================================================")
    print("\nDashboard is running on:")
    print("http://127.0.0.1:8070")
    print("http://localhost:8070")
    print("\nPress CTRL+C to stop the server")
    print("==================================================\n")
    app.run(debug=False, port=8070)  # Running on port 8070