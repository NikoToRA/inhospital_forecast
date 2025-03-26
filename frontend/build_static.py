import os
import shutil
from streamlit.web.bootstrap import run
import streamlit.web.bootstrap as bootstrap
from streamlit.config import get_config_options
import streamlit.runtime.scriptrunner.script_runner as script_runner

def build_static():
    # Create build directory
    build_dir = os.path.join(os.path.dirname(__file__), 'build')
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)

    # Copy static assets
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    if os.path.exists(static_dir):
        shutil.copytree(static_dir, os.path.join(build_dir, 'static'))

    # Generate index.html
    with open(os.path.join(build_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Inhospital Forecast</title>
    <script src="https://cdn.jsdelivr.net/npm/streamlit-component-lib@^1.4.0/dist/streamlit.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div id="root"></div>
    <script>
        // Initialize connection to Streamlit
        const streamlit = new Streamlit.Client();

        // Connect to the Streamlit app backend
        streamlit.connect();

        // Load the Streamlit app
        fetch('/api/StreamlitProxy')
            .then(response => response.json())
            .then(data => {
                // Update the UI with the data
                streamlit.setComponentValue(data);
            });
    </script>
</body>
</html>
        """.strip())

if __name__ == '__main__':
    build_static() 