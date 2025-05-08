"""
Test script for the symbolic AI component.
"""

import os
import networkx as nx
from dotenv import load_dotenv
from src.data_processing.gtfs_loader import GTFSLoader
from src.graph_analysis.graph_builder import TransportGraphBuilder
from src.graph_analysis.community_detection import CommunityDetector
from src.symbolic_ai.knowledge_base import TransportKnowledgeBase

# Load environment variables
load_dotenv()

def main():
    # Get configuration from environment variables
    gtfs_url = os.getenv("GTFS_URL")
    data_dir = os.getenv("DATA_DIR")
    
    # Load GTFS data
    print("Loading GTFS data...")
    loader = GTFSLoader(gtfs_url, data_dir)
    
    # Check if data already exists, otherwise download it
    if not os.path.exists(os.path.join(data_dir, "stops.txt")):
        gtfs_data = loader.process()
    else:
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
    
    # Create symbolic knowledge base
    print("\nCreating symbolic knowledge base...")
    kb_creator = TransportKnowledgeBase(G, partition)
    kb = kb_creator.create_knowledge_base(max_critical_nodes=50)
    
    # Print knowledge base statistics
    print("\nKnowledge Base Statistics:")
    print(f"Communities: {len(kb['communities'])}")
    print(f"Critical nodes: {len(kb['nodes'])}")
    print(f"Membership rules: {len(kb['membership_rules'])}")
    print(f"Connectivity rules: {len(kb['connectivity_rules'])}")
    print(f"Community connectivity rules: {len(kb['community_connectivity_rules'])}")
    
    # Perform symbolic reasoning
    print("\nPerforming symbolic reasoning...")
    results = kb_creator.perform_symbolic_reasoning(critical_nodes)
    
    # Print gateway nodes (nodes connecting multiple communities)
    print("\nTop Gateway Nodes (connecting multiple communities):")
    for i, (node_id, data) in enumerate(results['gateway_nodes'][:10], 1):
        print(f"{i}. {data['name']} (Community {data['community']}):")
        print(f"   Connects to {data['num_communities']} communities: {data['connected_communities']}")
    
    # Print community dependencies
    print("\nCommunity Dependencies:")
    for i, (comm_id, data) in enumerate(results['community_dependencies'][:5], 1):
        print(f"{i}. Community {comm_id}:")
        print(f"   Connected to {data['num_connections']} communities: {data['connected_to']}")
    
    # Print network vulnerabilities
    print("\nNetwork Vulnerabilities:")
    for i, vuln in enumerate(results['vulnerabilities'][:5], 1):
        print(f"{i}. {vuln['name']} (Community {vuln['community']}):")
        print(f"   Impact if removed: Would affect {vuln['impact']} communities")
        print(f"   Affected communities: {vuln['affected_communities']}")
    
    # Generate sample logical queries
    print("\nSample Logical Queries:")
    queries = kb_creator.generate_logical_queries()
    
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query['name']}: {query['description']}")
        print(f"   Query: {query['query']}")
        print(f"   Result: {query['result']}")

if __name__ == "__main__":
    main()