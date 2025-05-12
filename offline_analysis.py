"""
Transport Network Analysis - Offline version
This script creates a static HTML report instead of running a live server
"""

import os
import time
import logging
import sys
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import base64
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def run_analysis(sample_size=500):
    """Run the complete analysis and return results"""
    start_time = time.time()
    results = {}
    
    try:
        # Import modules
        from src.data_processing.gtfs_loader import EnhancedGTFSLoader as GTFSLoader
        from src.graph_analysis.graph_builder import TransportGraphBuilder
        from src.graph_analysis.community_detection import CommunityDetector
        
        # Get configuration
        gtfs_url = os.getenv("GTFS_URL")
        data_dir = os.getenv("DATA_DIR")
        
        logger.info(f"Starting analysis with sample size {sample_size}")
        
        # 1. Load GTFS data
        logger.info("Loading GTFS data...")
        loader = GTFSLoader(gtfs_url, data_dir)
        
        if not os.path.exists(os.path.join(data_dir, "stops.txt")):
            logger.info("Downloading GTFS data...")
            gtfs_data = loader.process()
        else:
            logger.info("Loading existing GTFS data...")
            gtfs_data = loader.load_data()
        
        # 2. Build graph
        logger.info(f"Building graph with sample size {sample_size}...")
        builder = TransportGraphBuilder(gtfs_data)
        graph = builder.build_graph(sample_size=sample_size)
        
        stats = {
            "num_nodes": graph.number_of_nodes(),
            "num_edges": graph.number_of_edges(),
            "density": nx.density(graph),
            "connected_components": nx.number_connected_components(graph)
        }
        results["graph_stats"] = stats
        
        # 3. Detect communities
        logger.info("Detecting communities...")
        detector = CommunityDetector(graph)
        partition = detector.detect_communities_louvain()
        
        # 4. Analyze communities
        logger.info("Analyzing communities...")
        community_analysis = detector.analyze_communities()
        
        # Create community dataframe
        community_data = []
        for comm_id, comm_data in community_analysis["communities"].items():
            community_data.append({
                "community_id": comm_id,
                "size": comm_data["size"],
                "density": comm_data["density"],
                "avg_degree": comm_data["avg_degree"]
            })
        community_df = pd.DataFrame(community_data)
        results["community_df"] = community_df
        
        # 5. Identify critical nodes
        logger.info("Identifying critical nodes...")
        critical_nodes = detector.identify_critical_nodes(top_n=20)
        
        # Create critical nodes dataframe
        critical_nodes_data = []
        for node_id, score in critical_nodes:
            node_data = graph.nodes[node_id]
            critical_nodes_data.append({
                "node_id": node_id,
                "name": node_data.get("name", f"Stop_{node_id}"),
                "community": partition[node_id],
                "centrality": score,
                "degree": graph.degree[node_id]
            })
        critical_df = pd.DataFrame(critical_nodes_data)
        results["critical_df"] = critical_df
        
        # 6. Create visualizations
        logger.info("Creating visualizations...")
        vis_path = "visualizations"
        if not os.path.exists(vis_path):
            os.makedirs(vis_path)
            
        # Create community visualization
        detector.visualize_communities(output_file=os.path.join(vis_path, "communities.png"))
        
        # Calculate execution time
        execution_time = time.time() - start_time
        results["execution_time"] = execution_time
        logger.info(f"Analysis completed in {execution_time:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        results["error"] = str(e)
    
    return results

def create_html_report(results):
    """Create an HTML report from the analysis results"""
    
    if "error" in results:
        html = f"""
        <html>
        <head>
            <title>Transport Network Analysis - Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .error {{ color: red; background-color: #ffeeee; padding: 10px; border: 1px solid #ffcccc; }}
            </style>
        </head>
        <body>
            <h1>Transport Network Analysis - Error</h1>
            <div class="error">
                <h2>Error During Analysis</h2>
                <p>{results['error']}</p>
            </div>
        </body>
        </html>
        """
        return html
    
    # Read the community visualization as base64
    try:
        with open("visualizations/communities.png", "rb") as f:
            communities_img = base64.b64encode(f.read()).decode("utf-8")
    except:
        communities_img = ""
    
    # Format the community table
    community_table = results["community_df"].to_html(index=False, 
                                                     classes="table table-striped",
                                                     float_format="%.4f")
    
    # Format the critical nodes table
    critical_table = results["critical_df"].to_html(index=False, 
                                                  classes="table table-striped",
                                                  float_format="%.6f")
    
    # Create the HTML report
    html = f"""
    <html>
    <head>
        <title>Transport Network Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .section {{ margin-bottom: 30px; padding: 15px; border: 1px solid #ddd; }}
            .stats {{ display: flex; flex-wrap: wrap; }}
            .stat-box {{ width: 200px; padding: 10px; margin: 10px; background-color: #f5f5f5; border: 1px solid #ddd; }}
            table {{ border-collapse: collapse; width: 100%; }}
            table, th, td {{ border: 1px solid #ddd; }}
            th, td {{ padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .visualization {{ margin-top: 20px; text-align: center; }}
        </style>
    </head>
    <body>
        <h1>Transport Network Analysis Report</h1>
        <p>Analysis completed in {results['execution_time']:.2f} seconds</p>
        
        <div class="section">
            <h2>Network Overview</h2>
            <div class="stats">
                <div class="stat-box">
                    <h3>Nodes</h3>
                    <p>{results['graph_stats']['num_nodes']}</p>
                </div>
                <div class="stat-box">
                    <h3>Edges</h3>
                    <p>{results['graph_stats']['num_edges']}</p>
                </div>
                <div class="stat-box">
                    <h3>Density</h3>
                    <p>{results['graph_stats']['density']:.6f}</p>
                </div>
                <div class="stat-box">
                    <h3>Connected Components</h3>
                    <p>{results['graph_stats']['connected_components']}</p>
                </div>
                <div class="stat-box">
                    <h3>Communities</h3>
                    <p>{len(results['community_df'])}</p>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Communities</h2>
            {community_table}
            
            <div class="visualization">
                <h3>Community Visualization</h3>
                <img src="data:image/png;base64,{communities_img}" style="max-width: 100%;" />
            </div>
        </div>
        
        <div class="section">
            <h2>Critical Nodes</h2>
            {critical_table}
        </div>
    </body>
    </html>
    """
    
    return html

def main():
    """Main function to run analysis and create HTML report"""
    # Run the analysis with a small sample size
    logger.info("Starting transport network analysis")
    results = run_analysis(sample_size=200)
    
    # Create HTML report
    logger.info("Creating HTML report")
    html_report = create_html_report(results)
    
    # Save HTML report
    report_path = "transport_network_report.html"
    with open(report_path, "w") as f:
        f.write(html_report)
    
    logger.info(f"HTML report saved to {report_path}")
    print(f"\nAnalysis complete! Open {report_path} in your web browser to view the results.")

if __name__ == "__main__":
    main()