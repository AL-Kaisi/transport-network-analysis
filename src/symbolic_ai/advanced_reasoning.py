"""
Advanced symbolic reasoning for transport networks.
"""

import networkx as nx
import numpy as np
from sympy.logic.boolalg import And, Or, Not, Implies, Equivalent
from sympy import symbols, sympify
from typing import Dict, List, Tuple, Any, Set
import logging

logger = logging.getLogger(__name__)

class AdvancedTransportReasoning:
    """Class for advanced symbolic reasoning about transport networks."""
    
    def __init__(self, graph: nx.Graph, partition: Dict[Any, int], critical_nodes: List[Tuple[Any, float]]):
        """
        Initialize advanced reasoning.
        
        Args:
            graph: NetworkX graph representing the transport network
            partition: Dictionary mapping node IDs to community IDs
            critical_nodes: List of tuples (node_id, centrality_score)
        """
        self.graph = graph
        self.partition = partition
        self.critical_nodes = critical_nodes
        self.kb = {}
        self.symbols = {}
        
    def create_advanced_knowledge_base(self) -> Dict:
        """
        Create an advanced symbolic knowledge base with more sophisticated rules.
        
        Returns:
            Dictionary with symbolic entities and rules
        """
        logger.info("Creating advanced symbolic knowledge base")
        
        # Create symbols for communities
        community_symbols = {}
        for comm_id in set(self.partition.values()):
            name = f"Community_{comm_id}"
            community_symbols[comm_id] = symbols(name)
            self.symbols[name] = community_symbols[comm_id]
        
        # Create symbols for critical nodes
        node_symbols = {}
        for node_id, _ in self.critical_nodes:
            node_name = self.graph.nodes[node_id].get('name', str(node_id))
            safe_name = node_name.replace(' ', '_').replace('-', '_')
            name = f"Node_{safe_name}"
            node_symbols[node_id] = symbols(name)
            self.symbols[name] = node_symbols[node_id]
        
        self.kb['communities'] = community_symbols
        self.kb['nodes'] = node_symbols
        
        # Create advanced membership rules with bidirectional implications
        membership_rules = []
        for node_id, node_symbol in node_symbols.items():
            comm_id = self.partition[node_id]
            rule = Equivalent(node_symbol, And(node_symbol, community_symbols[comm_id]))
            membership_rules.append(rule)
        
        self.kb['membership_rules'] = membership_rules
        
        # Create community connectivity rules
        community_connections = self._find_community_connections()
        connectivity_rules = []
        
        for comm1, comm2 in community_connections:
            # Create symbol for this connection
            conn_name = f"Connected_{comm1}_{comm2}"
            conn_symbol = symbols(conn_name)
            self.symbols[conn_name] = conn_symbol
            
            # Create rule: Community A and Community B are connected
            rule = Implies(
                And(community_symbols[comm1], community_symbols[comm2]),
                conn_symbol
            )
            connectivity_rules.append(rule)
        
        self.kb['connectivity_rules'] = connectivity_rules
        
        # Create node dependency rules
        dependency_rules = []
        
        # Find which nodes are critical for connecting communities
        community_bridges = self._find_community_bridges()
        
        for node_id, connections in community_bridges.items():
            if node_id not in node_symbols:
                continue
                
            node_symbol = node_symbols[node_id]
            
            for comm1, comm2 in connections:
                if (comm1, comm2) not in community_connections:
                    continue
                    
                # Create symbol for this dependency
                dep_name = f"Depends_{comm1}_{comm2}_on_{node_id}"
                dep_symbol = symbols(dep_name)
                self.symbols[dep_name] = dep_symbol
                
                # Create rule: If Node is removed, Community A and Community B become disconnected
                conn_name = f"Connected_{comm1}_{comm2}"
                
                rule = Implies(
                    Not(node_symbol),
                    Not(self.symbols[conn_name])
                )
                dependency_rules.append(rule)
        
        self.kb['dependency_rules'] = dependency_rules
        
        # Create redundancy rules
        redundancy_rules = []
        
        # Find redundant paths between communities
        redundant_paths = self._find_redundant_paths()
        
        for (comm1, comm2), redundancy in redundant_paths.items():
            if (comm1, comm2) not in community_connections:
                continue
                
            # Create symbol for redundancy
            red_name = f"Redundant_{comm1}_{comm2}"
            red_symbol = symbols(red_name)
            self.symbols[red_name] = red_symbol
            
            # Create rule: If there are redundant paths, the connection is more reliable
            conn_name = f"Connected_{comm1}_{comm2}"
            
            rule = Implies(
                self.symbols[conn_name],
                red_symbol if redundancy > 1 else Not(red_symbol)
            )
            redundancy_rules.append(rule)
        
        self.kb['redundancy_rules'] = redundancy_rules
        
        logger.info(f"Created advanced knowledge base with:")
        logger.info(f"- {len(community_symbols)} community symbols")
        logger.info(f"- {len(node_symbols)} node symbols")
        logger.info(f"- {len(membership_rules)} membership rules")
        logger.info(f"- {len(connectivity_rules)} connectivity rules")
        logger.info(f"- {len(dependency_rules)} dependency rules")
        logger.info(f"- {len(redundancy_rules)} redundancy rules")
        
        return self.kb
    
    def _find_community_connections(self) -> Set[Tuple[int, int]]:
        """Find direct connections between communities."""
        connections = set()
        
        for source, target in self.graph.edges():
            source_comm = self.partition.get(source)
            target_comm = self.partition.get(target)
            
            if source_comm != target_comm:
                connections.add((min(source_comm, target_comm), max(source_comm, target_comm)))
        
        return connections
    
    def _find_community_bridges(self) -> Dict[Any, List[Tuple[int, int]]]:
        """Find nodes that are bridges between communities."""
        bridges = {}
        
        for node_id, _ in self.critical_nodes:
            node_comm = self.partition.get(node_id)
            
            # Get communities connected through this node
            connections = []
            neighbor_comms = set()
            
            for neighbor in self.graph.neighbors(node_id):
                neigh_comm = self.partition.get(neighbor)
                if neigh_comm != node_comm:
                    neighbor_comms.add(neigh_comm)
            
            # Check which community pairs are connected through this node
            for comm1 in neighbor_comms:
                for comm2 in neighbor_comms:
                    if comm1 < comm2:
                        connections.append((comm1, comm2))
            
            bridges[node_id] = connections
        
        return bridges
    
    def _find_redundant_paths(self) -> Dict[Tuple[int, int], int]:
        """Find redundant paths between communities."""
        redundancy = {}
        
        # Get community connections
        connections = self._find_community_connections()
        
        for comm1, comm2 in connections:
            # Find nodes in each community
            comm1_nodes = [n for n, c in self.partition.items() if c == comm1]
            comm2_nodes = [n for n, c in self.partition.items() if c == comm2]
            
            # Sample nodes if there are too many
            if len(comm1_nodes) > 10 or len(comm2_nodes) > 10:
                comm1_nodes = np.random.choice(comm1_nodes, min(10, len(comm1_nodes)), replace=False)
                comm2_nodes = np.random.choice(comm2_nodes, min(10, len(comm2_nodes)), replace=False)
            
            # Count the number of edge-disjoint paths
            max_paths = 0
            
            for n1 in comm1_nodes:
                for n2 in comm2_nodes:
                    try:
                        # Count edge-disjoint paths
                        paths = nx.edge_disjoint_paths(self.graph, n1, n2)
                        num_paths = len(list(paths))
                        max_paths = max(max_paths, num_paths)
                    except:
                        pass
            
            redundancy[(comm1, comm2)] = max_paths
        
        return redundancy
    
    def generate_advanced_queries(self) -> List[Dict]:
        """
        Generate advanced logical queries for the knowledge base.
        
        Returns:
            List of query dictionaries
        """
        logger.info("Generating advanced logical queries")
        
        if not self.kb:
            self.create_advanced_knowledge_base()
        
        queries = []
        
        # Generate query about community connections
        community_connections = self._find_community_connections()
        if community_connections:
            # Pick a random connection
            comm1, comm2 = list(community_connections)[0]
            
            conn_name = f"Connected_{comm1}_{comm2}"
            if conn_name in self.symbols:
                queries.append({
                    'name': 'Community Connectivity',
                    'description': f"Are Community {comm1} and Community {comm2} connected?",
                    'query': f"{conn_name}",
                    'result': True
                })
        
        # Generate query about critical node
        community_bridges = self._find_community_bridges()
        for node_id, connections in community_bridges.items():
            if connections and node_id in self.kb.get('nodes', {}):
                # Pick the first connection
                comm1, comm2 = connections[0]
                
                node_name = self.graph.nodes[node_id].get('name', str(node_id))
                
                queries.append({
                    'name': 'Critical Node Impact',
                    'description': f"What happens if {node_name} is removed?",
                    'query': f"Impact(Not(Node_{node_name.replace(' ', '_').replace('-', '_')}))",
                    'result': f"Communities {comm1} and {comm2} may become disconnected"
                })
                
                break
        
        # Generate query about redundancy
        redundant_paths = self._find_redundant_paths()
        for (comm1, comm2), redundancy in redundant_paths.items():
            red_name = f"Redundant_{comm1}_{comm2}"
            if red_name in self.symbols:
                queries.append({
                    'name': 'Path Redundancy',
                    'description': f"Are there redundant paths between Community {comm1} and Community {comm2}?",
                    'query': f"{red_name}",
                    'result': redundancy > 1
                })
                break
        
        # Generate query about dependency chain
        if community_bridges and len(self.critical_nodes) >= 2:
            # Find two critical nodes
            node1_id = self.critical_nodes[0][0]
            node2_id = self.critical_nodes[1][0]
            
            if node1_id in community_bridges and node2_id in community_bridges:
                node1_name = self.graph.nodes[node1_id].get('name', str(node1_id))
                node2_name = self.graph.nodes[node2_id].get('name', str(node2_id))
                
                queries.append({
                    'name': 'Dependency Chain',
                    'description': f"What happens if both {node1_name} and {node2_name} are removed?",
                    'query': f"Impact(And(Not(Node_{node1_name.replace(' ', '_').replace('-', '_')}), Not(Node_{node2_name.replace(' ', '_').replace('-', '_')})))",
                    'result': "Multiple communities may become disconnected, severely impacting network connectivity"
                })
        
        return queries
    
    def perform_advanced_reasoning(self) -> Dict[str, Any]:
        """
        Perform advanced reasoning tasks on the network.
        
        Returns:
            Dictionary with reasoning results
        """
        logger.info("Performing advanced reasoning tasks")
        
        if not self.kb:
            self.create_advanced_knowledge_base()
        
        results = {}
        
        # Analyze network vulnerability
        vulnerability = self._analyze_vulnerability()
        results['vulnerability'] = vulnerability
        
        # Analyze community resilience
        resilience = self._analyze_community_resilience()
        results['community_resilience'] = resilience
        
        # Analyze interdependencies
        interdependencies = self._analyze_interdependencies()
        results['interdependencies'] = interdependencies
        
        # Generate improvement recommendations
        recommendations = self._generate_recommendations()
        results['recommendations'] = recommendations
        
        return results
    
    def _analyze_vulnerability(self) -> Dict[str, Any]:
        """Analyze network vulnerability."""
        # Calculate vulnerability score for each community based on connectivity
        community_vulnerability = {}
        
        for comm_id in set(self.partition.values()):
            # Count connections to other communities
            connections = 0
            for source, target in self.graph.edges():
                if self.partition.get(source) == comm_id and self.partition.get(target) != comm_id:
                    connections += 1
            
            # Get number of nodes in community
            community_size = len([n for n, c in self.partition.items() if c == comm_id])
            
            # Calculate vulnerability as inverse of connectivity ratio
            if community_size > 0:
                connectivity_ratio = connections / community_size
                vulnerability = 1 - (connectivity_ratio / max(1, connectivity_ratio))
            else:
                vulnerability = 1
            
            community_vulnerability[comm_id] = {
                'connections': connections,
                'size': community_size,
                'vulnerability': vulnerability
            }
        
        # Find most vulnerable communities
        vulnerable_communities = sorted(
            community_vulnerability.items(),
            key=lambda x: x[1]['vulnerability'],
            reverse=True
        )
        
        # Calculate overall network vulnerability
        overall_vulnerability = sum(d['vulnerability'] for _, d in community_vulnerability.items()) / len(community_vulnerability)
        
        return {
            'community_vulnerability': community_vulnerability,
            'most_vulnerable': vulnerable_communities[:5],
            'overall_vulnerability': overall_vulnerability
        }
    
    def _analyze_community_resilience(self) -> Dict[str, Any]:
        """Analyze community resilience to disruptions."""
        redundant_paths = self._find_redundant_paths()
        
        # Calculate resilience score for each community
        community_resilience = {}
        for comm_id in set(self.partition.values()):
            # Get average redundancy of connections
            comm_redundancies = []
            for (c1, c2), redundancy in redundant_paths.items():
                if c1 == comm_id or c2 == comm_id:
                    comm_redundancies.append(redundancy)
            
            # Calculate resilience score
            if comm_redundancies:
                avg_redundancy = sum(comm_redundancies) / len(comm_redundancies)
                max_redundancy = max(comm_redundancies)
                resilience = (avg_redundancy + max_redundancy) / 2
            else:
                resilience = 0
            
            community_resilience[comm_id] = {
                'avg_redundancy': avg_redundancy if comm_redundancies else 0,
                'max_redundancy': max_redundancy if comm_redundancies else 0,
                'resilience': resilience
            }
        
        # Find most and least resilient communities
        resilient_communities = sorted(
            community_resilience.items(),
            key=lambda x: x[1]['resilience'],
            reverse=True
        )
        
        vulnerable_communities = sorted(
            community_resilience.items(),
            key=lambda x: x[1]['resilience']
        )
        
        return {
            'community_resilience': community_resilience,
            'most_resilient': resilient_communities[:5],
            'least_resilient': vulnerable_communities[:5],
        }
    
    def _analyze_interdependencies(self) -> Dict[str, Any]:
        """Analyze interdependencies between communities."""
        # Create a community-to-community dependency graph
        community_graph = nx.Graph()
        
        # Add communities as nodes
        for comm_id in set(self.partition.values()):
            # Count nodes in community
            nodes = len([n for n, c in self.partition.items() if c == comm_id])
            community_graph.add_node(comm_id, size=nodes)
        
        # Add edges between communities
        for source, target in self.graph.edges():
            source_comm = self.partition.get(source)
            target_comm = self.partition.get(target)
            
            if source_comm != target_comm:
                if community_graph.has_edge(source_comm, target_comm):
                    community_graph[source_comm][target_comm]['weight'] += 1
                else:
                    community_graph.add_edge(source_comm, target_comm, weight=1)
        
        # Calculate betweenness centrality for communities
        try:
            centrality = nx.betweenness_centrality(community_graph, weight='weight')
        except:
            centrality = {comm: 0 for comm in community_graph.nodes()}
        
        # Identify central communities
        central_communities = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate dependency metric for each community
        community_dependencies = {}
        for comm_id in community_graph.nodes():
            # Number of dependent connections
            dependents = sum(community_graph[comm_id][neigh]['weight'] 
                            for neigh in community_graph.neighbors(comm_id))
            
            # Dependency score is betweenness scaled by number of connections
            dependency_score = centrality[comm_id] * dependents if dependents > 0 else 0
            
            community_dependencies[comm_id] = {
                'centrality': centrality[comm_id],
                'dependents': dependents,
                'dependency_score': dependency_score
            }
        
        # Sort by dependency score
        key_communities = sorted(
            community_dependencies.items(),
            key=lambda x: x[1]['dependency_score'],
            reverse=True
        )
        
        return {
            'community_dependencies': community_dependencies,
            'key_communities': key_communities[:5],
            'community_graph': community_graph
        }
    
    def _generate_recommendations(self) -> List[Dict]:
        """Generate network improvement recommendations."""
        recommendations = []
        
        # Get vulnerability and resilience analysis
        vulnerability = self._analyze_vulnerability()
        resilience = self._analyze_community_resilience()
        
        # Recommend improving connections for vulnerable communities
        if vulnerability and 'most_vulnerable' in vulnerability:
            for comm_id, data in vulnerability['most_vulnerable'][:3]:
                if data['vulnerability'] > 0.5:  # Only recommend for significantly vulnerable communities
                    # Find nearby communities to connect to
                    nearby_communities = []
                    
                    # Get nodes in this community
                    comm_nodes = [n for n, c in self.partition.items() if c == comm_id]
                    
                    # Find communities of neighbors
                    neighbor_comms = set()
                    for node in comm_nodes:
                        for neighbor in self.graph.neighbors(node):
                            neigh_comm = self.partition.get(neighbor)
                            if neigh_comm != comm_id:
                                neighbor_comms.add(neigh_comm)
                    
                    # Find which communities are already connected
                    connected_comms = set()
                    for (c1, c2) in self._find_community_connections():
                        if c1 == comm_id:
                            connected_comms.add(c2)
                        elif c2 == comm_id:
                            connected_comms.add(c1)
                    
                    # Potential new connections
                    potential_connections = neighbor_comms - connected_comms
                    
                    recommendations.append({
                        'type': 'connectivity',
                        'description': f"Improve connectivity for vulnerable Community {comm_id}",
                        'details': f"Community {comm_id} has a vulnerability score of {data['vulnerability']:.2f}",
                        'action': f"Add connections to nearby communities: {', '.join(map(str, potential_connections))}"
                    })
        
        # Recommend increasing redundancy for critical connections
        redundant_paths = self._find_redundant_paths()
        critical_connections = []
        
        for (comm1, comm2), redundancy in redundant_paths.items():
            if redundancy <= 1:
                # This is a critical connection with no redundancy
                # Calculate size of communities to prioritize
                size1 = len([n for n, c in self.partition.items() if c == comm1])
                size2 = len([n for n, c in self.partition.items() if c == comm2])
                
                critical_connections.append(((comm1, comm2), size1 + size2))
        
        # Sort by community size (impact)
        critical_connections.sort(key=lambda x: x[1], reverse=True)
        
        for (comm1, comm2), _ in critical_connections[:3]:
            recommendations.append({
                'type': 'redundancy',
                'description': f"Increase redundancy between Communities {comm1} and {comm2}",
                'details': f"There is only one path connecting these communities, creating a vulnerability",
                'action': f"Add additional transport links between these communities to provide alternate routes"
            })
        
        # Recommend reducing dependency on critical nodes
        community_bridges = self._find_community_bridges()
        critical_bridges = []
        
        for node_id, connections in community_bridges.items():
            if len(connections) > 1:
                # This node connects multiple community pairs
                critical_bridges.append((node_id, len(connections)))
        
        # Sort by number of connections
        critical_bridges.sort(key=lambda x: x[1], reverse=True)
        
        for node_id, num_connections in critical_bridges[:3]:
            node_name = self.graph.nodes[node_id].get('name', str(node_id))
            
            recommendations.append({
                'type': 'redundancy',
                'description': f"Reduce dependency on critical node {node_name}",
                'details': f"This node connects {num_connections} community pairs, creating a single point of failure",
                'action': f"Add alternative routes that bypass this node to maintain connectivity if it becomes unavailable"
            })
        
        return recommendations