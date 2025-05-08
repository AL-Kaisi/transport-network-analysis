def create_community_size_chart(community_data):
    """
    Create a histogram of community sizes.
    
    Args:
        community_data: DataFrame or dictionary with community information
    
    Returns:
        Plotly figure object
    """
    import plotly.express as px
    import pandas as pd
    
    # Check if community_data is empty
    if community_data is None or (isinstance(community_data, dict) and not community_data):
        # Return an empty chart with a message
        fig = px.bar(
            x=["No Data"], 
            y=[0],
            labels={"x": "Status", "y": "Count"},
            title="Community Size Distribution (No Data Available)"
        )
        fig.update_layout(
            annotations=[{
                "text": "No community data available. Run analysis first.",
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False
            }]
        )
        return fig
    
    # Check the structure of community_data and convert to dataframe if needed
    if isinstance(community_data, dict):
        # If it's a dictionary of community information
        if 'sizes' in community_data:
            # If it has a 'sizes' key that contains community sizes
            df = pd.DataFrame({"community": list(community_data['sizes'].keys()), 
                             "size": list(community_data['sizes'].values())})
        else:
            # If it's a partition dictionary {node_id: community_id}
            # Count occurrences of each community
            community_counts = {}
            for node, comm in community_data.items():
                if comm not in community_counts:
                    community_counts[comm] = 0
                community_counts[comm] += 1
            
            df = pd.DataFrame({"community": list(community_counts.keys()), 
                             "size": list(community_counts.values())})
    elif isinstance(community_data, pd.DataFrame):
        # If already a DataFrame, check for required columns
        if 'size' not in community_data.columns:
            # If no 'size' column, check for alternatives or assume it needs to be aggregated
            if 'community' in community_data.columns:
                # Count nodes per community
                df = community_data.groupby('community').size().reset_index()
                df.columns = ['community', 'size']
            else:
                # If we can't find usable data, create an empty dataframe with right columns
                df = pd.DataFrame({"community": [], "size": []})
        else:
            # DataFrame already has right structure
            df = community_data
    else:
        # Fallback: create empty dataframe with right structure
        df = pd.DataFrame({"community": [], "size": []})
    
    # Now create the histogram with the properly structured data
    if len(df) > 0:
        fig = px.histogram(
            df,
            x="size",
            nbins=20,
            labels={"size": "Number of Stops", "count": "Number of Communities"},
            title="Community Size Distribution"
        )
        
        fig.update_layout(
            xaxis_title="Community Size (Number of Stops)",
            yaxis_title="Number of Communities",
            bargap=0.1
        )
    else:
        # If dataframe is empty, return message
        fig = px.bar(
            x=["No Data"], 
            y=[0],
            labels={"x": "Status", "y": "Count"},
            title="Community Size Distribution (No Data Available)"
        )
        fig.update_layout(
            annotations=[{
                "text": "No community data available. Run analysis first.",
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False
            }]
        )
    
    return fig