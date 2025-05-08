"""
Main script to run the complete transport network analysis with optimized performance.
"""
import sys
import os
import time
import pickle
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import logging
import argparse
import multiprocessing
from dotenv import load_dotenv
from concurrent.futures import ProcessPoolExecutor

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules
from src.data_processing.gtfs_loader import EnhancedGTFSLoader
from src.graph_analysis.graph_builder import TransportGraphBuilder
from src.graph_analysis.community_detection import CommunityDetector
from src.graph_analysis.critical_nodes import CriticalNodeAnalyzer
from src.graph_analysis.temporal_analysis import TemporalNetworkAnalyzer
from src.symbolic_ai.knowledge_base import TransportKnowledgeBase
from src.symbolic_ai.advanced_reasoning import AdvancedTransportReasoning
from src.visualizations.network_visualizer import NetworkVisualizer
from src.domain_analysis.transport_efficiency import TransportEfficiencyAnalyzer
from src.domain_analysis.equity_analysis import EquityAnalyzer
from src.utils.optimization import optimize_graph_for_memory, sample_graph_for_visualization
from src.utils.geocoding import enhance_node_coordinates

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Transport Network Analysis")
    
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/tfgm_gtfs",
        help="Directory containing GTFS data"
    )
    
    parser.add_argument(
        "--gtfs-url",
        type=str,
        default="https://odata.tfgm.com/opendata/downloads/TfGMgtfsnew.zip",
        help="URL to download GTFS data from"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Directory to save results"
    )
    
    parser.add_argument(
        "--sample-size",
        type=int,
        default=500,  # Reduced from 1000 to 500 for faster processing
        help="Number of trips to sample for graph construction"
    )
    
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Force download of GTFS data even if it exists locally"
    )
    
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Generate visualizations"
    )
    
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Optimize graph for memory usage"
    )
    
    parser.add_argument(
        "--enhance-geocoding",
        action="store_true",
        help="Enhance node coordinates using geocoding"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        default=True,
        help="Use parallel processing for computationally intensive tasks"
    )
    
    parser.add_argument(
        "--num-workers",
        type=int,
        default=max(1, multiprocessing.cpu_count() - 1),  # Use all but one CPU cores
        help="Number of parallel workers to use"
    )
    
    parser.add_argument(
        "--skip-steps",
        type=str,
        default="",
        help="Comma-separated list of steps to skip (e.g. 'temporal,symbolic,equity')"
    )
    
    parser.add_argument(
        "--cache",
        action="store_true",
        default=True, 
        help="Use cached results when available"
    )
    
    return parser.parse_args()

# Helper functions for parallelization
def run_domain_analysis(G, partition, output_dir):
    """Run domain-specific analyses in parallel."""
    # Transport efficiency
    efficiency_analyzer = TransportEfficiencyAnalyzer(G, partition)
    efficiency_metrics = efficiency_analyzer.calculate_efficiency_metrics()
    connection_quality = efficiency_analyzer.analyze_connection_quality()
    community_accessibility = efficiency_analyzer.analyze_community_accessibility()
    
    # Save efficiency analysis
    with open(os.path.join(output_dir, "efficiency_metrics.pkl"), "wb") as f:
        pickle.dump(efficiency_metrics, f)
    
    with open(os.path.join(output_dir, "connection_quality.pkl"), "wb") as f:
        pickle.dump(connection_quality, f)
    
    with open(os.path.join(output_dir, "community_accessibility.pkl"), "wb") as f:
        pickle.dump(community_accessibility, f)
    
    return {
        'efficiency_metrics': efficiency_metrics,
        'connection_quality': connection_quality,
        'community_accessibility': community_accessibility
    }

def run_equity_analysis(G, partition, output_dir):
    """Run equity analysis in parallel."""
    # Equity analysis
    equity_analyzer = EquityAnalyzer(G, partition)
    service_distribution = equity_analyzer.analyze_service_distribution()
    accessibility_equity = equity_analyzer.analyze_accessibility_equity()
    equity_gaps = equity_analyzer.identify_equity_gaps()
    
    # Save equity analysis
    with open(os.path.join(output_dir, "service_distribution.pkl"), "wb") as f:
        pickle.dump(service_distribution, f)
    
    with open(os.path.join(output_dir, "accessibility_equity.pkl"), "wb") as f:
        pickle.dump(accessibility_equity, f)
    
    with open(os.path.join(output_dir, "equity_gaps.pkl"), "wb") as f:
        pickle.dump(equity_gaps, f)
    
    return {
        'service_distribution': service_distribution,
        'accessibility_equity': accessibility_equity,
        'equity_gaps': equity_gaps
    }

def run_temporal_analysis(gtfs_data, output_dir):
    """Run temporal analysis in parallel."""
    temporal_analyzer = TemporalNetworkAnalyzer(gtfs_data)
    hourly_patterns = temporal_analyzer.analyze_hourly_patterns()
    weekly_patterns = temporal_analyzer.analyze_weekly_patterns()
    
    # Save temporal analysis
    with open(os.path.join(output_dir, "hourly_patterns.pkl"), "wb") as f:
        pickle.dump(hourly_patterns, f)
    
    with open(os.path.join(output_dir, "weekly_patterns.pkl"), "wb") as f:
        pickle.dump(weekly_patterns, f)
    
    return {
        'hourly_patterns': hourly_patterns,
        'weekly_patterns': weekly_patterns
    }

def run_symbolic_analysis(G, partition, critical_nodes, output_dir):
    """Run symbolic AI analysis in parallel."""
    # Basic knowledge base
    kb_creator = TransportKnowledgeBase(G, partition)
    kb = kb_creator.create_knowledge_base(max_critical_nodes=50)
    
    # Save knowledge base
    with open(os.path.join(output_dir, "knowledge_base.pkl"), "wb") as f:
        pickle.dump(kb, f)
    
    # Advanced reasoning
    adv_reasoning = AdvancedTransportReasoning(G, partition, critical_nodes)
    adv_kb = adv_reasoning.create_advanced_knowledge_base()
    
    # Perform reasoning tasks
    reasoning_results = adv_reasoning.perform_advanced_reasoning()
    with open(os.path.join(output_dir, "advanced_reasoning_results.pkl"), "wb") as f:
        pickle.dump(reasoning_results, f)
    
    return {
        'knowledge_base': kb,
        'advanced_kb': adv_kb,
        'reasoning_results': reasoning_results
    }

def main():
    """Main entry point for analysis."""
    start_time = time.time()
    
    # Parse arguments
    args = parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Create visualizations directory if visualize flag is set
    if args.visualize:
        os.makedirs("visualizations", exist_ok=True)
    
    # Parse steps to skip
    skip_steps = [step.strip() for step in args.skip_steps.split(',') if step.strip()]
    
    # Step 1: Load GTFS data
    logger.info("Step 1: Loading GTFS data")
    cache_file = os.path.join(args.output_dir, "gtfs_data_cache.pkl")
    
    if args.cache and os.path.exists(cache_file) and not args.force_download:
        logger.info("Using cached GTFS data")
        with open(cache_file, "rb") as f:
            gtfs_data = pickle.load(f)
    else:
        loader = EnhancedGTFSLoader(args.gtfs_url, args.data_dir)
        gtfs_data = loader.process(force_download=args.force_download)
        
        # Cache the data
        with open(cache_file, "wb") as f:
            pickle.dump(gtfs_data, f)
    
    # Step 2: Build graph
    logger.info("Step 2: Building transport network graph")
    graph_cache_file = os.path.join(args.output_dir, "graph_cache.pkl")
    
    if args.cache and os.path.exists(graph_cache_file) and not args.force_download:
        logger.info("Using cached graph")
        with open(graph_cache_file, "rb") as f:
            cache_data = pickle.load(f)
            G = cache_data['graph']
            graph_stats = cache_data['stats']
    else:
        builder = TransportGraphBuilder(gtfs_data)
        G = builder.build_graph(sample_size=args.sample_size)
        
        # Enhance geocoding if requested
        if args.enhance_geocoding:
            logger.info("Enhancing node coordinates with geocoding")
            enhanced = enhance_node_coordinates(G, region="Manchester, UK")
            logger.info(f"Enhanced {enhanced} node coordinates")
        
        # Optimize graph if requested
        if args.optimize:
            logger.info("Optimizing graph for memory usage")
            G = optimize_graph_for_memory(G)
        
        # Save graph statistics
        graph_stats = builder.get_graph_stats()
        
        # Cache the graph and stats
        with open(graph_cache_file, "wb") as f:
            pickle.dump({'graph': G, 'stats': graph_stats}, f)
    
    # Save graph statistics
    with open(os.path.join(args.output_dir, "graph_stats.pkl"), "wb") as f:
        pickle.dump(graph_stats, f)
    
    # Step 3: Detect communities
    logger.info("Step 3: Detecting communities")
    communities_cache_file = os.path.join(args.output_dir, "communities_cache.pkl")
    
    if args.cache and os.path.exists(communities_cache_file):
        logger.info("Using cached community detection results")
        with open(communities_cache_file, "rb") as f:
            cache_data = pickle.load(f)
            partition = cache_data['partition']
            community_analysis = cache_data['analysis']
    else:
        detector = CommunityDetector(G)
        partition = detector.detect_communities_louvain()
        
        # Analyze communities
        community_analysis = detector.analyze_communities()
        
        # Cache the results
        with open(communities_cache_file, "wb") as f:
            pickle.dump({'partition': partition, 'analysis': community_analysis}, f)
    
    # Save partition
    with open(os.path.join(args.output_dir, "communities_partition.pkl"), "wb") as f:
        pickle.dump(partition, f)
    
    # Save community analysis
    with open(os.path.join(args.output_dir, "community_analysis.pkl"), "wb") as f:
        pickle.dump(community_analysis, f)
    
    # Step 4: Identify critical nodes
    logger.info("Step 4: Identifying critical nodes")
    critical_nodes_cache_file = os.path.join(args.output_dir, "critical_nodes_cache.pkl")
    
    if args.cache and os.path.exists(critical_nodes_cache_file):
        logger.info("Using cached critical nodes results")
        with open(critical_nodes_cache_file, "rb") as f:
            cache_data = pickle.load(f)
            critical_nodes = cache_data['nodes']
            critical_nodes_df = cache_data['df']
            vulnerability_analysis = cache_data['vulnerability']
    else:
        node_analyzer = CriticalNodeAnalyzer(G, partition)
        critical_nodes = node_analyzer.identify_critical_nodes(top_n=30)
        
        # Analyze critical nodes
        critical_nodes_df = node_analyzer.analyze_critical_nodes(critical_nodes)
        
        # Assess vulnerabilities with parallelization if enabled
        vulnerability_analysis = node_analyzer.assess_vulnerability(
            critical_nodes, 
            parallel=args.parallel, 
            max_workers=args.num_workers
        )
        
        # Cache the results
        with open(critical_nodes_cache_file, "wb") as f:
            pickle.dump({
                'nodes': critical_nodes, 
                'df': critical_nodes_df, 
                'vulnerability': vulnerability_analysis
            }, f)
    
    # Save critical nodes analysis
    critical_nodes_df.to_csv(os.path.join(args.output_dir, "critical_nodes.csv"), index=False)
    
    # Save vulnerability analysis
    with open(os.path.join(args.output_dir, "vulnerability_analysis.pkl"), "wb") as f:
        pickle.dump(vulnerability_analysis, f)
    
    # Set up parallel tasks for the remaining steps
    parallel_tasks = []
    
    # Step 5: Symbolic AI analysis (if not skipped)
    if 'symbolic' not in skip_steps:
        logger.info("Step 5: Preparing symbolic AI analysis")
        if args.parallel:
            symbolic_task = ('symbolic', G, partition, critical_nodes, args.output_dir)
            parallel_tasks.append(symbolic_task)
        else:
            logger.info("Running symbolic AI analysis sequentially")
            run_symbolic_analysis(G, partition, critical_nodes, args.output_dir)
    else:
        logger.info("Skipping symbolic AI analysis")
    
    # Step 6: Temporal patterns analysis (if not skipped)
    if 'temporal' not in skip_steps:
        logger.info("Step 6: Preparing temporal patterns analysis")
        if args.parallel:
            temporal_task = ('temporal', gtfs_data, args.output_dir)
            parallel_tasks.append(temporal_task)
        else:
            logger.info("Running temporal analysis sequentially")
            run_temporal_analysis(gtfs_data, args.output_dir)
    else:
        logger.info("Skipping temporal patterns analysis")
    
    # Step 7: Domain-specific analysis (if not skipped)
    if 'domain' not in skip_steps:
        logger.info("Step 7: Preparing domain-specific analysis")
        if args.parallel:
            domain_task = ('domain', G, partition, args.output_dir)
            parallel_tasks.append(domain_task)
        else:
            logger.info("Running domain analysis sequentially")
            run_domain_analysis(G, partition, args.output_dir)
    else:
        logger.info("Skipping domain analysis")
    
    # Run equity analysis (if not skipped)
    if 'equity' not in skip_steps:
        logger.info("Preparing equity analysis")
        if args.parallel:
            equity_task = ('equity', G, partition, args.output_dir)
            parallel_tasks.append(equity_task)
        else:
            logger.info("Running equity analysis sequentially")
            run_equity_analysis(G, partition, args.output_dir)
    else:
        logger.info("Skipping equity analysis")
    
    # Execute parallel tasks if there are any
    if parallel_tasks and args.parallel:
        logger.info(f"Running {len(parallel_tasks)} tasks in parallel with {args.num_workers} workers")
        
        with ProcessPoolExecutor(max_workers=min(len(parallel_tasks), args.num_workers)) as executor:
            futures = []
            
            for task in parallel_tasks:
                task_type = task[0]
                task_args = task[1:]
                
                if task_type == 'symbolic':
                    futures.append(executor.submit(run_symbolic_analysis, *task_args))
                elif task_type == 'temporal':
                    futures.append(executor.submit(run_temporal_analysis, *task_args))
                elif task_type == 'domain':
                    futures.append(executor.submit(run_domain_analysis, *task_args))
                elif task_type == 'equity':
                    futures.append(executor.submit(run_equity_analysis, *task_args))
            
            # Wait for all tasks to complete
            for i, future in enumerate(futures):
                try:
                    result = future.result()
                    logger.info(f"Completed parallel task {i+1}/{len(futures)}")
                except Exception as e:
                    logger.error(f"Error in parallel task {i+1}: {str(e)}")
    
    # Step 8: Generate visualizations if requested
    if args.visualize:
        logger.info("Step 8: Generating visualizations")
        
        # Create visualizer
        visualizer = NetworkVisualizer(G, partition)
        
        # Generate community map
        logger.info("Generating community map")
        visualizer.create_community_map(output_file="visualizations/communities.png")
        
        # Generate critical nodes visualization
        logger.info("Generating critical nodes visualization")
        visualizer.create_critical_nodes_visualization(
            critical_nodes, 
            output_file="visualizations/critical_nodes.png"
        )
        
        # Generate interactive network visualization
        logger.info("Generating interactive network visualization")
        interactive_network = visualizer.create_interactive_network(critical_nodes)
        with open("visualizations/interactive_network.html", "w") as f:
            f.write(interactive_network.to_html())
        
        # Generate transport density heatmap
        logger.info("Generating transport density heatmap")
        density_heatmap = visualizer.create_transport_density_heatmap()
        with open("visualizations/density_heatmap.html", "w") as f:
            f.write(density_heatmap.to_html())
        
        # Generate community network visualization
        logger.info("Generating community network visualization")
        community_network = visualizer.create_community_network_visualization()
        with open("visualizations/community_network.html", "w") as f:
            f.write(community_network.to_html())
    
    # Calculate total time
    end_time = time.time()
    total_time = end_time - start_time
    
    logger.info(f"Analysis completed in {total_time:.2f} seconds")
    logger.info(f"Results saved to {args.output_dir}")

if __name__ == "__main__":
    main()