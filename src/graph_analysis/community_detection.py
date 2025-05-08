"""
Community detection module.
Implements community detection algorithms for transport networks.
"""

import networkx as nx
import community as community_louvain
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
from collections import defaultdict
from typing import Dict, List, Tuple, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CommunityDetector:
    """Class for detecting and analyzing communities in transport networks."""
    
    def __init__(self, graph: nx.Graph):
        """
        Initialize the community detector.
        
        Args:
            graph: NetworkX graph representing the transport network
        """
        self.graph = graph
        self.partition = None
        self.community_nodes = None
        self.modularity = None
        
    def detect_communities_louvain(self) -> Dict[Any, int]:
        """
        Detect communities using the Louvain method.
        
        Returns:
            Dictionary mapping node IDs to community IDs
        """
        logger.info("Detecting communities using Louvain method")
        
        # Apply the Louvain method
        self.partition = community_louvain.best_partition(self.graph)
        
        # Calculate modularity
        self.modularity = community_louvain.modularity(self.partition, self.graph)
        logger.info(f"Network modularity: {self.modularity:.4f}")
        
        # Group nodes by community
        self.community_nodes = defaultdict(list)
        for node, community_id in self.partition.items():
            self.community_nodes[community_id].append(node)
        
        communities = set(self.partition.values())
        logger.info(f"Number of communities detected: {len(communities)}")
        
        # Print some info about communities
        for community_id, nodes in self.community_nodes.items():
            logger.info(f"Community {community_id}: {len(nodes)} nodes")
        
        return self.partition
    
    def visualize_communities(self, output_file: str = "transport_communities.png") -> None:
        """
        Visualize the detected communities.
        
        Args:
            output_file: Path to save the visualization
        """
        if self.partition is None:
            raise ValueError("Communities have not been detected yet")
            
        logger.info("Visualizing communities")
        
        plt.figure(figsize=(15, 12))
        
        # Get positions for nodes
        pos = {}
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            if 'lat' in node_data and 'lon' in node_data:
                # Use geographic coordinates if available
                pos[node] = (node_data['lon'], node_data['lat'])
        
        # If we don't have positions for all nodes, use spring layout
        if len(pos) < len(self.graph.nodes()):
            logger.info("Using spring layout for node positioning")
            pos = nx.spring_layout(self.graph, seed=42)
        
        # Colors
        communities = set(self.partition.values())
        cmap = cm.get_cmap('tab20', max(communities) + 1)
        
        # Draw nodes
        for com in communities:
            # List nodes in this community
            com_nodes = [node for node in self.graph.nodes() if self.partition[node] == com]
            nx.draw_networkx_nodes(
                self.graph, 
                pos, 
                nodelist=com_nodes,
                node_color=[cmap(com)] * len(com_nodes),
                node_size=30,
                alpha=0.8,
                label=f"Community {com}"
            )
        
        # Draw edges
        nx.draw_networkx_edges(self.graph, pos, alpha=0.1, width=0.5)
        
        plt.title("Greater Manchester Transport Network Communities")
        plt.axis('off')
        plt.legend(scatterpoints=1, frameon=False, labelspacing=1)
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        logger.info(f"Visualization saved to {output_file}")
        plt.close()
    
    def analyze_communities(self) -> Dict:
        """
        Analyze the detected communities.
        
        Returns:
            Dictionary with community analysis results
        """
        if self.partition is None:
            raise ValueError("Communities have not been detected yet")
            
        logger.info("Analyzing communities")
        
        results = {
            "modularity": self.modularity,
            "num_communities": len(self.community_nodes),
            "communities": {}
        }
        
        # Analyze each community
        for community_id, nodes in self.community_nodes.items():
            # Get subgraph for this community
            subgraph = self.graph.subgraph(nodes)
            
            # Get node coordinates if available
            lats = []
            lons = []
            for node in nodes:
                node_data = self.graph.nodes[node]
                if 'lat' in node_data and 'lon' in node_data:
                    lats.append(node_data['lat'])
                    lons.append(node_data['lon'])
            
            # Calculate geographic center and radius if coordinates available
            if lats and lons:
                center_lat = np.mean(lats)
                center_lon = np.mean(lons)
                # Approximate radius as std dev of coordinates
                radius = np.std(lats) + np.std(lons)
            else:
                center_lat = None
                center_lon = None
                radius = None
            
            # Store community analysis
            results["communities"][community_id] = {
                "size": len(nodes),
                "density": nx.density(subgraph),
                "avg_degree": sum(dict(subgraph.degree()).values()) / len(nodes),
                "center_lat": center_lat,
                "center_lon": center_lon,
                "radius": radius
            }
        
        return results
    
    def identify_critical_nodes(self, top_n: int = 20) -> List[Tuple[Any, float]]:
        """
        Identify critical nodes using betweenness centrality.
        
        Args:
            top_n: Number of critical nodes to identify
            
        Returns:
            List of tuples (node_id, centrality_score)
        """
        logger.info(f"Identifying top {top_n} critical nodes")
        
        # Calculate betweenness centrality (this can be time-consuming for large networks)
        # Use approximate betweenness centrality for larger graphs
        if self.graph.number_of_nodes() > 1000:
            betweenness = nx.betweenness_centrality(self.graph, k=500, normalized=True)
        else:
            betweenness = nx.betweenness_centrality(self.graph, normalized=True)
        
        # Get top N nodes by centrality
        critical_nodes = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        # Log the critical nodes
        logger.info("Top critical stops:")
        for i, (node_id, score) in enumerate(critical_nodes, 1):
            node_name = self.graph.nodes[node_id].get('name', 'Unknown')
            community_id = self.partition[node_id] if self.partition else None
            logger.info(f"{i}. {node_name} (ID: {node_id})")
            logger.info(f"   Betweenness Centrality: {score:.6f}")
            if community_id is not None:
                logger.info(f"   Community: {community_id}")
        
        return critical_nodes