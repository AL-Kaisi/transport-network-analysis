"""
Equity analysis for transport networks.
Evaluates the fairness of transport service distribution.
"""

import networkx as nx
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class EquityAnalyzer:
    """Class for analyzing equity in transport networks."""
    
    def __init__(self, graph: nx.Graph, partition: Optional[Dict[Any, int]] = None):
        """
        Initialize the equity analyzer.
        
        Args:
            graph: NetworkX graph representing the transport network
            partition: Optional dictionary mapping node IDs to community IDs
        """
        self.graph = graph
        self.partition = partition
        
    def analyze_service_distribution(self) -> Dict[str, Any]:
        """
        Analyze how transport service is distributed across the network.
        
        Returns:
            Dictionary with service distribution metrics
        """
        logger.info("Analyzing service distribution")
        
        # Calculate node degrees (number of connections)
        degrees = dict(self.graph.degree())
        
        # Calculate basic statistics
        avg_degree = np.mean(list(degrees.values()))
        median_degree = np.median(list(degrees.values()))
        std_degree = np.std(list(degrees.values()))
        min_degree = min(degrees.values())
        max_degree = max(degrees.values())
        
        # Calculate Gini coefficient (measure of inequality)
        gini = self._calculate_gini(list(degrees.values()))
        
        # Calculate coefficient of variation
        cv = std_degree / avg_degree if avg_degree > 0 else 0
        
        # Identify underserved nodes (nodes with low connectivity)
        threshold = avg_degree - std_degree
        underserved_nodes = {node: deg for node, deg in degrees.items() if deg < threshold}
        
        metrics = {
            'avg_degree': avg_degree,
            'median_degree': median_degree,
            'std_degree': std_degree,
            'min_degree': min_degree,
            'max_degree': max_degree,
            'gini_coefficient': gini,
            'coefficient_of_variation': cv,
            'underserved_nodes': len(underserved_nodes),
            'underserved_ratio': len(underserved_nodes) / len(degrees) if degrees else 0
        }
        
        # Analyze community-level distribution if partition is available
        if self.partition:
            community_metrics = self._analyze_community_distribution()
            metrics['community_distribution'] = community_metrics
            
            # Calculate between-community inequality
            community_avg_degrees = [data['avg_degree'] for data in community_metrics.values()]
            metrics['between_community_gini'] = self._calculate_gini(community_avg_degrees)
            
            # Calculate service balance ratio (how evenly distributed service is across communities)
            min_comm_deg = min(community_avg_degrees) if community_avg_degrees else 0
            max_comm_deg = max(community_avg_degrees) if community_avg_degrees else 0
            
            if max_comm_deg > 0:
                metrics['service_balance_ratio'] = min_comm_deg / max_comm_deg
            else:
                metrics['service_balance_ratio'] = 0
        
        return metrics
    
    def _analyze_community_distribution(self) -> Dict[int, Dict[str, float]]:
        """Analyze service distribution within each community."""
        community_metrics = {}
        
        for comm_id in set(self.partition.values()):
            # Get nodes in this community
            comm_nodes = [node for node, c in self.partition.items() if c == comm_id]
            
            # Skip empty communities
            if not comm_nodes:
                continue
                
            # Calculate degrees for nodes in this community
            comm_degrees = [self.graph.degree[node] for node in comm_nodes]
            
            # Calculate metrics
            avg_degree = np.mean(comm_degrees)
            median_degree = np.median(comm_degrees)
            std_degree = np.std(comm_degrees)
            gini = self._calculate_gini(comm_degrees)
            
            # Calculate coefficient of variation
            cv = std_degree / avg_degree if avg_degree > 0 else 0
            
            community_metrics[comm_id] = {
                'size': len(comm_nodes),
                'avg_degree': avg_degree,
                'median_degree': median_degree,
                'std_degree': std_degree,
                'gini_coefficient': gini,
                'coefficient_of_variation': cv
            }
        
        return community_metrics
    
    @staticmethod
    def _calculate_gini(values: List[float]) -> float:
        """
        Calculate the Gini coefficient, a measure of inequality.
        0 means perfect equality, 1 means perfect inequality.
        """
        if not values:
            return 0
            
        # Sort values
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n <= 1 or sum(sorted_values) == 0:
            return 0
            
        # Calculate Gini coefficient
        cum_values = np.cumsum(sorted_values)
        return (n + 1 - 2 * np.sum(cum_values) / cum_values[-1]) / n
    
    def analyze_accessibility_equity(self) -> Dict[str, Any]:
        """
        Analyze equity in terms of network accessibility.
        
        Returns:
            Dictionary with accessibility equity metrics
        """
        logger.info("Analyzing accessibility equity")
        
        # Calculate closeness centrality (measure of accessibility)
        try:
            closeness = nx.closeness_centrality(self.graph)
        except:
            # For disconnected graphs, calculate on largest component
            largest_cc = max(nx.connected_components(self.graph), key=len)
            largest_G = self.graph.subgraph(largest_cc)
            closeness = nx.closeness_centrality(largest_G)
            
            # Set closeness to 0 for nodes not in largest component
            for node in self.graph.nodes():
                if node not in closeness:
                    closeness[node] = 0
        
        # Calculate basic statistics
        closeness_values = list(closeness.values())
        avg_closeness = np.mean(closeness_values)
        median_closeness = np.median(closeness_values)
        std_closeness = np.std(closeness_values)
        
        # Calculate Gini coefficient for accessibility
        access_gini = self._calculate_gini(closeness_values)
        
        # Calculate coefficient of variation
        cv = std_closeness / avg_closeness if avg_closeness > 0 else 0
        
        # Identify poorly accessible nodes
        threshold = avg_closeness - std_closeness
        poor_access_nodes = {node: c for node, c in closeness.items() if c < threshold}
        
        metrics = {
            'avg_accessibility': avg_closeness,
            'median_accessibility': median_closeness,
            'std_accessibility': std_closeness,
            'accessibility_gini': access_gini,
            'accessibility_cv': cv,
            'poor_access_nodes': len(poor_access_nodes),
            'poor_access_ratio': len(poor_access_nodes) / len(closeness) if closeness else 0
        }
        
        # Analyze community-level accessibility if partition is available
        if self.partition:
            community_access = {}
            
            for comm_id in set(self.partition.values()):
                # Get nodes in this community
                comm_nodes = [node for node, c in self.partition.items() if c == comm_id]
                
                # Skip empty communities
                if not comm_nodes:
                    continue
                    
                # Calculate accessibility metrics for this community
                comm_closeness = [closeness.get(node, 0) for node in comm_nodes]
                
                community_access[comm_id] = {
                    'avg_accessibility': np.mean(comm_closeness),
                    'median_accessibility': np.median(comm_closeness),
                    'accessibility_gini': self._calculate_gini(comm_closeness)
                }
            
            metrics['community_accessibility'] = community_access
            
            # Calculate between-community inequality in accessibility
            community_avg_access = [data['avg_accessibility'] for data in community_access.values()]
            metrics['between_community_access_gini'] = self._calculate_gini(community_avg_access)
        
        return metrics
    
    def identify_equity_gaps(self) -> List[Dict[str, Any]]:
        """
        Identify specific equity gaps in the transport network.
        
        Returns:
            List of equity gap descriptions
        """
        logger.info("Identifying equity gaps")
        
        equity_gaps = []
        
        # Analyze service distribution
        distribution = self.analyze_service_distribution()
        
        # Check for high overall inequality
        if distribution['gini_coefficient'] > 0.3:
            equity_gaps.append({
                'type': 'service_inequality',
                'metric': 'gini_coefficient',
                'value': distribution['gini_coefficient'],
                'description': f"High inequality in service distribution (Gini = {distribution['gini_coefficient']:.2f})",
                'severity': 'high' if distribution['gini_coefficient'] > 0.5 else 'medium'
            })
        
        # Check for high ratio of underserved nodes
        if distribution['underserved_ratio'] > 0.2:
            equity_gaps.append({
                'type': 'underserved',
                'metric': 'underserved_ratio',
                'value': distribution['underserved_ratio'],
                'description': f"{distribution['underserved_ratio']*100:.1f}% of stops are underserved with below-average connectivity",
                'severity': 'high' if distribution['underserved_ratio'] > 0.3 else 'medium'
            })
        
        # Check for community-level inequalities if partition is available
        if self.partition and 'between_community_gini' in distribution:
            if distribution['between_community_gini'] > 0.2:
                equity_gaps.append({
                    'type': 'community_inequality',
                    'metric': 'between_community_gini',
                    'value': distribution['between_community_gini'],
                    'description': f"Uneven service distribution between communities (Gini = {distribution['between_community_gini']:.2f})",
                    'severity': 'high' if distribution['between_community_gini'] > 0.4 else 'medium'
                })
            
            # Check for poor service balance
            if distribution['service_balance_ratio'] < 0.5:
                equity_gaps.append({
                    'type': 'service_imbalance',
                    'metric': 'service_balance_ratio',
                    'value': distribution['service_balance_ratio'],
                    'description': f"Large disparity in service levels between communities (Ratio = {distribution['service_balance_ratio']:.2f})",
                    'severity': 'high' if distribution['service_balance_ratio'] < 0.3 else 'medium'
                })
        
        # Analyze accessibility equity
        accessibility = self.analyze_accessibility_equity()
        
        # Check for high accessibility inequality
        if accessibility['accessibility_gini'] > 0.3:
            equity_gaps.append({
                'type': 'accessibility_inequality',
                'metric': 'accessibility_gini',
                'value': accessibility['accessibility_gini'],
                'description': f"High inequality in network accessibility (Gini = {accessibility['accessibility_gini']:.2f})",
                'severity': 'high' if accessibility['accessibility_gini'] > 0.5 else 'medium'
            })
        
        # Check for high proportion of poorly accessible nodes
        if accessibility['poor_access_ratio'] > 0.2:
            equity_gaps.append({
                'type': 'poor_accessibility',
                'metric': 'poor_access_ratio',
                'value': accessibility['poor_access_ratio'],
                'description': f"{accessibility['poor_access_ratio']*100:.1f}% of stops have poor accessibility to the rest of the network",
                'severity': 'high' if accessibility['poor_access_ratio'] > 0.3 else 'medium'
            })
        
        # Check for community-level accessibility inequalities if partition is available
        if self.partition and 'between_community_access_gini' in accessibility:
            if accessibility['between_community_access_gini'] > 0.2:
                equity_gaps.append({
                    'type': 'community_accessibility',
                    'metric': 'between_community_access_gini',
                    'value': accessibility['between_community_access_gini'],
                    'description': f"Uneven accessibility between communities (Gini = {accessibility['between_community_access_gini']:.2f})",
                    'severity': 'high' if accessibility['between_community_access_gini'] > 0.4 else 'medium'
                })
        
        return equity_gaps