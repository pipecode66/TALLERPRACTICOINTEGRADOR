from __future__ import annotations

from flask import Blueprint, render_template, redirect, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Página principal del hotel."""
    return render_template('index.html')

@main_bp.route('/reservas')
def reservas():
    """Página de búsqueda y reservas."""
    return render_template('reservas.html')

@main_bp.route('/habitaciones')
def habitaciones():
    """Página de habitaciones."""
    return redirect(url_for('main.reservas'))  # Por ahora redirige a reservas

@main_bp.route('/about')
def about():
    """Página Acerca de."""
    return render_template('about.html')

@main_bp.route('/contacto')
def contacto():
    """Página de contacto."""
    return render_template('contacto.html')

@main_bp.route('/registro')
def registro():
    """Página de registro."""
    return render_template('registro.html')

@main_bp.route('/login')
def login():
    """Página de inicio de sesión."""
    return render_template('login.html')