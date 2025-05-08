"""
Temporal analysis of transport networks.
Analyze how the network changes throughout the day and week.
"""

import pandas as pd
import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class TemporalNetworkAnalyzer:
    """Class for temporal analysis of transport networks."""
    
    def __init__(self, gtfs_data: Dict[str, pd.DataFrame]):
        """
        Initialize the temporal network analyzer.
        
        Args:
            gtfs_data: Dictionary of GTFS DataFrames
        """
        self.gtfs_data = gtfs_data
        
    def analyze_hourly_patterns(self) -> Dict[str, Any]:
        """
        Analyze how the network changes by hour of day.
        
        Returns:
            Dictionary with hourly analysis results
        """
        logger.info("Analyzing hourly network patterns")
        
        # Extract necessary data
        stop_times_df = self.gtfs_data['stop_times']
        trips_df = self.gtfs_data['trips']
        
        # Check if we have the necessary time columns
        if 'departure_time_seconds' not in stop_times_df.columns:
            logger.warning("No departure_time_seconds column, extracting time from departure_time")
            # Try to convert departure_time to seconds
            if 'departure_time' in stop_times_df.columns:
                stop_times_df['departure_time_seconds'] = stop_times_df['departure_time'].apply(
                    lambda x: self._time_to_seconds(x) if pd.notna(x) else None
                )
            else:
                logger.error("No departure_time column, cannot analyze hourly patterns")
                return {'error': 'No departure time data available'}
        
        # Convert seconds to hours (0-23)
        stop_times_df['hour'] = stop_times_df['departure_time_seconds'].apply(
            lambda x: (x // 3600) % 24 if pd.notna(x) else None
        )
        
        # Count departures by hour
        hourly_departures = stop_times_df.groupby('hour').size()
        
        # Calculate trips per hour (unique trip_ids)
        hourly_trips = stop_times_df.groupby('hour')['trip_id'].nunique()
        
        # Create a dictionary to store hourly subgraphs
        hourly_graphs = {}
        
        # Create graph for each hour with sufficient data (sample for efficiency)
        sample_hours = [7, 12, 17, 22]  # Morning, noon, evening, night
        
        for hour in sample_hours:
            # Get stop times for this hour
            hour_stop_times = stop_times_df[stop_times_df['hour'] == hour]
            
            # Skip if not enough data
            if len(hour_stop_times) < 100:
                logger.warning(f"Not enough data for hour {hour}, skipping")
                continue
                
            # Get unique trip IDs for this hour
            hour_trips = hour_stop_times['trip_id'].unique()
            
            # Sample trips for efficiency if there are too many
            if len(hour_trips) > 1000:
                hour_trips = np.random.choice(hour_trips, 1000, replace=False)
                
            # Filter stop times for sampled trips
            hour_stop_times = hour_stop_times[hour_stop_times['trip_id'].isin(hour_trips)]
            
            # Build graph for this hour
            G = nx.Graph()
            
            # Add stops as nodes
            stops_df = self.gtfs_data['stops']
            for _, stop in stops_df.iterrows():
                # Only add stops that are used during this hour
                if stop['stop_id'] in hour_stop_times['stop_id'].values:
                    G.add_node(
                        stop['stop_id'], 
                        type='stop', 
                        name=stop['stop_name'],
                        lat=float(stop['stop_lat']),
                        lon=float(stop['stop_lon'])
                    )
            
            # Connect stops based on trips during this hour
            for trip_id in hour_trips:
                trip_stops = hour_stop_times[hour_stop_times['trip_id'] == trip_id].sort_values('stop_sequence')
                
                if len(trip_stops) <= 1:
                    continue
                    
                # Connect consecutive stops
                stop_ids = trip_stops['stop_id'].tolist()
                for i in range(len(stop_ids) - 1):
                    source = stop_ids[i]
                    target = stop_ids[i + 1]
                    
                    # Add the edge if both nodes exist
                    if G.has_node(source) and G.has_node(target):
                        if G.has_edge(source, target):
                            # Increment a count attribute
                            G[source][target]['trips'] = G[source][target].get('trips', 0) + 1
                        else:
                            # Add new edge
                            G.add_edge(
                                source, 
                                target,
                                trip_id=trip_id,
                                trips=1
                            )
            
            # Store the graph
            hourly_graphs[hour] = G
            logger.info(f"Built graph for hour {hour}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        
        # Analyze network properties by hour
        hourly_properties = {}
        for hour, G in hourly_graphs.items():
            # Skip empty graphs
            if G.number_of_nodes() == 0:
                continue
                
            # Calculate basic graph metrics
            hourly_properties[hour] = {
                'nodes': G.number_of_nodes(),
                'edges': G.number_of_edges(),
                'density': nx.density(G),
            }
            
            # Calculate more complex metrics for connected components
            largest_cc = max(nx.connected_components(G), key=len)
            largest_G = G.subgraph(largest_cc)
            
            try:
                hourly_properties[hour]['avg_path_length'] = nx.average_shortest_path_length(largest_G)
            except:
                hourly_properties[hour]['avg_path_length'] = None
            
            hourly_properties[hour]['clustering_coefficient'] = nx.average_clustering(largest_G)
        
        return {
            'hourly_departures': hourly_departures.to_dict(),
            'hourly_trips': hourly_trips.to_dict(),
            'hourly_graphs': hourly_graphs,
            'hourly_properties': hourly_properties
        }
    
    def analyze_weekly_patterns(self) -> Dict[str, Any]:
        """
        Analyze how the network changes by day of week.
        
        Returns:
            Dictionary with weekly analysis results
        """
        logger.info("Analyzing weekly network patterns")
        
        # Check if calendar data is available
        if 'calendar' not in self.gtfs_data:
            logger.warning("No calendar data available, cannot analyze weekly patterns")
            return {'error': 'No calendar data available'}
            
        calendar_df = self.gtfs_data['calendar']
        trips_df = self.gtfs_data['trips']
        
        # Get service IDs for each day of the week
        weekday_columns = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        # Count trips by day of week
        day_trips = {}
        for i, day in enumerate(weekday_columns):
            # Get service IDs that operate on this day
            day_services = calendar_df[calendar_df[day] == 1]['service_id'].tolist()
            
            # Count trips on this day
            day_trips[day] = len(trips_df[trips_df['service_id'].isin(day_services)])
        
        # Calculate service level ratio (weekday vs weekend)
        weekday_services = sum([day_trips[day] for day in weekday_columns[:5]])
        weekend_services = sum([day_trips[day] for day in weekday_columns[5:]])
        
        if weekend_services > 0:
            weekday_weekend_ratio = weekday_services / (5 * (weekend_services / 2))
        else:
            weekday_weekend_ratio = float('inf')
        
        return {
            'day_trips': day_trips,
            'weekday_services': weekday_services,
            'weekend_services': weekend_services,
            'weekday_weekend_ratio': weekday_weekend_ratio
        }
    
    @staticmethod
    def _time_to_seconds(time_str):
        """Convert time string to seconds past midnight."""
        if pd.isna(time_str):
            return None
        
        try:
            parts = time_str.split(':')
            if len(parts) != 3:
                return None
                
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        except:
            return None