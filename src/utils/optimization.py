"""
Optimization utilities for transport network analysis.
"""

import networkx as nx
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

def optimize_graph_for_memory(G: nx.Graph) -> nx.Graph:
    """
    Optimize a graph to reduce memory usage.
    
    Args:
        G: NetworkX graph to optimize
        
    Returns:
        Optimized graph
    """
    logger.info("Optimizing graph for memory usage")
    
    # Create a new graph
    G_opt = nx.Graph()
    
    # Copy only essential node attributes
    essential_node_attrs = ['name', 'lat', 'lon', 'type']
    
    for node, data in G.nodes(data=True):
        # Filter attributes
        essential_data = {k: v for k, v in data.items() if k in essential_node_attrs}
        G_opt.add_node(node, **essential_data)
    
    # Copy only essential edge attributes
    essential_edge_attrs = ['route_id', 'route_type', 'trips']
    
    for u, v, data in G.edges(data=True):
        # Filter attributes
        essential_data = {k: v for k, v in data.items() if k in essential_edge_attrs}
        G_opt.add_edge(u, v, **essential_data)
    
    logger.info(f"Original graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    logger.info(f"Optimized graph: {G_opt.number_of_nodes()} nodes, {G_opt.number_of_edges()} edges")
    
    return G_opt

def sample_graph_for_visualization(G: nx.Graph, max_nodes: int = 1000) -> nx.Graph:
    """
    Sample a subgraph for visualization if the graph is too large.
    
    Args:
        G: NetworkX graph to sample
        max_nodes: Maximum number of nodes in the sample
        
    Returns:
        Sampled graph
    """
    if G.number_of_nodes() <= max_nodes:
        return G
        
    logger.info(f"Sampling graph for visualization (max {max_nodes} nodes)")
    
    # Calculate node importance
    try:
        # Try betweenness centrality on a sample
        sample_nodes = np.random.choice(list(G.nodes()), min(5000, G.number_of_nodes()), replace=False)
        sample_graph = G.subgraph(sample_nodes)
        
        centrality = nx.betweenness_centrality(sample_graph, k=100)
    except Exception as e:
        logger.warning(f"Failed to calculate betweenness centrality: {e}")
        # Fall back to degree centrality
        centrality = nx.degree_centrality(G)
    
    # Get top nodes by centrality
    top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:max_nodes // 2]
    top_node_ids = [n for n, _ in top_nodes]
    
    # Add random nodes
    remaining_nodes = list(set(G.nodes()) - set(top_node_ids))
    if remaining_nodes:
        random_nodes = np.random.choice(
            remaining_nodes, 
            min(max_nodes - len(top_node_ids), len(remaining_nodes)), 
            replace=False
        )
    else:
        random_nodes = []
    
    # Create subgraph
    nodes_to_include = top_node_ids + random_nodes.tolist()
    subgraph = G.subgraph(nodes_to_include)
    
    logger.info(f"Sampled graph: {subgraph.number_of_nodes()} nodes, {subgraph.number_of_edges()} edges")
    
    return subgraph

def create_multilayer_network(G: nx.Graph, attribute: str = 'route_type') -> Dict[Any, nx.Graph]:
    """
    Create a multi-layer network based on an attribute.
    
    Args:
        G: Original NetworkX graph
        attribute: Node or edge attribute to split by
        
    Returns:
        Dictionary mapping attribute values to subgraphs
    """
    logger.info(f"Creating multi-layer network based on '{attribute}'")
    
    # Collect unique attribute values from edges
    attribute_values = set()
    for _, _, data in G.edges(data=True):
        if attribute in data:
            attribute_values.add(data[attribute])
    
    # Create a graph for each layer
    layers = {}
    for value in attribute_values:
        # Create a new graph
        layer_graph = nx.Graph()
        
        # Add all nodes
        for node, data in G.nodes(data=True):
            layer_graph.add_node(node, **data)
        
        # Add edges with matching attribute
        for u, v, data in G.edges(data=True):
            if attribute in data and data[attribute] == value:
                layer_graph.add_edge(u, v, **data)
        
        # Remove isolated nodes
        isolated_nodes = list(nx.isolates(layer_graph))
        layer_graph.remove_nodes_from(isolated_nodes)
        
        # Store the layer
        layers[value] = layer_graph
        
        logger.info(f"Layer {value}: {layer_graph.number_of_nodes()} nodes, {layer_graph.number_of_edges()} edges")
    
    return layers

def find_optimal_paths(G: nx.Graph, 
                     source_nodes: List[Any],
                     target_nodes: List[Any],
                     weight: Optional[str] = None) -> Dict[Tuple[Any, Any], List]:
    """
    Find optimal paths between sets of nodes.
    
    Args:
        G: NetworkX graph
        source_nodes: List of source nodes
        target_nodes: List of target nodes
        weight: Optional edge attribute to use as weight
        
    Returns:
        Dictionary mapping (source, target) pairs to paths
    """
    logger.info(f"Finding optimal paths between {len(source_nodes)} sources and {len(target_nodes)} targets")
    
    paths = {}
    
    # Limit the number of pairs for efficiency
    max_pairs = 1000
    current_pairs = 0
    
    for source in source_nodes:
        for target in target_nodes:
            if source != target and current_pairs < max_pairs:
                try:
                    if weight:
                        path = nx.shortest_path(G, source, target, weight=weight)
                    else:
                        path = nx.shortest_path(G, source, target)
                        
                    paths[(source, target)] = path
                    current_pairs += 1
                except nx.NetworkXNoPath:
                    # No path exists
                    pass
    
    logger.info(f"Found {len(paths)} paths")
    
    return paths