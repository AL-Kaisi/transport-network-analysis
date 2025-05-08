"""
Transport efficiency analysis for transport networks.
"""

import networkx as nx
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class TransportEfficiencyAnalyzer:
    """Class for analyzing transport efficiency metrics."""
    
    def __init__(self, graph: nx.Graph, partition: Optional[Dict[Any, int]] = None):
        """
        Initialize the transport efficiency analyzer.
        
        Args:
            graph: NetworkX graph representing the transport network
            partition: Optional dictionary mapping node IDs to community IDs
        """
        self.graph = graph
        self.partition = partition
        
    def calculate_efficiency_metrics(self) -> Dict[str, Any]:
        """
        Calculate various transport efficiency metrics.
        
        Returns:
            Dictionary with efficiency metrics
        """
        logger.info("Calculating transport efficiency metrics")
        
        metrics = {}
        
        # Calculate global efficiency
        try:
            metrics['global_efficiency'] = nx.global_efficiency(self.graph)
        except:
            metrics['global_efficiency'] = None
            logger.warning("Failed to calculate global efficiency")
        
        # Calculate average shortest path length
        if nx.is_connected(self.graph):
            metrics['avg_path_length'] = nx.average_shortest_path_length(self.graph)
        else:
            # Calculate for largest connected component
            largest_cc = max(nx.connected_components(self.graph), key=len)
            largest_G = self.graph.subgraph(largest_cc)
            metrics['avg_path_length'] = nx.average_shortest_path_length(largest_G)
            metrics['largest_cc_ratio'] = len(largest_cc) / self.graph.number_of_nodes()
        
        # Calculate diameter
        if nx.is_connected(self.graph):
            metrics['diameter'] = nx.diameter(self.graph)
        else:
            # Calculate for largest connected component
            largest_cc = max(nx.connected_components(self.graph), key=len)
            largest_G = self.graph.subgraph(largest_cc)
            metrics['diameter'] = nx.diameter(largest_G)
        
        # Calculate average degree
        degrees = dict(self.graph.degree())
        metrics['avg_degree'] = sum(degrees.values()) / len(degrees)
        metrics['max_degree'] = max(degrees.values())
        metrics['min_degree'] = min(degrees.values())
        
        # Calculate clustering coefficient (local connectivity)
        metrics['avg_clustering'] = nx.average_clustering(self.graph)
        
        # Calculate network density
        metrics['density'] = nx.density(self.graph)
        
        # Calculate transfer metrics if partition is available
        if self.partition:
            transfer_metrics = self._calculate_transfer_metrics()
            metrics.update(transfer_metrics)
        
        return metrics
    
    def _calculate_transfer_metrics(self) -> Dict[str, Any]:
        """Calculate metrics related to transfers between communities."""
        logger.info("Calculating transfer metrics")
        
        metrics = {}
        
        # Calculate intra-community vs inter-community edges
        intra_edges = 0
        inter_edges = 0
        
        for source, target in self.graph.edges():
            source_comm = self.partition.get(source)
            target_comm = self.partition.get(target)
            
            if source_comm == target_comm:
                intra_edges += 1
            else:
                inter_edges += 1
        
        total_edges = intra_edges + inter_edges
        if total_edges > 0:
            metrics['intra_edge_ratio'] = intra_edges / total_edges
            metrics['inter_edge_ratio'] = inter_edges / total_edges
        else:
            metrics['intra_edge_ratio'] = 0
            metrics['inter_edge_ratio'] = 0
        
        # Calculate average transfers required between communities
        community_transfers = {}
        communities = set(self.partition.values())
        
        # Limit analysis to a subset of community pairs for efficiency
        comm_pairs = []
        for comm1 in communities:
            for comm2 in communities:
                if comm1 < comm2:
                    comm_pairs.append((comm1, comm2))
        
        # Sample pairs if there are too many
        if len(comm_pairs) > 50:
            import random
            random.shuffle(comm_pairs)
            comm_pairs = comm_pairs[:50]
        
        for comm1, comm2 in comm_pairs:
            # Get nodes in each community
            comm1_nodes = [n for n, c in self.partition.items() if c == comm1]
            comm2_nodes = [n for n, c in self.partition.items() if c == comm2]
            
            # Sample nodes for efficiency
            if len(comm1_nodes) > 5 or len(comm2_nodes) > 5:
                comm1_nodes = np.random.choice(comm1_nodes, min(5, len(comm1_nodes)), replace=False)
                comm2_nodes = np.random.choice(comm2_nodes, min(5, len(comm2_nodes)), replace=False)
            
            # Calculate paths
            path_lengths = []
            for n1 in comm1_nodes:
                for n2 in comm2_nodes:
                    try:
                        path = nx.shortest_path(self.graph, n1, n2)
                        path_lengths.append(len(path) - 1)  # Convert to number of edges
                    except nx.NetworkXNoPath:
                        # No path exists
                        pass
            
            if path_lengths:
                avg_path = np.mean(path_lengths)
                community_transfers[(comm1, comm2)] = avg_path
        
        if community_transfers:
            metrics['avg_community_transfers'] = np.mean(list(community_transfers.values()))
            metrics['max_community_transfers'] = max(community_transfers.values())
            metrics['min_community_transfers'] = min(community_transfers.values())
            metrics['community_transfers'] = community_transfers
        
        return metrics
    
    def analyze_connection_quality(self) -> Dict[str, Any]:
        """
        Analyze the quality of connections in the network.
        
        Returns:
            Dictionary with connection quality metrics
        """
        logger.info("Analyzing connection quality")
        
        # Calculate edge betweenness centrality
        edge_betweenness = nx.edge_betweenness_centrality(self.graph)
        
        # Identify critical connections
        critical_connections = sorted(edge_betweenness.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate connection redundancy
        redundancy = {}
        
        # Sample node pairs for efficiency
        sample_size = min(100, self.graph.number_of_nodes())
        sample_nodes = np.random.choice(list(self.graph.nodes()), sample_size, replace=False)
        
        for i, n1 in enumerate(sample_nodes):
            for n2 in sample_nodes[i+1:]:
                try:
                    # Calculate edge connectivity (minimum number of edges to remove to disconnect)
                    conn = nx.edge_connectivity(self.graph, n1, n2)
                    redundancy[(n1, n2)] = conn
                except:
                    pass
        
        if redundancy:
            avg_redundancy = np.mean(list(redundancy.values()))
        else:
            avg_redundancy = 0
        
        # Identify bottlenecks
        bottlenecks = [(edge, score) for edge, score in critical_connections[:10]]
        
        return {
            'critical_connections': critical_connections[:20],
            'bottlenecks': bottlenecks,
            'avg_redundancy': avg_redundancy,
            'redundancy_samples': redundancy
        }
    
    def analyze_community_accessibility(self) -> Dict[int, Dict[str, Any]]:
        """
        Analyze accessibility metrics for each community.
        
        Returns:
            Dictionary mapping community IDs to accessibility metrics
        """
        if not self.partition:
            logger.error("Cannot analyze community accessibility: no partition provided")
            return {}
            
        logger.info("Analyzing community accessibility")
        
        community_accessibility = {}
        
        for comm_id in set(self.partition.values()):
            # Get nodes in this community
            comm_nodes = [n for n, c in self.partition.items() if c == comm_id]
            
            # Skip empty communities
            if not comm_nodes:
                continue
                
            # Create subgraph for this community
            subgraph = self.graph.subgraph(comm_nodes)
            
            # Calculate metrics
            metrics = {}
            
            # Basic metrics
            metrics['size'] = len(comm_nodes)
            metrics['internal_edges'] = subgraph.number_of_edges()
            metrics['density'] = nx.density(subgraph)
            
            # Calculate internal efficiency if possible
            if len(comm_nodes) > 1:
                if nx.is_connected(subgraph):
                    metrics['avg_internal_path'] = nx.average_shortest_path_length(subgraph)
                else:
                    # Calculate for largest connected component
                    largest_cc = max(nx.connected_components(subgraph), key=len)
                    largest_G = subgraph.subgraph(largest_cc)
                    if len(largest_cc) > 1:
                        metrics['avg_internal_path'] = nx.average_shortest_path_length(largest_G)
                        metrics['largest_cc_ratio'] = len(largest_cc) / len(comm_nodes)
                    else:
                        metrics['avg_internal_path'] = 0
                        metrics['largest_cc_ratio'] = 1 / len(comm_nodes)
            else:
                metrics['avg_internal_path'] = 0
                metrics['largest_cc_ratio'] = 1
            
            # Calculate external connectivity
            external_edges = 0
            external_communities = set()
            
            for node in comm_nodes:
                for neighbor in self.graph.neighbors(node):
                    if self.partition.get(neighbor) != comm_id:
                        external_edges += 1
                        external_communities.add(self.partition.get(neighbor))
            
            metrics['external_edges'] = external_edges
            metrics['connected_communities'] = len(external_communities)
            
            if len(comm_nodes) > 0:
                metrics['external_connectivity'] = external_edges / len(comm_nodes)
            else:
                metrics['external_connectivity'] = 0
            
            # Calculate accessibility score
            # Higher is better - combines internal efficiency and external connectivity
            internal_score = 1 / (1 + metrics.get('avg_internal_path', 0))
            external_score = metrics['external_connectivity']
            
            metrics['accessibility_score'] = (internal_score + external_score) / 2
            
            community_accessibility[comm_id] = metrics
        
        return community_accessibility