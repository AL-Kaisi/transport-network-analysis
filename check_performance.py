"""
Diagnostic script to identify bottlenecks in the transport network analysis.
This script will time each component of the analysis to determine which parts are slow.
"""

import os
import time
import logging
import sys

# Set up logging to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Loaded environment variables from .env")
except ImportError:
    logger.warning("Could not import dotenv. Using environment variables as is.")

def time_function(func, *args, **kwargs):
    """Time the execution of a function."""
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    return result, end_time - start_time

def main():
    # Add the current directory to sys.path to ensure imports work
    sys.path.insert(0, os.path.abspath('.'))
    
    logger.info("Starting performance check")
    
    # 1. Test GTFS data loading
    try:
        logger.info("Testing GTFS data loading...")
        from src.data_processing.gtfs_loader import GTFSLoader
        
        gtfs_url = os.getenv("GTFS_URL")
        data_dir = os.getenv("DATA_DIR")
        
        if not gtfs_url or not data_dir:
            logger.error("GTFS_URL or DATA_DIR environment variables not set")
            return
            
        logger.info(f"GTFS URL: {gtfs_url}")
        logger.info(f"Data directory: {data_dir}")
        
        loader = GTFSLoader(gtfs_url, data_dir)
        
        # Check if data already exists
        if os.path.exists(os.path.join(data_dir, "stops.txt")):
            logger.info("GTFS data already exists locally, loading...")
            gtfs_data, loading_time = time_function(loader.load_data)
            logger.info(f"GTFS data loading took: {loading_time:.2f} seconds")
        else:
            logger.info("GTFS data doesn't exist locally, downloading...")
            gtfs_data, processing_time = time_function(loader.process)
            logger.info(f"GTFS data download and processing took: {processing_time:.2f} seconds")
            
        # Log some data stats
        for file_name, df in gtfs_data.items():
            logger.info(f"  {file_name}: {len(df)} rows")
    except Exception as e:
        logger.error(f"Error in GTFS data loading: {str(e)}")
        return
        
    # 2. Test graph building
    try:
        logger.info("Testing graph building...")
        from src.graph_analysis.graph_builder import TransportGraphBuilder
        
        builder = TransportGraphBuilder(gtfs_data)
        
        # Build graph with sample
        logger.info("Building graph with 500 samples...")
        G_small, small_time = time_function(builder.build_graph, 500)
        logger.info(f"Graph building with 500 samples took: {small_time:.2f} seconds")
        logger.info(f"Graph has {G_small.number_of_nodes()} nodes and {G_small.number_of_edges()} edges")
        
        # Try with larger sample if first one was fast
        if small_time < 10:
            logger.info("Building graph with 1000 samples...")
            G, larger_time = time_function(builder.build_graph, 1000)
            logger.info(f"Graph building with 1000 samples took: {larger_time:.2f} seconds")
            logger.info(f"Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        else:
            G = G_small
    except Exception as e:
        logger.error(f"Error in graph building: {str(e)}")
        return
        
    # 3. Test community detection
    try:
        logger.info("Testing community detection...")
        from src.graph_analysis.community_detection import CommunityDetector
        
        detector = CommunityDetector(G)
        
        # Detect communities
        logger.info("Detecting communities...")
        partition, detection_time = time_function(detector.detect_communities_louvain)
        logger.info(f"Community detection took: {detection_time:.2f} seconds")
        
        # Analyze communities
        logger.info("Analyzing communities...")
        community_analysis, analysis_time = time_function(detector.analyze_communities)
        logger.info(f"Community analysis took: {analysis_time:.2f} seconds")
        
        # Identify critical nodes
        logger.info("Identifying critical nodes...")
        critical_nodes, critical_time = time_function(detector.identify_critical_nodes, 20)
        logger.info(f"Critical nodes identification took: {critical_time:.2f} seconds")
    except Exception as e:
        logger.error(f"Error in community detection: {str(e)}")
        return
        
    # 4. Test symbolic AI (if it's slow)
    try:
        logger.info("Testing symbolic AI...")
        from src.symbolic_ai.knowledge_base import TransportKnowledgeBase
        
        kb_creator = TransportKnowledgeBase(G, partition)
        
        # Create knowledge base
        logger.info("Creating knowledge base...")
        kb, kb_time = time_function(kb_creator.create_knowledge_base)
        logger.info(f"Knowledge base creation took: {kb_time:.2f} seconds")
        
        # Perform symbolic reasoning
        logger.info("Performing symbolic reasoning...")
        symbolic_results, reasoning_time = time_function(kb_creator.perform_symbolic_reasoning, critical_nodes)
        logger.info(f"Symbolic reasoning took: {reasoning_time:.2f} seconds")
    except Exception as e:
        logger.error(f"Error in symbolic AI: {str(e)}")
        
    # 5. Test visualization
    try:
        logger.info("Testing visualization...")
        
        # Test community visualization
        logger.info("Visualizing communities...")
        vis_time_start = time.time()
        detector.visualize_communities("test_communities.png")
        vis_time = time.time() - vis_time_start
        logger.info(f"Community visualization took: {vis_time:.2f} seconds")
    except Exception as e:
        logger.error(f"Error in visualization: {str(e)}")
    
    logger.info("Performance check complete")
    logger.info("Summary of bottlenecks (ordered by time):")
    
    # Create a summary of all timed operations
    timings = [
        ("GTFS data loading/processing", loading_time if 'loading_time' in locals() else processing_time if 'processing_time' in locals() else 0),
        ("Graph building", larger_time if 'larger_time' in locals() else small_time if 'small_time' in locals() else 0),
        ("Community detection", detection_time if 'detection_time' in locals() else 0),
        ("Community analysis", analysis_time if 'analysis_time' in locals() else 0),
        ("Critical nodes identification", critical_time if 'critical_time' in locals() else 0),
        ("Knowledge base creation", kb_time if 'kb_time' in locals() else 0),
        ("Symbolic reasoning", reasoning_time if 'reasoning_time' in locals() else 0),
        ("Visualization", vis_time if 'vis_time' in locals() else 0)
    ]
    
    # Sort by time
    timings.sort(key=lambda x: x[1], reverse=True)
    
    # Display results
    for operation, time_taken in timings:
        if time_taken > 0:
            logger.info(f"  {operation}: {time_taken:.2f} seconds")

if __name__ == "__main__":
    main()