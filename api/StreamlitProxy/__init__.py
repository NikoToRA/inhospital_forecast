import azure.functions as func
import json
import sys
import os
import importlib.util

def main(req: func.HttpRequest) -> func.HttpResponse:
    # Add the frontend directory to the Python path
    frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend'))
    sys.path.append(frontend_path)

    # Import the Streamlit app
    spec = importlib.util.spec_from_file_location("streamlit_app", os.path.join(frontend_path, "streamlit_app.py"))
    streamlit_app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(streamlit_app)

    try:
        # Get the data from the Streamlit app
        data = streamlit_app.get_data()
        
        # Convert the data to JSON
        return func.HttpResponse(
            json.dumps(data),
            mimetype="application/json"
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500
        ) 