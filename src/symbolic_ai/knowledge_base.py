"""
Knowledge base module for symbolic AI reasoning about transport networks.
"""

import networkx as nx
from sympy.logic.boolalg import And, Or, Not, Implies
from sympy import symbols, sympify
from typing import Dict, List, Any, Tuple, Set
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TransportKnowledgeBase:
    """Class for creating and reasoning with a symbolic knowledge base for transport networks."""
    
    def __init__(self, graph: nx.Graph, partition: Dict[Any, int]):
        """
        Initialize the knowledge base.
        
        Args:
            graph: NetworkX graph representing the transport network
            partition: Dictionary mapping node IDs to community IDs
        """
        self.graph = graph
        self.partition = partition
        self.kb = {}
        self.symbols = {}
        
    def create_knowledge_base(self, max_critical_nodes: int = 50) -> Dict:
        """
        Create a symbolic knowledge base for transport network reasoning.
        
        Args:
            max_critical_nodes: Maximum number of critical nodes to include (for efficiency)
            
        Returns:
            Dictionary with symbolic entities and rules
        """
        logger.info("Creating symbolic knowledge base for transport network")
        
        # Create symbols for communities
        community_symbols = {}
        for comm_id in set(self.partition.values()):
            name = f"Community_{comm_id}"
            community_symbols[comm_id] = symbols(name)
            self.symbols[name] = community_symbols[comm_id]
        
        # Find critical nodes (using betweenness centrality)
        betweenness = nx.betweenness_centrality(self.graph, k=500, normalized=True)
        critical_nodes = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:max_critical_nodes]
        
        # Create symbols for critical nodes
        node_symbols = {}
        for node_id, _ in critical_nodes:
            node_name = self.graph.nodes[node_id].get('name', f"Stop_{node_id}")
            safe_name = node_name.replace(' ', '_').replace('-', '_')
            name = f"Stop_{safe_name}"
            node_symbols[node_id] = symbols(name)
            self.symbols[name] = node_symbols[node_id]
        
        self.kb['communities'] = community_symbols
        self.kb['nodes'] = node_symbols
        
        logger.info(f"Created symbols for {len(community_symbols)} communities and {len(node_symbols)} critical nodes")
        
        # Create membership rules: node → community
        membership_rules = []
        for node_id, node_symbol in node_symbols.items():
            community_id = self.partition[node_id]
            rule = Implies(node_symbol, community_symbols[community_id])
            membership_rules.append(rule)
        
        self.kb['membership_rules'] = membership_rules
        logger.info(f"Created {len(membership_rules)} membership rules")
        
        # Create connectivity rules: if nodes are connected
        connectivity_rules = []
        
        # Get pairs of critical nodes that are directly connected
        critical_node_ids = list(node_symbols.keys())
        for i, node1 in enumerate(critical_node_ids):
            for node2 in critical_node_ids[i+1:]:
                if self.graph.has_edge(node1, node2):
                    rule = Implies(
                        And(node_symbols[node1], node_symbols[node2]),
                        symbols(f"Connected_{node1}_{node2}")
                    )
                    connectivity_rules.append(rule)
                    self.symbols[f"Connected_{node1}_{node2}"] = symbols(f"Connected_{node1}_{node2}")
        
        self.kb['connectivity_rules'] = connectivity_rules
        logger.info(f"Created {len(connectivity_rules)} connectivity rules")
        
        # Create community connectivity rules
        community_connectivity_rules = []
        
        # Find connections between communities
        community_connections = set()
        for node1, node2 in self.graph.edges():
            comm1 = self.partition[node1]
            comm2 = self.partition[node2]
            if comm1 != comm2:
                community_connections.add((min(comm1, comm2), max(comm1, comm2)))
        
        # Create rules for community connections
        for comm1, comm2 in community_connections:
            rule = Implies(
                And(community_symbols[comm1], community_symbols[comm2]),
                symbols(f"ConnectedCommunities_{comm1}_{comm2}")
            )
            community_connectivity_rules.append(rule)
            self.symbols[f"ConnectedCommunities_{comm1}_{comm2}"] = symbols(f"ConnectedCommunities_{comm1}_{comm2}")
        
        self.kb['community_connectivity_rules'] = community_connectivity_rules
        logger.info(f"Created {len(community_connectivity_rules)} community connectivity rules")
        
        return self.kb
    
    def perform_symbolic_reasoning(self, critical_nodes: List[Tuple[Any, float]]) -> Dict:
        """
        Perform symbolic reasoning to extract insights from the knowledge base.
        
        Args:
            critical_nodes: List of critical nodes with their centrality scores
            
        Returns:
            Dictionary with reasoning results
        """
        logger.info("Performing symbolic reasoning on transport network")
        
        if not self.kb:
            self.create_knowledge_base()
        
        results = {}
        
        # Find gateway nodes (nodes that connect multiple communities)
        gateway_nodes = {}
        for node_id, _ in critical_nodes:
            if node_id not in self.kb['nodes']:
                continue
                
            node_community = self.partition[node_id]
            neighbor_communities = set()
            
            for neighbor in self.graph.neighbors(node_id):
                neigh_community = self.partition[neighbor]
                if neigh_community != node_community:
                    neighbor_communities.add(neigh_community)
            
            gateway_nodes[node_id] = {
                'name': self.graph.nodes[node_id].get('name', f"Stop_{node_id}"),
                'community': node_community,
                'connected_communities': list(neighbor_communities),
                'num_communities': len(neighbor_communities)
            }
        
        # Sort gateway nodes by number of connected communities
        sorted_gateway_nodes = sorted(gateway_nodes.items(), 
                                       key=lambda x: x[1]['num_communities'], 
                                       reverse=True)
        
        results['gateway_nodes'] = sorted_gateway_nodes
        
        # Find community dependencies
        community_dependencies = {}
        
        for comm_id in set(self.partition.values()):
            # Find which other communities this one depends on
            connected_comms = set()
            comm_nodes = [node for node, com in self.partition.items() if com == comm_id]
            
            for node in comm_nodes:
                for neighbor in self.graph.neighbors(node):
                    neigh_comm = self.partition[neighbor]
                    if neigh_comm != comm_id:
                        connected_comms.add(neigh_comm)
            
            community_dependencies[comm_id] = {
                'connected_to': list(connected_comms),
                'num_connections': len(connected_comms)
            }
        
        # Sort communities by number of connections
        sorted_community_deps = sorted(community_dependencies.items(), 
                                      key=lambda x: x[1]['num_connections'], 
                                      reverse=True)
        
        results['community_dependencies'] = sorted_community_deps
        
        # Identify network vulnerabilities
        vulnerabilities = []
        
        # Find connections between communities
        community_connections = set()
        for node1, node2 in self.graph.edges():
            comm1 = self.partition[node1]
            comm2 = self.partition[node2]
            if comm1 != comm2:
                community_connections.add((min(comm1, comm2), max(comm1, comm2)))
        
        # Top 10 critical nodes
        top_nodes = critical_nodes[:10]
        for node_id, score in top_nodes:
            node_name = self.graph.nodes[node_id].get('name', f"Stop_{node_id}")
            node_community = self.partition[node_id]
            
            # Simulate removing this node
            G_temp = self.graph.copy()
            G_temp.remove_node(node_id)
            
            # Check how many communities would be affected
            affected_communities = set()
            for comm1, comm2 in community_connections:
                # Check if there's still a path between these communities
                found_path = False
                
                # Get a sample of nodes from each community to check paths
                # (checking all pairs would be too computationally expensive)
                comm1_nodes = [n for n in G_temp.nodes() if self.partition.get(n) == comm1][:5]
                comm2_nodes = [n for n in G_temp.nodes() if self.partition.get(n) == comm2][:5]
                
                for node1 in comm1_nodes:
                    for node2 in comm2_nodes:
                        try:
                            path = nx.shortest_path(G_temp, node1, node2)
                            found_path = True
                            break
                        except (nx.NetworkXNoPath, nx.NodeNotFound):
                            continue
                    if found_path:
                        break
                
                if not found_path:
                    affected_communities.add(comm1)
                    affected_communities.add(comm2)
            
            vulnerabilities.append({
                'node_id': node_id,
                'name': node_name,
                'community': node_community,
                'centrality': score,
                'affected_communities': list(affected_communities),
                'impact': len(affected_communities)
            })
        
        results['vulnerabilities'] = vulnerabilities
        
        return results
    
    def generate_logical_queries(self) -> List[Dict]:
        """
        Generate sample logical queries that can be executed on the knowledge base.
        
        Returns:
            List of sample queries
        """
        logger.info("Generating sample logical queries")
        
        if not self.kb:
            self.create_knowledge_base()
        
        queries = []
        
        # Sample query 1: Can you get from Community A to Community B?
        community_ids = list(self.kb['communities'].keys())
        if len(community_ids) >= 2:
            comm1, comm2 = community_ids[0], community_ids[1]
            query_str = f"Connected(Community_{comm1}, Community_{comm2})"
            
            # Evaluate if there is a connection
            connected = False
            for rule in self.kb['community_connectivity_rules']:
                if isinstance(rule, Implies) and str(rule.args[1]) == f"ConnectedCommunities_{min(comm1, comm2)}_{max(comm1, comm2)}":
                    connected = True
                    break
            
            queries.append({
                'name': 'Community Connectivity',
                'description': f"Is Community {comm1} connected to Community {comm2}?",
                'query': query_str,
                'result': connected
            })
        
        # Sample query 2: Which community does a stop belong to?
        node_ids = list(self.kb['nodes'].keys())
        if node_ids:
            node_id = node_ids[0]
            node_name = self.graph.nodes[node_id].get('name', f"Stop_{node_id}")
            community_id = self.partition[node_id]
            
            query_str = f"Community(Stop_{node_name.replace(' ', '_').replace('-', '_')})"
            
            queries.append({
                'name': 'Stop Community',
                'description': f"Which community does {node_name} belong to?",
                'query': query_str,
                'result': f"Community {community_id}"
            })
        
        # Sample query 3: What happens if a critical node is removed?
        if node_ids:
            node_id = node_ids[0]
            node_name = self.graph.nodes[node_id].get('name', f"Stop_{node_id}")
            
            # Find communities connected through this node
            node_community = self.partition[node_id]
            connected_communities = set()
            
            for neighbor in self.graph.neighbors(node_id):
                neigh_community = self.partition[neighbor]
                if neigh_community != node_community:
                    connected_communities.add(neigh_community)
            
            query_str = f"Impact(Remove(Stop_{node_name.replace(' ', '_').replace('-', '_')}))"
            
            queries.append({
                'name': 'Node Removal Impact',
                'description': f"What is the impact of removing {node_name}?",
                'query': query_str,
                'result': f"Disconnects Community {node_community} from Communities {', '.join(map(str, connected_communities))}"
            })
        
        return queries