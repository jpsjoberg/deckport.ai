"""
CMS Admin Routes
Frontend routes for content management system
"""

from flask import render_template, redirect, url_for, flash, request, session
from functools import wraps
from . import admin_bp

def require_admin_auth(f):
    """Decorator to require admin authentication for frontend routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_jwt = request.cookies.get("admin_jwt")
        if not admin_jwt:
            return redirect(url_for("admin_login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/cms')
@require_admin_auth
def cms_dashboard():
    """CMS dashboard with overview and quick actions"""
    return render_template('admin/cms/index.html')


@admin_bp.route('/cms/articles')
@require_admin_auth
def cms_articles():
    """Articles management page"""
    return render_template('admin/cms/articles.html')


@admin_bp.route('/cms/videos')
@require_admin_auth
def cms_videos():
    """Videos management page"""
    return render_template('admin/cms/videos.html')


@admin_bp.route('/cms/articles/<int:article_id>')
@require_admin_auth
def cms_article_detail(article_id):
    """Individual article management page"""
    return render_template('admin/cms/articles.html', article_id=article_id)


@admin_bp.route('/cms/videos/<int:video_id>')
@require_admin_auth
def cms_video_detail(video_id):
    """Individual video management page"""
    return render_template('admin/cms/videos.html', video_id=video_id)
