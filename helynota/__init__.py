from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any

from flask import Flask

from .database import db
from .seed import seed_initial_data
from .dashboard_routes import dashboard_bp
from .main_routes import main_bp


def create_app(test_config: Optional[Dict[str, Any]] = None) -> Flask:
    """Application factory used by tests and runtime."""
    project_root = Path(__file__).resolve().parent.parent
    
    app = Flask(
        __name__,
        template_folder=str(project_root / "templates"),
        static_folder=str(project_root / "static")
    )
    
    default_db_path = project_root / "hotel_reservas.db"

    app.config.setdefault("SQLALCHEMY_DATABASE_URI", f"sqlite:///{default_db_path}")
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("SECRET_KEY", "hotel-reservas-secret")

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from .routes import api_bp

    # Registrar blueprints
    app.register_blueprint(main_bp)  # Rutas principales
    app.register_blueprint(api_bp)   # API
    app.register_blueprint(dashboard_bp, url_prefix='/dashboards')  # Dashboards

    @app.cli.command("init-db")
    def init_db_command() -> None:
        """Create database schema and seed sample data."""
        from .models import BaseModel  # noqa: F401

        db_path = Path(app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)

        db.drop_all()
        db.create_all()
        seed_initial_data()
        print(f"Database initialised at {db_path}")

    return app
