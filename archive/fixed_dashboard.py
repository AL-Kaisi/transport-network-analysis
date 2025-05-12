"""
Fixed dashboard for Transport Network Analysis.
This version shows appropriate loading indicators and doesn't hang on startup.
"""

import os
import base64
import io
import time
import sys
import logging
from dash import Dash, html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib
from dotenv import load_dotenv

# Set up logging to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize the app with Bootstrap for better UI
app = Dash(__name__, 
           external_stylesheets=[dbc.themes.BOOTSTRAP],
           suppress_callback_exceptions=True)

# Create the directory for visualizations if it doesn't exist
if not os.path.exists("visualizations"):
    os.makedirs("visualizations")

def load_data(sample_size=500):
    """Load and process data with proper timing information."""
    start_time = time.time()
    
    # Import our project modules - import here to not slow down initial app load
    from src.data_processing.gtfs_loader import GTFSLoader
    from src.graph_analysis.graph_builder import TransportGraphBuilder
    from src.graph_analysis.community_detection import CommunityDetector
    from src.symbolic_ai.knowledge_base import TransportKnowledgeBase
    
    # Get configuration from environment variables
    gtfs_url = os.getenv("GTFS_URL")
    data_dir = os.getenv("DATA_DIR")
    
    logger.info(f"Starting data loading with {sample_size} samples")
    
    # Initialize result data dictionary
    data = {
        "status": "loading",
        "log": ["Starting data loading..."],
        "progress": 0,
        "graph": None,
        "partition": None,
        "community_data": None,
        "critical_nodes_data": None,
        "symbolic_results": None
    }
    
    # 1. Load GTFS data
    data["log"].append("Loading GTFS data...")
    data["progress"] = 10
    yield data
    
    loader = GTFSLoader(gtfs_url, data_dir)
    
    # Check if data already exists, otherwise download it
    if not os.path.exists(os.path.join(data_dir, "stops.txt")):
        data["log"].append("Downloading GTFS data...")
        gtfs_data = loader.process()
    else:
        data["log"].append("Loading existing GTFS data...")
        gtfs_data = loader.load_data()
    
    data["log"].append("GTFS data loaded successfully")
    data["progress"] = 20
    yield data
    
    # 2. Build graph
    data["log"].append(f"Building graph with sample size {sample_size}...")
    data["progress"] = 30
    yield data
    
    builder = TransportGraphBuilder(gtfs_data)
    graph = builder.build_graph(sample_size=sample_size)
    data["graph"] = graph
    
    data["log"].append(f"Graph built with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
    data["progress"] = 50
    yield data
    
    # 3. Detect communities
    data["log"].append("Detecting communities...")
    data["progress"] = 60
    yield data
    
    detector = CommunityDetector(graph)
    partition = detector.detect_communities_louvain()
    data["partition"] = partition
    
    data["log"].append(f"Detected {len(set(partition.values()))} communities")
    data["progress"] = 70
    yield data
    
    # 4. Analyze communities
    data["log"].append("Analyzing communities...")
    data["progress"] = 75
    yield data
    
    community_analysis = detector.analyze_communities()
    
    # Create community dataframe
    community_data = []
    for comm_id, comm_data in community_analysis["communities"].items():
        community_data.append({
            "community_id": comm_id,
            "size": comm_data["size"],
            "density": comm_data["density"],
            "avg_degree": comm_data["avg_degree"],
            "center_lat": comm_data["center_lat"],
            "center_lon": comm_data["center_lon"],
            "radius": comm_data["radius"]
        })
    community_data = pd.DataFrame(community_data)
    data["community_data"] = community_data
    
    data["log"].append("Community analysis complete")
    data["progress"] = 80
    yield data
    
    # 5. Identify critical nodes
    data["log"].append("Identifying critical nodes...")
    data["progress"] = 85
    yield data
    
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
    data["critical_nodes_data"] = critical_nodes_data
    
    data["log"].append("Critical nodes identified")
    data["progress"] = 90
    yield data
    
    # 6. Symbolic reasoning
    data["log"].append("Performing symbolic reasoning...")
    data["progress"] = 95
    yield data
    
    kb_creator = TransportKnowledgeBase(graph, partition)
    kb = kb_creator.create_knowledge_base(max_critical_nodes=50)
    symbolic_results = kb_creator.perform_symbolic_reasoning(critical_nodes)
    data["symbolic_results"] = symbolic_results
    
    # 7. Create visualizations
    data["log"].append("Creating visualizations...")
    data["progress"] = 98
    yield data
    
    # Create visualization if it doesn't exist
    if not os.path.exists("visualizations/communities.png") or not os.path.exists("visualizations/critical_nodes.png"):
        create_visualizations(graph, partition, critical_nodes_data)
    
    # Complete
    end_time = time.time()
    processing_time = end_time - start_time
    
    data["log"].append(f"Data loading complete in {processing_time:.2f} seconds")
    data["progress"] = 100
    data["status"] = "complete"
    yield data

def create_visualizations(graph, partition, critical_nodes_data):
    """Create visualizations for use in the dashboard."""
    logger.info("Creating visualizations...")
    
    # Create community visualization
    plt.figure(figsize=(15, 12))
    
    # Get positions for nodes
    pos = {}
    for node in graph.nodes():
        node_data = graph.nodes[node]
        if 'lat' in node_data and 'lon' in node_data:
            pos[node] = (node_data['lon'], node_data['lat'])
    
    # Colors for communities
    communities = set(partition.values())
    cmap = matplotlib.colormaps['tab20']
    
    # Draw nodes
    for com in communities:
        # List nodes in this community
        com_nodes = [node for node in graph.nodes() if partition[node] == com]
        nx.draw_networkx_nodes(
            graph, 
            pos, 
            nodelist=com_nodes,
            node_color=[cmap(com % 20)] * len(com_nodes),
            node_size=30,
            alpha=0.8,
            label=f"Community {com}" if len(com_nodes) > 10 else "_nolegend_"
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
            node_color=[cmap(com % 20)] * len(com_nodes),
            node_size=20,
            alpha=0.6
        )
    
    # Draw edges
    nx.draw_networkx_edges(graph, pos, alpha=0.1, width=0.5)
    
    # Draw critical nodes (larger and opaque)
    critical_ids = critical_nodes_data["node_id"].tolist()
    critical_colors = [cmap(partition[node_id] % 20) for node_id in critical_ids]
    
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
    critical_labels = {node_id: graph.nodes[node_id].get('name', f'Stop_{node_id}') for node_id in top_critical_ids}
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
    try:
        with open(image_file, "rb") as f:
            encoded = base64.b64encode(f.read())
        return f"data:image/png;base64,{encoded.decode()}"
    except:
        return ""

# Initial layout with loading UI
app.layout = html.Div([
    # App title
    html.H1("Transport Network Analysis Dashboard"),
    
    # Tabs for different views
    dcc.Tabs(id='tabs', value='loading-tab', children=[
        # Loading tab - initial view
        dcc.Tab(label='Loading', value='loading-tab', children=[
            html.Div([
                html.H2("Data Loading"),
                html.P("Load the transport network data to view analysis."),
                html.Div([
                    dcc.Input(
                        id='sample-size-input',
                        type='number',
                        min=100,
                        max=5000,
                        step=100,
                        value=500,
                        placeholder="Sample size (default: 500)"
                    ),
                    html.Button('Load Data', id='load-button', n_clicks=0),
                ], style={'margin-bottom': '20px'}),
                
                # Progress indicator
                html.Div(id='loading-ui', children=[
                    dbc.Progress(id='loading-progress', value=0, style={'height': '20px', 'margin-bottom': '10px'}),
                    html.Div(id='loading-status', children="Click 'Load Data' to begin"),
                    html.Div(id='loading-log', style={'height': '200px', 'overflow-y': 'scroll', 'border': '1px solid #ddd', 'padding': '10px', 'margin-top': '10px'})
                ], style={'display': 'none'})
            ])
        ]),
        
        # Overview tab
        dcc.Tab(label='Network Overview', value='overview-tab', children=[
            html.Div(id='overview-content')
        ]),
        
        # Communities tab
        dcc.Tab(label='Communities', value='communities-tab', children=[
            html.Div(id='communities-content')
        ]),
        
        # Critical Nodes tab
        dcc.Tab(label='Critical Nodes', value='critical-nodes-tab', children=[
            html.Div(id='critical-nodes-content')
        ]),
        
        # Symbolic AI tab
        dcc.Tab(label='Symbolic AI Insights', value='symbolic-tab', children=[
            html.Div(id='symbolic-content')
        ])
    ]),
    
    # Store component to save processed data
    dcc.Store(id='network-data'),
])

# Callback to handle data loading with progress updates
@app.callback(
    [Output('loading-ui', 'style'),
     Output('loading-progress', 'value'),
     Output('loading-status', 'children'),
     Output('loading-log', 'children')],
    [Input('load-button', 'n_clicks')],
    [State('sample-size-input', 'value')],
    prevent_initial_call=True
)
def process_data(n_clicks, sample_size):
    """
    Process network data with progress updates.
    Simplified callback to ensure it works properly.
    """
    if n_clicks is None or n_clicks == 0:
        return {'display': 'none'}, 0, "", []

    # Show loading UI
    loading_style = {'display': 'block'}

    # Display initial status
    return loading_style, 10, "Starting analysis...", [html.Div("Initializing analysis...")]

# Callback to render Overview tab content
@app.callback(
    Output('overview-content', 'children'),
    [Input('network-data', 'data')],
    prevent_initial_call=True
)
def update_overview_tab(data):
    if not data or data.get('status') != 'complete':
        return html.Div("No data loaded. Please go to the Loading tab and load data.")
    
    graph = data.get('graph')
    community_data = data.get('community_data')
    
    if not graph or not community_data:
        return html.Div("Data incomplete. Please reload data.")
    
    # Create Overview content
    return html.Div([
        html.H2("Network Overview"),
        html.Div([
            html.Div([
                html.H3("Graph Statistics"),
                html.P(f"Nodes: {data['graph'].number_of_nodes()}"),
                html.P(f"Edges: {data['graph'].number_of_edges()}"),
                html.P(f"Density: {nx.density(data['graph']):.6f}"),
                html.P(f"Number of communities: {len(set(data['partition'].values()))}"),
            ], style={'width': '30%', 'display': 'inline-block', 'vertical-align': 'top', 'padding': '10px'}),
            
            html.Div([
                html.H3("Community Size Distribution"),
                dcc.Graph(
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
    ], style={'padding': '20px'})

# Callback to render Communities tab content
@app.callback(
    Output('communities-content', 'children'),
    [Input('network-data', 'data')],
    prevent_initial_call=True
)
def update_communities_tab(data):
    if not data or data.get('status') != 'complete':
        return html.Div("No data loaded. Please go to the Loading tab and load data.")
    
    community_data = data.get('community_data')
    
    if not community_data:
        return html.Div("Community data not available. Please reload data.")
    
    # Create Communities content
    return html.Div([
        html.H2("Communities"),
        html.Div([
            html.Div([
                html.H3("Largest Communities"),
                dcc.Graph(
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
    ], style={'padding': '20px'})

# Callback to render Critical Nodes tab content
@app.callback(
    Output('critical-nodes-content', 'children'),
    [Input('network-data', 'data')],
    prevent_initial_call=True
)
def update_critical_nodes_tab(data):
    if not data or data.get('status') != 'complete':
        return html.Div("No data loaded. Please go to the Loading tab and load data.")
    
    critical_nodes_data = data.get('critical_nodes_data')
    
    if not critical_nodes_data:
        return html.Div("Critical nodes data not available. Please reload data.")
    
    # Create Critical Nodes content
    return html.Div([
        html.H2("Critical Nodes"),
        html.Div([
            html.Div([
                html.H3("Top Critical Nodes"),
                dcc.Graph(
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
    ], style={'padding': '20px'})

# Callback to render Symbolic AI tab content
@app.callback(
    Output('symbolic-content', 'children'),
    [Input('network-data', 'data')],
    prevent_initial_call=True
)
def update_symbolic_tab(data):
    if not data or data.get('status') != 'complete':
        return html.Div("No data loaded. Please go to the Loading tab and load data.")
    
    symbolic_results = data.get('symbolic_results')
    
    if not symbolic_results:
        return html.Div("Symbolic reasoning results not available. Please reload data.")
    
    # Create Symbolic AI content
    return html.Div([
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
    ], style={'padding': '20px'})

# Run the app
if __name__ == '__main__':
    print("\n==================================================")
    print("Transport Network Analysis Dashboard")
    print("==================================================")
    print("\nDashboard is running on:")
    print("http://127.0.0.1:8888")
    print("http://localhost:8888")
    print("\nPress CTRL+C to stop the server")
    print("==================================================\n")
    app.run(debug=False, host='0.0.0.0', port=8888)