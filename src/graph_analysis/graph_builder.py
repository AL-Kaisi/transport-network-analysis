"""
Graph builder module.
Converts GTFS data into a NetworkX graph for further analysis.
"""

import networkx as nx
import pandas as pd
from typing import Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TransportGraphBuilder:
    """Class for building a graph from GTFS data."""
    
    def __init__(self, gtfs_data: Dict[str, pd.DataFrame]):
        """
        Initialize the graph builder.
        
        Args:
            gtfs_data: Dictionary mapping GTFS file names to pandas DataFrames
        """
        self.gtfs_data = gtfs_data
        self.graph = nx.Graph()
        
    def build_graph(self, sample_size: Optional[int] = None) -> nx.Graph:
        """
        Build a graph from GTFS data.
        
        Args:
            sample_size: Optional number of trips to sample for graph construction.
                         If None, all trips are used.
        
        Returns:
            NetworkX graph representing the transport network
        """
        logger.info("Building transport network graph")
        
        # Extract needed dataframes
        stops_df = self.gtfs_data["stops"]
        routes_df = self.gtfs_data["routes"]
        trips_df = self.gtfs_data["trips"]
        stop_times_df = self.gtfs_data["stop_times"]
        
        # Add stops as nodes
        for _, stop in stops_df.iterrows():
            self.graph.add_node(
                stop['stop_id'], 
                type='stop', 
                name=stop['stop_name'],
                lat=float(stop['stop_lat']),
                lon=float(stop['stop_lon'])
            )
        
        logger.info(f"Added {len(stops_df)} stops as nodes")
        
        # Process stop times to find connections
        # Sample trips if specified
        if sample_size is not None and sample_size < len(trips_df):
            logger.info(f"Sampling {sample_size} trips from {len(trips_df)} total trips")
            sampled_trips_df = trips_df.sample(sample_size)
            trip_ids = sampled_trips_df['trip_id'].tolist()
        else:
            trip_ids = trips_df['trip_id'].tolist()
            
        # Process trips
        trips_processed = 0
        edges_added = 0
        
        for trip_id in trip_ids:
            # Get stop sequence for this trip
            trip_stops = stop_times_df[stop_times_df['trip_id'] == trip_id].sort_values('stop_sequence')
            
            if len(trip_stops) <= 1:
                continue
                
            # Get route info
            trip_info = trips_df[trips_df['trip_id'] == trip_id]
            if len(trip_info) == 0:
                continue
                
            route_id = trip_info.iloc[0]['route_id']
            route_info = routes_df[routes_df['route_id'] == route_id]
            
            if len(route_info) == 0:
                continue
                
            route_type = route_info.iloc[0]['route_type']
            
            # Connect consecutive stops
            stop_ids = trip_stops['stop_id'].tolist()
            for i in range(len(stop_ids) - 1):
                source = stop_ids[i]
                target = stop_ids[i + 1]
                
                # Skip if nodes don't exist (some GTFS datasets have inconsistencies)
                if source not in self.graph or target not in self.graph:
                    continue
                
                # Add the edge or update attributes if it already exists
                if self.graph.has_edge(source, target):
                    # If the edge exists, increment a count attribute
                    self.graph[source][target]['trips'] = self.graph[source][target].get('trips', 0) + 1
                else:
                    # Add new edge
                    self.graph.add_edge(
                        source, 
                        target,
                        trip_id=trip_id,
                        route_id=route_id,
                        route_type=int(route_type),
                        trips=1
                    )
                    edges_added += 1
            
            trips_processed += 1
            
            # Status update every 100 trips
            if trips_processed % 100 == 0:
                logger.info(f"Processed {trips_processed}/{len(trip_ids)} trips, added {edges_added} edges")
        
        # Remove isolated nodes (stops that aren't connected)
        isolated_nodes = list(nx.isolates(self.graph))
        self.graph.remove_nodes_from(isolated_nodes)
        
        logger.info(f"Graph construction complete")
        logger.info(f"Final graph has {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
        logger.info(f"Removed {len(isolated_nodes)} isolated stops")
        
        return self.graph
    
    def get_graph_stats(self) -> Dict:
        """
        Get basic statistics about the graph.
        
        Returns:
            Dictionary with graph statistics
        """
        if not self.graph or self.graph.number_of_nodes() == 0:
            raise ValueError("Graph has not been built yet or is empty")
            
        stats = {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "connected_components": nx.number_connected_components(self.graph),
            "avg_degree": sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes()
        }
        
        # Add largest component size if there are any connected components
        if stats["connected_components"] > 0:
            largest_cc = max(nx.connected_components(self.graph), key=len)
            stats["largest_component_size"] = len(largest_cc)
            stats["largest_component_ratio"] = len(largest_cc) / stats["num_nodes"]
        
        return stats