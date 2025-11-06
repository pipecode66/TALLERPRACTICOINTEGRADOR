from pathlib import Path
from flask import Blueprint, send_from_directory, redirect, current_app

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/')

@dashboard_bp.route('/dashboards/<path:filename>')
def serve_static(filename):
    """Serve static files from the dashboards directory."""
    project_root = Path(current_app.root_path).parent
    dashboards_path = project_root / 'dashboards'
    return send_from_directory(dashboards_path, filename)

@dashboard_bp.route('/')
def index():
    """Redirect to the first dashboard."""
    return redirect('/dashboard/1')

@dashboard_bp.route('/dashboard/<int:day>')
def serve_dashboard(day):
    """Serve the dashboard HTML files."""
    if not (1 <= day <= 5):
        return "Dashboard not found", 404
    project_root = Path(__file__).resolve().parent.parent
    dashboards_path = project_root / 'dashboards'
    return send_from_directory(dashboards_path, f'dashboard_dia_{day}.html')