"""
Simple test Dash app to verify connectivity
"""
import dash
from dash import html
import dash_bootstrap_components as dbc

# Initialize the app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# App layout
app.layout = html.Div([
    html.H1("Test Dashboard"),
    html.P("If you can see this page, the Dash server is working correctly!"),
    html.Button("Click Me", id="test-button"),
    html.Div(id="output-div")
])

# Run the app
if __name__ == '__main__':
    print("Starting test app at http://127.0.0.1:8050")
    app.run(debug=True, port=8050)
    print("Server should be running now. Press CTRL+C to stop.")