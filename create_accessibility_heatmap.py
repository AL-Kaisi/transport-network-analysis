"""
Generate a heatmap visualization of community accessibility for the static HTML dashboard.
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Ensure assets directory exists
os.makedirs('docs/assets', exist_ok=True)

# Load community accessibility data
try:
    with open('assets/json/community_accessibility.json', 'r') as f:
        accessibility_data = json.load(f)
    
    # Extract data for heatmap
    communities = sorted(list(accessibility_data.keys()))
    z_data = []
    
    for comm1 in communities:
        row = []
        for comm2 in communities:
            value = accessibility_data.get(comm1, {}).get(comm2, 0)
            row.append(value)
        z_data.append(row)
    
    # Create heatmap
    plt.figure(figsize=(10, 8))
    ax = sns.heatmap(
        z_data,
        annot=True,
        fmt=".2f",
        cmap="YlGnBu",
        xticklabels=[f"C{c}" for c in communities],
        yticklabels=[f"C{c}" for c in communities]
    )
    plt.title("Community Accessibility")
    plt.xlabel("Destination Community")
    plt.ylabel("Origin Community")
    plt.tight_layout()
    
    # Save figure
    plt.savefig('docs/assets/accessibility_heatmap.png', dpi=300)
    print("Created accessibility heatmap: docs/assets/accessibility_heatmap.png")
except Exception as e:
    print(f"Error creating accessibility heatmap: {e}")