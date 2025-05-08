"""
Enhanced GTFS loader with better error handling and data quality improvements.
"""

import os
import io
import zipfile
import logging
import requests
import pandas as pd
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class EnhancedGTFSLoader:
    """Enhanced class for loading and validating GTFS data."""
    
    def __init__(self, gtfs_url: str, data_dir: str):
        """
        Initialize the enhanced GTFS loader.
        
        Args:
            gtfs_url: URL to download the GTFS data from
            data_dir: Directory to store the extracted data
        """
        self.gtfs_url = gtfs_url
        self.data_dir = data_dir
        self.gtfs_data = {}
        
    def download_and_extract(self, force_download: bool = False) -> List[str]:
        """
        Download and extract GTFS data with better error handling.
        
        Args:
            force_download: If True, download data even if it exists locally
            
        Returns:
            List of extracted filenames
        """
        logger.info(f"Downloading GTFS data from {self.gtfs_url}")
        
        # Create the data directory if it doesn't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # Check if data already exists and force_download is False
        if not force_download and os.path.exists(os.path.join(self.data_dir, "stops.txt")):
            logger.info("GTFS data already exists locally, skipping download")
            return os.listdir(self.data_dir)
            
        # Download the GTFS zip file with proper error handling
        try:
            response = requests.get(self.gtfs_url, timeout=30)
            response.raise_for_status()  # Raise error for bad status codes
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download GTFS data: {str(e)}")
            raise Exception(f"Failed to download GTFS data: {str(e)}")
            
        # Extract the contents
        try:
            z = zipfile.ZipFile(io.BytesIO(response.content))
            z.extractall(self.data_dir)
        except zipfile.BadZipFile:
            logger.error("Invalid zip file downloaded")
            raise Exception("Invalid zip file downloaded")
        except Exception as e:
            logger.error(f"Error extracting GTFS data: {str(e)}")
            raise Exception(f"Error extracting GTFS data: {str(e)}")
        
        # List the extracted files
        files = os.listdir(self.data_dir)
        logger.info(f"Extracted {len(files)} files: {', '.join(files)}")
        
        return files
        
    def load_data(self, validate: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Load GTFS data into pandas DataFrames with improved data types and validation.
        
        Args:
            validate: If True, validate and clean the data
            
        Returns:
            Dictionary mapping file names to pandas DataFrames
        """
        logger.info("Loading GTFS data into pandas DataFrames")
        
        # Define required GTFS files with their data types
        required_files = {
            "stops.txt": {
                'stop_id': str,
                'stop_code': str,
                'stop_name': str,
                'stop_desc': str,
                'stop_lat': float,
                'stop_lon': float
            },
            "routes.txt": {
                'route_id': str,
                'agency_id': str,
                'route_short_name': str,
                'route_long_name': str,
                'route_type': int
            },
            "trips.txt": {
                'route_id': str,
                'service_id': str,
                'trip_id': str
            },
            "stop_times.txt": {
                'trip_id': str,
                'stop_id': str,
                'stop_sequence': int
            }
        }
        
        # Load required files with proper data types
        for file, dtypes in required_files.items():
            file_path = os.path.join(self.data_dir, file)
            if not os.path.exists(file_path):
                logger.warning(f"Required GTFS file not found: {file}")
                if file in ["stops.txt", "routes.txt", "trips.txt", "stop_times.txt"]:
                    raise FileNotFoundError(f"Required GTFS file not found: {file}")
                continue
            
            try:
                # For large files like stop_times.txt, use chunking
                if file == "stop_times.txt":
                    chunks = []
                    chunk_size = 500000  # Adjust based on available memory
                    
                    for chunk in pd.read_csv(file_path, dtype=dtypes, chunksize=chunk_size, 
                                           na_values=[''], keep_default_na=True, low_memory=False):
                        # Clean the chunk if validation is enabled
                        if validate:
                            chunk = self._clean_stop_times(chunk)
                        chunks.append(chunk)
                    
                    df = pd.concat(chunks)
                else:
                    df = pd.read_csv(file_path, dtype=dtypes, na_values=[''], keep_default_na=True)
                    
                    # Clean data if validation is enabled
                    if validate:
                        if file == "stops.txt":
                            df = self._clean_stops(df)
                        elif file == "routes.txt":
                            df = self._clean_routes(df)
                        elif file == "trips.txt":
                            df = self._clean_trips(df)
                
                # Add to the GTFS data dictionary
                self.gtfs_data[file.split('.')[0]] = df
                
            except Exception as e:
                logger.error(f"Error loading {file}: {str(e)}")
                raise Exception(f"Error loading {file}: {str(e)}")
            
        # Load optional files
        optional_files = ["calendar.txt", "transfers.txt", "shapes.txt", "frequencies.txt"]
        for file in optional_files:
            file_path = os.path.join(self.data_dir, file)
            if os.path.exists(file_path):
                try:
                    self.gtfs_data[file.split('.')[0]] = pd.read_csv(file_path)
                    logger.info(f"Loaded optional file: {file}")
                except Exception as e:
                    logger.warning(f"Error loading optional file {file}: {str(e)}")
        
        # Log summary of loaded data
        logger.info(f"Loaded {len(self.gtfs_data)} GTFS files")
        for name, df in self.gtfs_data.items():
            logger.info(f"  {name}: {len(df)} rows")
            
        return self.gtfs_data
    
    def _clean_stops(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate stops data."""
        # Remove stops without coordinates
        initial_len = len(df)
        df = df.dropna(subset=['stop_lat', 'stop_lon'])
        
        # Log how many stops were removed
        removed = initial_len - len(df)
        if removed > 0:
            logger.warning(f"Removed {removed} stops without coordinates")
        
        # Ensure coordinates are within reasonable bounds
        df = df[(df['stop_lat'] >= -90) & (df['stop_lat'] <= 90) & 
                (df['stop_lon'] >= -180) & (df['stop_lon'] <= 180)]
        
        return df
    
    def _clean_routes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate routes data."""
        # Remove routes without IDs
        initial_len = len(df)
        df = df.dropna(subset=['route_id'])
        
        # Log how many routes were removed
        removed = initial_len - len(df)
        if removed > 0:
            logger.warning(f"Removed {removed} routes without IDs")
        
        # Ensure route_type is valid (0-7 according to GTFS spec)
        df = df[(df['route_type'] >= 0) & (df['route_type'] <= 7)]
        
        return df
    
    def _clean_trips(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate trips data."""
        # Remove trips without IDs or route IDs
        initial_len = len(df)
        df = df.dropna(subset=['trip_id', 'route_id'])
        
        # Log how many trips were removed
        removed = initial_len - len(df)
        if removed > 0:
            logger.warning(f"Removed {removed} trips without IDs or route IDs")
        
        return df
    
    def _clean_stop_times(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate stop times data."""
        # Remove stop times without trip IDs, stop IDs, or stop sequences
        initial_len = len(df)
        df = df.dropna(subset=['trip_id', 'stop_id', 'stop_sequence'])
        
        # Log how many stop times were removed
        removed = initial_len - len(df)
        if removed > 0:
            logger.debug(f"Removed {removed} stop times with missing data")
        
        # Ensure stop_sequence is non-negative
        df = df[df['stop_sequence'] >= 0]
        
        # Parse arrival and departure times if possible
        for time_col in ['arrival_time', 'departure_time']:
            if time_col in df.columns:
                # Convert time strings to seconds past midnight for easier calculations
                df[f'{time_col}_seconds'] = df[time_col].apply(self._time_to_seconds)
        
        return df
    
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
    
    def process(self, force_download: bool = False, validate: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Download, extract, and load GTFS data with validation.
        
        Args:
            force_download: If True, download data even if it exists locally
            validate: If True, validate and clean the data
            
        Returns:
            Dictionary mapping file names to pandas DataFrames
        """
        self.download_and_extract(force_download)
        return self.load_data(validate)