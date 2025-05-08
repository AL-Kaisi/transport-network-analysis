"""
Script to identify and analyze critical nodes in the transport network.
"""

import os
import time
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from dotenv import load_dotenv
from src.data_processing.gtfs_loader import GTFSLoader
from src.graph_analysis.graph_builder import TransportGraphBuilder
from src.graph_analysis.community_detection import CommunityDetector

# Load environment variables
load_dotenv()

def main():
    # Get configuration from environment variables
    gtfs_url = os.getenv("GTFS_URL")
    data_dir = os.getenv("DATA_DIR")
    
    # Load GTFS data
    loader = GTFSLoader(gtfs_url, data_dir)
    
    # Check if data already exists, otherwise download it
    if not os.path.exists(os.path.join(data_dir, "stops.txt")):
        print("Downloading GTFS data...")
        gtfs_data = loader.process()
    else:
        print("Loading existing GTFS data...")
        gtfs_data = loader.load_data()
    
    # Build graph from a sample of trips
    print("\nBuilding transport network graph...")
    builder = TransportGraphBuilder(gtfs_data)
    G = builder.build_graph(sample_size=1000)  # Sample for faster testing
    
    # Detect communities
    print("\nDetecting communities...")
    detector = CommunityDetector(G)
    partition = detector.detect_communities_louvain()
    
    # Identify critical nodes
    print("\nIdentifying critical nodes...")
    critical_nodes = detector.identify_critical_nodes(top_n=20)
    
    # Create a DataFrame for better visualization
    critical_data = []
    for node_id, score in critical_nodes:
        node_data = G.nodes[node_id]
        community_id = partition[node_id]
        critical_data.append({
            'node_id': node_id,
            'name': node_data.get('name', 'Unknown'),
            'community': community_id,
            'centrality': score,
            'latitude': node_data.get('lat', 0),
            'longitude': node_data.get('lon', 0),
            'degree': G.degree[node_id]
        })
    
    critical_df = pd.DataFrame(critical_data)
    print("\nTop 20 Critical Nodes:")
    print(critical_df[['name', 'community', 'centrality', 'degree']])
    
    # Analyze inter-community connections through critical nodes
    print("\nAnalyzing inter-community connections...")
    
    # For each critical node, find which communities it connects
    for i, row in critical_df.iterrows():
        node_id = row['node_id']
        node_community = row['community']
        neighbors = list(G.neighbors(node_id))
        neighbor_communities = [partition[neigh] for neigh in neighbors]
        unique_neighbor_communities = set(neighbor_communities)
        
        # Only count distinct communities other than the node's own community
        connected_communities = unique_neighbor_communities - {node_community}
        
        print(f"\n{row['name']} (Community {node_community}):")
        print(f"  Connects to {len(connected_communities)} other communities: {sorted(connected_communities)}")
        
        # Count connections to each community
        community_connections = {}
        for neigh, comm in zip(neighbors, neighbor_communities):
            if comm != node_community:
                community_connections[comm] = community_connections.get(comm, 0) + 1
        
        # Print top connections
        if community_connections:
            top_connections = sorted(community_connections.items(), key=lambda x: x[1], reverse=True)[:3]
            print("  Strongest connections:")
            for comm, count in top_connections:
                print(f"    Community {comm}: {count} connections")
    
    # Visualize critical nodes on the network
    print("\nVisualizing critical nodes on the network...")
    
    plt.figure(figsize=(15, 12))
    
    # Get positions for nodes
    pos = {}
    for node in G.nodes():
        node_data = G.nodes[node]
        if 'lat' in node_data and 'lon' in node_data:
            pos[node] = (node_data['lon'], node_data['lat'])
    
    # If we don't have positions for all nodes, use spring layout
    if len(pos) < len(G.nodes()):
        print("Using spring layout for node positioning")
        pos = nx.spring_layout(G, seed=42)
    
    # Colors for communities
    communities = set(partition.values())
    cmap = plt.cm.get_cmap('tab20', max(communities) + 1)
    
    # Draw regular nodes (small and transparent)
    for com in communities:
        com_nodes = [node for node in G.nodes() if partition[node] == com]
        nx.draw_networkx_nodes(
            G, 
            pos, 
            nodelist=com_nodes,
            node_color=[cmap(com)] * len(com_nodes),
            node_size=20,
            alpha=0.6
        )
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, alpha=0.1, width=0.5)
    
    # Draw critical nodes (larger and opaque)
    critical_node_ids = [row['node_id'] for _, row in critical_df.iterrows()]
    critical_node_colors = [cmap(partition[node_id]) for node_id in critical_node_ids]
    
    nx.draw_networkx_nodes(
        G, 
        pos, 
        nodelist=critical_node_ids,
        node_color=critical_node_colors,
        node_size=150,
        edgecolors='black',
        linewidths=1.5,
        alpha=1.0
    )
    
    # Add labels for critical nodes
    critical_labels = {node_id: G.nodes[node_id]['name'] for node_id in critical_node_ids}
    nx.draw_networkx_labels(
        G, 
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
    plt.savefig("transport_critical_nodes.png", dpi=300, bbox_inches='tight')
    print("Visualization saved to transport_critical_nodes.png")
    
    # Create a "gateway" score for each critical node based on its role connecting communities
    critical_df['connected_communities'] = 0
    critical_df['gateway_score'] = 0
    
    for i, row in critical_df.iterrows():
        node_id = row['node_id']
        node_community = row['community']
        neighbors = list(G.neighbors(node_id))
        neighbor_communities = [partition[neigh] for neigh in neighbors]
        connected_communities = len(set(neighbor_communities) - {node_community})
        
        # Gateway score: betweenness centrality × number of communities connected
        gateway_score = row['centrality'] * connected_communities
        
        critical_df.at[i, 'connected_communities'] = connected_communities
        critical_df.at[i, 'gateway_score'] = gateway_score
    
    # Print the nodes with highest gateway scores
    print("\nTop Gateway Nodes (crucial for inter-community connections):")
    gateway_df = critical_df.sort_values('gateway_score', ascending=False).head(10)
    print(gateway_df[['name', 'community', 'centrality', 'connected_communities', 'gateway_score']])
    
if __name__ == "__main__":
    main()