"""
Test script for the GTFS loader module.
"""

import os
from dotenv import load_dotenv
from src.data_processing.gtfs_loader import GTFSLoader

# Load environment variables
load_dotenv()

def main():
    # Get configuration from environment variables
    gtfs_url = os.getenv("GTFS_URL")
    data_dir = os.getenv("DATA_DIR")
    
    print(f"GTFS URL: {gtfs_url}")
    print(f"Data directory: {data_dir}")
    
    # Create GTFS loader
    loader = GTFSLoader(gtfs_url, data_dir)
    
    # Download and load data
    gtfs_data = loader.process()
    
    # Print information about loaded data
    print("\nLoaded GTFS data:")
    for name, df in gtfs_data.items():
        print(f"- {name}: {len(df)} rows, {df.columns.tolist()}")
    
    # Print a sample of stops data
    if 'stops' in gtfs_data:
        print("\nSample stops data:")
        print(gtfs_data['stops'].head())
    
if __name__ == "__main__":
    main()