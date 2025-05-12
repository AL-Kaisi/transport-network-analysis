"""
Super simple web server for Transport Network Analysis
"""

from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def home():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Transport Network Analysis</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
            .container { max-width: 800px; margin: 0 auto; }
            .header { background-color: #4285f4; color: white; padding: 10px 20px; border-radius: 5px; }
            .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
            button { background-color: #4285f4; color: white; border: none; padding: 10px 15px; 
                    cursor: pointer; border-radius: 4px; }
            button:hover { background-color: #3b78e7; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Transport Network Analysis</h1>
            </div>
            
            <div class="section">
                <h2>Dashboard Status</h2>
                <p>This simple server is working! You've successfully connected to the web server.</p>
                <p><strong>Status:</strong> Connected</p>
            </div>
            
            <div class="section">
                <h2>View Analysis Results</h2>
                <p>You can view the transport network analysis results:</p>
                <a href="/analysis"><button>View Analysis Report</button></a>
            </div>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/analysis')
def analysis():
    # Read the analysis file - this is the file we generated earlier
    try:
        with open('transport_network_report.html', 'r') as f:
            content = f.read()
        return content
    except:
        return "Error loading analysis report. Please make sure the transport_network_report.html file exists."

if __name__ == '__main__':
    print("\n==================================================")
    print("Transport Network Analysis - Simple Web App")
    print("==================================================")
    print("\nServer is running on:")
    print("http://127.0.0.1:5000")
    print("http://localhost:5000")
    print("\nPress CTRL+C to stop the server")
    print("==================================================\n")
    app.run(debug=False, host='127.0.0.1', port=5000)