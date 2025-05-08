"""
Advanced critical node analysis for transport networks with optimized performance.
"""
import networkx as nx
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Set
import logging
from concurrent.futures import ProcessPoolExecutor
import functools

logger = logging.getLogger(__name__)

# Define worker function at the module level so it can be pickled
def _vulnerability_worker(args):
    """Process a single node for vulnerability assessment - module level function for multiprocessing."""
    node_id, score, G, partition, baseline_metrics = args
    
    # Use graph view instead of a full copy - much more efficient
    G_view = nx.restricted_view(G, [node_id], [])
    
    # Calculate metrics after removal - using faster approximations
    modified_metrics = _calculate_network_metrics_fast(G_view)
    
    # Calculate impact percentages
    impact = {}
    for metric in baseline_metrics:
        if baseline_metrics[metric] == 0:
            impact[f"{metric}_impact"] = 0
        else:
            impact[f"{metric}_impact"] = 100 * (1 - (modified_metrics[metric] / baseline_metrics[metric]))
    
    # Calculate community connectivity impact if partition is available
    community_impact = {}
    if partition:
        community_impact = _assess_community_impact_fast(G, node_id, partition)
    
    # Combine results
    return {
        'node_id': node_id,
        'name': G.nodes[node_id].get('name', str(node_id)),
        'centrality': score,
        **impact,
        **community_impact
    }

def _calculate_network_metrics_fast(G: nx.Graph) -> Dict[str, float]:
    """
    Calculate key network metrics for a graph - optimized version.
    
    Uses approximation for expensive metrics.
    """
    metrics = {
        'nodes': G.number_of_nodes(),
        'edges': G.number_of_edges(),
        'density': nx.density(G)
    }
    
    # Find largest connected component
    connected_components = list(nx.connected_components(G))
    if connected_components:
        largest_cc = max(connected_components, key=len)
        largest_G = G.subgraph(largest_cc)
        
        metrics['largest_cc_size'] = len(largest_cc)
        metrics['largest_cc_ratio'] = len(largest_cc) / G.number_of_nodes()
        
        # Calculate additional metrics on largest component
        # Use sampling approach for path length if graph is large
        if len(largest_cc) > 1000:
            # Sample nodes for path length estimation
            sampled_nodes = np.random.choice(list(largest_cc), 
                                           size=min(100, len(largest_cc)),
                                           replace=False)
            path_lengths = []
            for source in sampled_nodes:
                lengths = nx.single_source_shortest_path_length(largest_G, source)
                path_lengths.extend(lengths.values())
            
            if path_lengths:
                metrics['avg_path_length'] = sum(path_lengths) / len(path_lengths)
            else:
                metrics['avg_path_length'] = 0
        else:
            try:
                metrics['avg_path_length'] = nx.average_shortest_path_length(largest_G)
            except:
                metrics['avg_path_length'] = 0
        
        # Use approximation for clustering coefficient
        metrics['avg_clustering'] = nx.approximation.average_clustering(largest_G, trials=1000)
    else:
        # Set default values if no connected components
        metrics['largest_cc_size'] = 0
        metrics['largest_cc_ratio'] = 0
        metrics['avg_path_length'] = 0
        metrics['avg_clustering'] = 0
    
    return metrics

def _assess_community_impact_fast(G: nx.Graph, node_id: Any, partition: Dict) -> Dict[str, Any]:
    """
    Assess impact of removing a node on community connectivity - optimized version.
    """
    if not partition:
        return {}
        
    # Get node's community
    node_community = partition.get(node_id)
    
    # Get communities connected through this node
    neighbor_communities = set()
    for neighbor in G.neighbors(node_id):
        neigh_community = partition.get(neighbor)
        if neigh_community != node_community:
            neighbor_communities.add(neigh_community)
    
    # Initialize tracking of disconnected communities
    disconnected_communities = set()
    
    # Get all nodes in node's community
    community_nodes = [n for n, comm in partition.items() 
                     if comm == node_community and n != node_id]
    
    # For each community that was connected through this node,
    # check if it's still connected to the node's community
    for comm in neighbor_communities:
        # Get all nodes in this community
        comm_nodes = [n for n, c in partition.items() if c == comm]
        
        # Check if any edges remain between node's community and this community
        is_connected = False
        for source in community_nodes:
            for target in comm_nodes:
                if G.has_edge(source, target):
                    is_connected = True
                    break
            if is_connected:
                break
        
        if not is_connected:
            disconnected_communities.add(comm)
    
    # Calculate impact metrics
    return {
        'connected_communities': len(neighbor_communities),
        'disconnected_communities': len(disconnected_communities),
        'community_impact_score': len(disconnected_communities) / max(1, len(neighbor_communities))
    }

class CriticalNodeAnalyzer:
    """Class for advanced analysis of critical nodes in transport networks."""
    
    def __init__(self, graph: nx.Graph, partition: Dict = None):
        """
        Initialize the critical node analyzer.
        
        Args:
            graph: NetworkX graph representing the transport network
            partition: Optional dictionary mapping node IDs to community IDs
        """
        self.graph = graph
        self.partition = partition
        
    def identify_critical_nodes(self, method: str = 'betweenness', top_n: int = 20, 
                               sample_size: int = None) -> List[Tuple[Any, float]]:
        """
        Identify critical nodes using various centrality measures.
        
        Args:
            method: Centrality method ('betweenness', 'degree', 'closeness', 'eigenvector', 'katz')
            top_n: Number of critical nodes to return
            sample_size: Optional sample size for approximate betweenness calculation
            
        Returns:
            List of tuples (node_id, centrality_score)
        """
        logger.info(f"Identifying critical nodes using {method} centrality")
        
        # Calculate centrality based on selected method
        if method == 'betweenness':
            if sample_size or self.graph.number_of_nodes() > 1000:
                logger.info(f"Using approximate betweenness centrality with k={sample_size or 500}")
                centrality = nx.betweenness_centrality(
                    self.graph, 
                    k=sample_size or min(500, self.graph.number_of_nodes()),
                    normalized=True
                )
            else:
                centrality = nx.betweenness_centrality(self.graph, normalized=True)
        elif method == 'degree':
            centrality = nx.degree_centrality(self.graph)
        elif method == 'closeness':
            centrality = nx.closeness_centrality(self.graph)
        elif method == 'eigenvector':
            centrality = nx.eigenvector_centrality_numpy(self.graph)
        elif method == 'katz':
            centrality = nx.katz_centrality_numpy(self.graph)
        else:
            logger.error(f"Unknown centrality method: {method}")
            raise ValueError(f"Unknown centrality method: {method}")
        
        # Sort nodes by centrality score
        critical_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        return critical_nodes
    
    def analyze_critical_nodes(self, critical_nodes: List[Tuple[Any, float]]) -> pd.DataFrame:
        """
        Analyze the properties of identified critical nodes.
        
        Args:
            critical_nodes: List of tuples (node_id, centrality_score)
            
        Returns:
            DataFrame with critical node analysis
        """
        logger.info(f"Analyzing {len(critical_nodes)} critical nodes")
        
        # Create DataFrame for analysis
        node_data = []
        for node_id, score in critical_nodes:
            # Get node data
            node_info = self.graph.nodes[node_id]
            
            # Basic data
            node_row = {
                'node_id': node_id,
                'name': node_info.get('name', str(node_id)),
                'centrality': score,
                'degree': self.graph.degree[node_id],
                'lat': node_info.get('lat'),
                'lon': node_info.get('lon')
            }
            
            # Add community if partition is available
            if self.partition:
                node_row['community'] = self.partition.get(node_id)
            
            # Calculate local clustering coefficient
            node_row['clustering'] = nx.clustering(self.graph, node_id)
            
            # Get neighbor communities if partition is available
            if self.partition:
                node_community = self.partition.get(node_id)
                neighbor_communities = set()
                
                for neighbor in self.graph.neighbors(node_id):
                    neigh_community = self.partition.get(neighbor)
                    if neigh_community != node_community:
                        neighbor_communities.add(neigh_community)
                
                node_row['connected_communities'] = len(neighbor_communities)
                node_row['connector_score'] = score * len(neighbor_communities)
            
            node_data.append(node_row)
        
        # Create DataFrame
        df = pd.DataFrame(node_data)
        
        # Add normalized connector score if available
        if 'connector_score' in df.columns:
            max_score = df['connector_score'].max()
            if max_score > 0:
                df['connector_score_norm'] = df['connector_score'] / max_score
        
        return df
    
    def assess_vulnerability(self, critical_nodes: List[Tuple[Any, float]], 
                             parallel: bool = True, max_workers: int = 4) -> List[Dict]:
        """
        Assess network vulnerability by simulating removal of critical nodes.
        
        Args:
            critical_nodes: List of tuples (node_id, centrality_score)
            parallel: Whether to use parallel processing
            max_workers: Number of parallel workers to use
            
        Returns:
            List of dictionaries with vulnerability assessment
        """
        logger.info("Assessing network vulnerability")
        
        # Calculate baseline metrics once
        baseline_metrics = _calculate_network_metrics_fast(self.graph)
        logger.info(f"Baseline network metrics: {baseline_metrics}")
        
        # Use parallel or sequential processing based on parameter
        if parallel and len(critical_nodes) > 1:
            return self._assess_vulnerability_parallel(critical_nodes, baseline_metrics, max_workers)
        else:
            return self._assess_vulnerability_sequential(critical_nodes, baseline_metrics)
    
    def _assess_vulnerability_parallel(self, critical_nodes, baseline_metrics, max_workers):
        """Parallel implementation of vulnerability assessment."""
        # Prepare arguments for the worker function
        worker_args = []
        for node_id, score in critical_nodes:
            worker_args.append((node_id, score, self.graph, self.partition, baseline_metrics))
        
        # Use a ProcessPoolExecutor to parallelize
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(_vulnerability_worker, worker_args))
        
        return results
    
    def _assess_vulnerability_sequential(self, critical_nodes, baseline_metrics):
        """Sequential implementation of vulnerability assessment."""
        vulnerability_results = []
        
        for node_id, score in critical_nodes:
            # Create a copy of the graph and remove the node
            G_view = nx.restricted_view(self.graph, [node_id], [])
            
            # Calculate metrics after removal
            modified_metrics = _calculate_network_metrics_fast(G_view)
            
            # Calculate impact percentages
            impact = {}
            for metric in baseline_metrics:
                if baseline_metrics[metric] == 0:
                    impact[f"{metric}_impact"] = 0
                else:
                    impact[f"{metric}_impact"] = 100 * (1 - (modified_metrics[metric] / baseline_metrics[metric]))
            
            # Calculate community connectivity impact if partition is available
            community_impact = {}
            if self.partition:
                community_impact = _assess_community_impact_fast(self.graph, node_id, self.partition)
            
            # Combine results
            vulnerability_results.append({
                'node_id': node_id,
                'name': self.graph.nodes[node_id].get('name', str(node_id)),
                'centrality': score,
                **impact,
                **community_impact
            })
            
        return vulnerability_results