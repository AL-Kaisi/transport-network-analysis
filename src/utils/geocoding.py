"""
Geocoding utilities for enhancing geographic data.
"""

import requests
import time
import json
import os
from typing import Dict, Any, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def geocode_location(location_name: str, region: str = "uk") -> Optional[Dict[str, float]]:
    """
    Geocode a location name to coordinates using Nominatim.
    
    Args:
        location_name: Name of the location to geocode
        region: Region to focus search in
        
    Returns:
        Dictionary with lat/lon or None if geocoding failed
    """
    logger.info(f"Geocoding location: {location_name}")
    
    # Format query
    query = f"{location_name}, {region}"
    url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json"
    
    # Make request with proper headers and rate limiting
    headers = {
        'User-Agent': 'TransportNetworkAnalysis/1.0'
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            results = response.json()
            
            if results:
                # Get first result
                result = results[0]
                
                coords = {
                    'lat': float(result['lat']),
                    'lon': float(result['lon'])
                }
                
                logger.info(f"Geocoded {location_name} to {coords['lat']}, {coords['lon']}")
                return coords
            else:
                logger.warning(f"No results found for {location_name}")
        else:
            logger.error(f"Geocoding request failed with status code {response.status_code}")
    except Exception as e:
        logger.error(f"Error geocoding {location_name}: {e}")
    
    # Be nice to the API - respect rate limits
    time.sleep(1)
    
    return None

def batch_geocode(location_names: List[str], 
                 region: str = "uk",
                 cache_file: str = "geocode_cache.json") -> Dict[str, Dict[str, float]]:
    """
    Geocode a batch of location names with caching.
    
    Args:
        location_names: List of location names to geocode
        region: Region to focus search in
        cache_file: File to cache results
        
    Returns:
        Dictionary mapping location names to coordinates
    """
    logger.info(f"Batch geocoding {len(location_names)} locations")
    
    # Load cache if it exists
    cache = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cache = json.load(f)
            logger.info(f"Loaded {len(cache)} cached geocoding results")
        except Exception as e:
            logger.warning(f"Failed to load geocoding cache: {e}")
    
    # Geocode locations not in cache
    results = {}
    new_results = 0
    
    for location in location_names:
        # Skip empty location names
        if not location:
            continue
            
        # Check cache first
        if location in cache:
            results[location] = cache[location]
        else:
            # Geocode and cache
            coords = geocode_location(location, region)
            
            if coords:
                results[location] = coords
                cache[location] = coords
                new_results += 1
    
    # Save updated cache
    if new_results > 0:
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache, f)
            logger.info(f"Saved {len(cache)} geocoding results to cache")
        except Exception as e:
            logger.warning(f"Failed to save geocoding cache: {e}")
    
    logger.info(f"Geocoded {new_results} new locations, {len(results)} total")
    
    return results

def enhance_node_coordinates(G, name_attribute: str = 'name', 
                          region: str = "Manchester, UK") -> int:
    """
    Enhance node coordinates by geocoding nodes without coordinates.
    
    Args:
        G: NetworkX graph to enhance
        name_attribute: Node attribute containing the location name
        region: Region to focus geocoding search in
        
    Returns:
        Number of nodes enhanced with coordinates
    """
    logger.info("Enhancing node coordinates")
    
    # Find nodes without coordinates
    missing_coords = []
    for node, data in G.nodes(data=True):
        if ('lat' not in data or 'lon' not in data) and name_attribute in data:
            missing_coords.append((node, data[name_attribute]))
    
    logger.info(f"Found {len(missing_coords)} nodes missing coordinates")
    
    if not missing_coords:
        return 0
    
    # Batch geocode
    location_names = [name for _, name in missing_coords]
    # Batch geocode
    location_names = [name for _, name in missing_coords]
    geocoded = batch_geocode([name for name in location_names], region.split(',')[0])
    
    # Update node coordinates
    enhanced = 0
    for node, name in missing_coords:
        if name in geocoded:
            G.nodes[node]['lat'] = geocoded[name]['lat']
            G.nodes[node]['lon'] = geocoded[name]['lon']
            enhanced += 1
    
    logger.info(f"Enhanced coordinates for {enhanced}/{len(missing_coords)} nodes")
    
    return enhanced

def calculate_distances(G, distance_attribute: str = 'distance') -> None:
    """
    Calculate geographic distances between connected nodes.
    
    Args:
        G: NetworkX graph
        distance_attribute: Edge attribute to store distances in
    """
    logger.info("Calculating geographic distances")
    
    # Count edges with coordinates
    edges_with_coords = 0
    
    # Calculate distances for all edges where both nodes have coordinates
    for u, v, data in G.edges(data=True):
        u_data = G.nodes[u]
        v_data = G.nodes[v]
        
        if 'lat' in u_data and 'lon' in u_data and 'lat' in v_data and 'lon' in v_data:
            # Calculate Haversine distance
            dist = haversine_distance(
                u_data['lat'], u_data['lon'],
                v_data['lat'], v_data['lon']
            )
            
            # Store in edge data
            G[u][v][distance_attribute] = dist
            edges_with_coords += 1
    
    logger.info(f"Calculated distances for {edges_with_coords}/{G.number_of_edges()} edges")

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees).
    
    Args:
        lat1, lon1: Coordinates of first point
        lat2, lon2: Coordinates of second point
        
    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    
    return c * r