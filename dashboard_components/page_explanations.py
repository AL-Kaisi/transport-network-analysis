"""
Page explanations component for the transport network dashboard.
"""

import dash
from dash import html
import dash_bootstrap_components as dbc

def create_overview_explanation():
    """
    Create explanation for the Network Overview tab in British English.
    """
    return html.Div([
        dbc.Alert([
            html.H5("What Am I Looking At?", className="alert-heading"),
            html.P([
                "This dashboard shows an analysis of Greater Manchester's public transport network. ",
                "Think of it as a map of how bus stops, train stations, and tram stops connect together across the region."
            ]),
            html.Hr(),
            html.P([
                "The ", html.Strong("Network Metrics"), " section shows key statistics about our transport system:"
            ]),
            html.Ul([
                html.Li([html.Strong("Nodes"), ": Each individual transport stop in the network"]),
                html.Li([html.Strong("Edges"), ": Direct connections between stops"]),
                html.Li([html.Strong("Density"), ": How interconnected the network is overall"]),
                html.Li([html.Strong("Communities"), ": Groups of stops that are well-connected to each other"]),
                html.Li([html.Strong("Modularity"), ": How clearly separated the communities are from each other"])
            ]),
            html.P([
                "The ", html.Strong("Community Size Distribution"), " chart shows how many transport stops exist in each community. ",
                "Larger communities often correspond to city centre areas or major transport corridors."
            ]),
            html.P([
                "The ", html.Strong("Community Network"), " visualisation shows how different communities connect to each other. ",
                "Brighter, larger nodes represent communities with more connections to other areas."
            ])
        ], color="info", className="mb-4"),
    ])

def create_communities_explanation():
    """
    Create explanation for the Communities tab in British English.
    """
    return html.Div([
        dbc.Alert([
            html.H5("Understanding Transport Communities", className="alert-heading"),
            html.P([
                "This page shows how Greater Manchester's transport network naturally divides into 'communities' - ",
                "groups of stops and stations that have strong connections to each other."
            ]),
            html.Hr(),
            html.P([
                "The ", html.Strong("Community Visualization"), " displays these communities on a map, with each colour representing a different community. ",
                "Areas with the same colour have good transport links between them, while different colours suggest potential barriers or service gaps."
            ]),
            html.P([
                "The ", html.Strong("Community Statistics"), " table shows detailed information about each community:"
            ]),
            html.Ul([
                html.Li([html.Strong("Size"), ": Number of stops within the community"]),
                html.Li([html.Strong("Density"), ": How interconnected the stops are within this community"]),
                html.Li([html.Strong("Average Degree"), ": The average number of connections per stop"])
            ]),
            html.P([
                "The ", html.Strong("Community Accessibility Analysis"), " shows how easily passengers can travel between different communities. ",
                "Darker colours indicate better connections between communities, while lighter colours suggest limited or slow service between areas."
            ])
        ], color="info", className="mb-4"),
    ])

def create_critical_nodes_explanation():
    """
    Create explanation for the Critical Nodes tab in British English.
    """
    return html.Div([
        dbc.Alert([
            html.H5("Critical Transport Hubs", className="alert-heading"),
            html.P([
                "This page identifies the most important stops and stations in Greater Manchester's transport network - ",
                "the locations that are most crucial for keeping passengers moving efficiently."
            ]),
            html.Hr(),
            html.P([
                "The ", html.Strong("Critical Nodes Visualization"), " highlights these key transport hubs on a map. ",
                "Larger circles represent stops that are more critical to the overall network. If services at these locations were disrupted, ",
                "it would have a significant impact on journeys across the region."
            ]),
            html.P([
                "The ", html.Strong("Top Critical Nodes"), " table ranks the most important stops based on several factors:"
            ]),
            html.Ul([
                html.Li([html.Strong("Centrality"), ": How important the stop is for connecting different parts of the network"]),
                html.Li([html.Strong("Community"), ": Which transport community the stop belongs to"]),
                html.Li([html.Strong("Degree"), ": The number of direct connections to other stops"])
            ]),
            html.P([
                "These critical nodes often correspond to major interchange stations, busy town centres, and key corridor junctions. ",
                "They are priority locations for investment in capacity, reliability, and resilience."
            ])
        ], color="info", className="mb-4"),
    ])

def create_equity_explanation():
    """
    Create explanation for the Equity Analysis tab in British English.
    """
    return html.Div([
        dbc.Alert([
            html.H5("Transport Fairness Analysis", className="alert-heading"),
            html.P([
                "This page examines how fairly transport services are distributed across Greater Manchester, ",
                "highlighting areas where some communities may be disadvantaged by current services."
            ]),
            html.Hr(),
            html.P([
                "The ", html.Strong("Equity Gaps"), " section identifies specific problems in the transport network that create unfair outcomes for residents:"
            ]),
            html.Ul([
                html.Li([html.Strong("Poor connectivity"), ": Areas with limited services or connections to key destinations"]),
                html.Li([html.Strong("Limited evening services"), ": Communities with reduced off-peak transport options"]),
                html.Li([html.Strong("Inadequate cross-town connections"), ": Difficult journeys between certain areas"]),
                html.Li([html.Strong("Accessibility barriers"), ": Stations lacking proper facilities for disabled passengers"])
            ]),
            html.P([
                "Each equity gap is rated by severity (Medium or High) and includes specific details about affected communities ",
                "and the metrics used to identify the issue."
            ]),
            html.P([
                "This analysis helps transport planners prioritise improvements that would create a fairer, more inclusive ",
                "transport system for all Greater Manchester residents."
            ])
        ], color="info", className="mb-4"),
    ])

def create_scenario_explanation():
    """
    Create explanation for the Scenario Testing tab in British English.
    """
    return html.Div([
        dbc.Alert([
            html.H5("What-If Planning Tools", className="alert-heading"),
            html.P([
                "This page allows planners to test different scenarios and see how changes might affect Greater Manchester's transport network."
            ]),
            html.Hr(),
            html.P([
                "The ", html.Strong("Node Removal Simulation"), " helps assess what would happen if certain stops or stations were temporarily closed ",
                "due to planned works, emergencies, or special events. This shows how resilient the network is to disruption."
            ]),
            html.P([
                "The ", html.Strong("Connection Addition Simulation"), " lets planners test the impact of adding new transport links between communities. ",
                "This can help prioritise which new routes or services would provide the greatest benefit to passengers."
            ]),
            html.P([
                "The ", html.Strong("Network Evolution Simulation"), " allows for testing long-term strategies for improving the transport network, ",
                "particularly focusing on improving connections for vulnerable or isolated communities."
            ]),
            html.P([
                "These planning tools help transport authorities make informed decisions about future investments and improvements, ",
                "ensuring they deliver the greatest benefit to passengers across Greater Manchester."
            ])
        ], color="info", className="mb-4"),
    ])