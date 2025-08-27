"""
Admin CMS Routes
Content Management System endpoints for news articles and videos
"""

import logging
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, g
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import joinedload

from shared.database.connection import SessionLocal
from shared.models.cms import (
    NewsArticle, VideoContent, ContentCategory, ContentTag, ContentView,
    ContentStatus, ContentType, VideoType, VideoPlatform
)
from shared.auth.decorators import admin_required
from shared.auth.admin_roles import Permission
from shared.auth.auto_rbac_decorator import auto_rbac_required

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
admin_cms_bp = Blueprint('admin_cms', __name__, url_prefix='/v1/admin/cms')


# === NEWS ARTICLES ===

@admin_cms_bp.route('/articles', methods=['GET'])
@auto_rbac_required(Permission.CMS_VIEW)
def get_articles():
    """Get list of news articles with filtering and pagination"""
    try:
        with SessionLocal() as session:
            page = int(request.args.get('page', 1))
            page_size = min(int(request.args.get('page_size', 20)), 100)
            status = request.args.get('status')
            content_type = request.args.get('type')
            search = request.args.get('search', '').strip()

            query = session.query(NewsArticle).options(
                joinedload(NewsArticle.author)
            )

            # Apply filters
            if status:
                query = query.filter(NewsArticle.status == status)
            if content_type:
                query = query.filter(NewsArticle.content_type == content_type)
            if search:
                query = query.filter(or_(
                    NewsArticle.title.ilike(f'%{search}%'),
                    NewsArticle.content.ilike(f'%{search}%')
                ))

            # Get total count
            total = query.count()

            # Apply pagination and ordering
            articles = query.order_by(desc(NewsArticle.created_at)).offset(
                (page - 1) * page_size
            ).limit(page_size).all()

            article_list = []
            for article in articles:
                article_data = {
                    'id': article.id,
                    'title': article.title,
                    'slug': article.slug,
                    'excerpt': article.excerpt,
                    'content_type': article.content_type.value,
                    'status': article.status.value,
                    'is_featured': article.is_featured,
                    'is_pinned': article.is_pinned,
                    'featured_image_url': article.featured_image_url,
                    'tags': article.tags or [],
                    'view_count': article.view_count,
                    'like_count': article.like_count,
                    'published_at': article.published_at.isoformat() if article.published_at else None,
                    'created_at': article.created_at.isoformat(),
                    'updated_at': article.updated_at.isoformat(),
                    'author': {
                        'id': article.author.id,
                        'email': article.author.email
                    } if article.author else None
                }
                article_list.append(article_data)

            return jsonify({
                'articles': article_list,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            })

    except Exception as e:
        logger.error(f"Error getting articles: {e}")
        return jsonify({'error': str(e)}), 500


@admin_cms_bp.route('/articles/<int:article_id>', methods=['GET'])
@auto_rbac_required(Permission.CMS_VIEW)
def get_article(article_id: int):
    """Get a specific news article"""
    try:
        with SessionLocal() as session:
            article = session.query(NewsArticle).options(
                joinedload(NewsArticle.author)
            ).filter(NewsArticle.id == article_id).first()

            if not article:
                return jsonify({'error': 'Article not found'}), 404

            return jsonify({
                'id': article.id,
                'title': article.title,
                'slug': article.slug,
                'excerpt': article.excerpt,
                'content': article.content,
                'content_type': article.content_type.value,
                'status': article.status.value,
                'is_featured': article.is_featured,
                'is_pinned': article.is_pinned,
                'featured_image_url': article.featured_image_url,
                'gallery_images': article.gallery_images or [],
                'meta_title': article.meta_title,
                'meta_description': article.meta_description,
                'tags': article.tags or [],
                'published_at': article.published_at.isoformat() if article.published_at else None,
                'expires_at': article.expires_at.isoformat() if article.expires_at else None,
                'view_count': article.view_count,
                'like_count': article.like_count,
                'share_count': article.share_count,
                'created_at': article.created_at.isoformat(),
                'updated_at': article.updated_at.isoformat(),
                'author': {
                    'id': article.author.id,
                    'email': article.author.email
                } if article.author else None
            })

    except Exception as e:
        logger.error(f"Error getting article {article_id}: {e}")
        return jsonify({'error': str(e)}), 500


@admin_cms_bp.route('/articles', methods=['POST'])
@auto_rbac_required(Permission.CMS_CREATE)
def create_article():
    """Create a new news article"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        if not data.get('content'):
            return jsonify({'error': 'Content is required'}), 400

        with SessionLocal() as session:
            # Generate slug from title if not provided
            slug = data.get('slug') or data['title'].lower().replace(' ', '-').replace('--', '-')
            
            # Check if slug already exists
            existing = session.query(NewsArticle).filter(NewsArticle.slug == slug).first()
            if existing:
                slug = f"{slug}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            article = NewsArticle(
                title=data['title'],
                slug=slug,
                excerpt=data.get('excerpt'),
                content=data['content'],
                content_type=ContentType(data.get('content_type', 'news')),
                status=ContentStatus(data.get('status', 'draft')),
                is_featured=data.get('is_featured', False),
                is_pinned=data.get('is_pinned', False),
                featured_image_url=data.get('featured_image_url'),
                gallery_images=data.get('gallery_images'),
                meta_title=data.get('meta_title'),
                meta_description=data.get('meta_description'),
                tags=data.get('tags'),
                published_at=datetime.fromisoformat(data['published_at']) if data.get('published_at') else None,
                expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
                author_admin_id=g.current_admin.id,
                extra_data=data.get('extra_data')
            )

            session.add(article)
            session.commit()

            return jsonify({
                'id': article.id,
                'message': 'Article created successfully'
            }), 201

    except Exception as e:
        logger.error(f"Error creating article: {e}")
        return jsonify({'error': str(e)}), 500


@admin_cms_bp.route('/articles/<int:article_id>', methods=['PUT'])
@auto_rbac_required(Permission.CMS_EDIT)
def update_article(article_id: int):
    """Update a news article"""
    try:
        data = request.get_json()
        
        with SessionLocal() as session:
            article = session.query(NewsArticle).filter(NewsArticle.id == article_id).first()
            
            if not article:
                return jsonify({'error': 'Article not found'}), 404

            # Update fields
            if 'title' in data:
                article.title = data['title']
            if 'slug' in data:
                article.slug = data['slug']
            if 'excerpt' in data:
                article.excerpt = data['excerpt']
            if 'content' in data:
                article.content = data['content']
            if 'content_type' in data:
                article.content_type = ContentType(data['content_type'])
            if 'status' in data:
                article.status = ContentStatus(data['status'])
            if 'is_featured' in data:
                article.is_featured = data['is_featured']
            if 'is_pinned' in data:
                article.is_pinned = data['is_pinned']
            if 'featured_image_url' in data:
                article.featured_image_url = data['featured_image_url']
            if 'gallery_images' in data:
                article.gallery_images = data['gallery_images']
            if 'meta_title' in data:
                article.meta_title = data['meta_title']
            if 'meta_description' in data:
                article.meta_description = data['meta_description']
            if 'tags' in data:
                article.tags = data['tags']
            if 'published_at' in data:
                article.published_at = datetime.fromisoformat(data['published_at']) if data['published_at'] else None
            if 'expires_at' in data:
                article.expires_at = datetime.fromisoformat(data['expires_at']) if data['expires_at'] else None

            session.commit()

            return jsonify({'message': 'Article updated successfully'})

    except Exception as e:
        logger.error(f"Error updating article {article_id}: {e}")
        return jsonify({'error': str(e)}), 500


@admin_cms_bp.route('/articles/<int:article_id>', methods=['DELETE'])
@auto_rbac_required(Permission.CMS_DELETE)
def delete_article(article_id: int):
    """Delete a news article"""
    try:
        with SessionLocal() as session:
            article = session.query(NewsArticle).filter(NewsArticle.id == article_id).first()
            
            if not article:
                return jsonify({'error': 'Article not found'}), 404

            session.delete(article)
            session.commit()

            return jsonify({'message': 'Article deleted successfully'})

    except Exception as e:
        logger.error(f"Error deleting article {article_id}: {e}")
        return jsonify({'error': str(e)}), 500


# === VIDEOS ===

@admin_cms_bp.route('/videos', methods=['GET'])
@auto_rbac_required(Permission.CMS_VIEW)
def get_videos():
    """Get list of videos with filtering and pagination"""
    try:
        with SessionLocal() as session:
            page = int(request.args.get('page', 1))
            page_size = min(int(request.args.get('page_size', 20)), 100)
            status = request.args.get('status')
            video_type = request.args.get('type')
            platform = request.args.get('platform')
            search = request.args.get('search', '').strip()

            query = session.query(VideoContent).options(
                joinedload(VideoContent.author)
            )

            # Apply filters
            if status:
                query = query.filter(VideoContent.status == status)
            if video_type:
                query = query.filter(VideoContent.video_type == video_type)
            if platform:
                query = query.filter(VideoContent.platform == platform)
            if search:
                query = query.filter(or_(
                    VideoContent.title.ilike(f'%{search}%'),
                    VideoContent.description.ilike(f'%{search}%')
                ))

            # Get total count
            total = query.count()

            # Apply pagination and ordering
            videos = query.order_by(desc(VideoContent.created_at)).offset(
                (page - 1) * page_size
            ).limit(page_size).all()

            video_list = []
            for video in videos:
                video_data = {
                    'id': video.id,
                    'title': video.title,
                    'slug': video.slug,
                    'description': video.description,
                    'video_type': video.video_type.value,
                    'platform': video.platform.value,
                    'video_url': video.video_url,
                    'thumbnail_url': video.thumbnail_url,
                    'duration_seconds': video.duration_seconds,
                    'status': video.status.value,
                    'is_featured': video.is_featured,
                    'is_trending': video.is_trending,
                    'tags': video.tags or [],
                    'view_count': video.view_count,
                    'like_count': video.like_count,
                    'published_at': video.published_at.isoformat() if video.published_at else None,
                    'created_at': video.created_at.isoformat(),
                    'updated_at': video.updated_at.isoformat(),
                    'author': {
                        'id': video.author.id,
                        'email': video.author.email
                    } if video.author else None
                }
                video_list.append(video_data)

            return jsonify({
                'videos': video_list,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            })

    except Exception as e:
        logger.error(f"Error getting videos: {e}")
        return jsonify({'error': str(e)}), 500


@admin_cms_bp.route('/videos', methods=['POST'])
@auto_rbac_required(Permission.CMS_CREATE)
def create_video():
    """Create a new video"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        if not data.get('video_url'):
            return jsonify({'error': 'Video URL is required'}), 400

        with SessionLocal() as session:
            # Generate slug from title if not provided
            slug = data.get('slug') or data['title'].lower().replace(' ', '-').replace('--', '-')
            
            # Check if slug already exists
            existing = session.query(VideoContent).filter(VideoContent.slug == slug).first()
            if existing:
                slug = f"{slug}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            video = VideoContent(
                title=data['title'],
                slug=slug,
                description=data.get('description'),
                video_type=VideoType(data.get('video_type', 'tutorial')),
                platform=VideoPlatform(data.get('platform', 'youtube')),
                video_url=data['video_url'],
                embed_code=data.get('embed_code'),
                thumbnail_url=data.get('thumbnail_url'),
                duration_seconds=data.get('duration_seconds'),
                status=ContentStatus(data.get('status', 'draft')),
                is_featured=data.get('is_featured', False),
                is_trending=data.get('is_trending', False),
                meta_title=data.get('meta_title'),
                meta_description=data.get('meta_description'),
                tags=data.get('tags'),
                published_at=datetime.fromisoformat(data['published_at']) if data.get('published_at') else None,
                expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
                author_admin_id=g.current_admin.id,
                extra_data=data.get('extra_data')
            )

            session.add(video)
            session.commit()

            return jsonify({
                'id': video.id,
                'message': 'Video created successfully'
            }), 201

    except Exception as e:
        logger.error(f"Error creating video: {e}")
        return jsonify({'error': str(e)}), 500


# === ANALYTICS ===

@admin_cms_bp.route('/analytics', methods=['GET'])
@auto_rbac_required(Permission.CMS_ANALYTICS)
def get_cms_analytics():
    """Get CMS analytics and statistics"""
    try:
        with SessionLocal() as session:
            # Article statistics
            total_articles = session.query(NewsArticle).count()
            published_articles = session.query(NewsArticle).filter(
                NewsArticle.status == ContentStatus.PUBLISHED
            ).count()
            draft_articles = session.query(NewsArticle).filter(
                NewsArticle.status == ContentStatus.DRAFT
            ).count()

            # Video statistics
            total_videos = session.query(VideoContent).count()
            published_videos = session.query(VideoContent).filter(
                VideoContent.status == ContentStatus.PUBLISHED
            ).count()
            draft_videos = session.query(VideoContent).filter(
                VideoContent.status == ContentStatus.DRAFT
            ).count()

            # Popular content
            popular_articles = session.query(NewsArticle).filter(
                NewsArticle.status == ContentStatus.PUBLISHED
            ).order_by(desc(NewsArticle.view_count)).limit(5).all()

            popular_videos = session.query(VideoContent).filter(
                VideoContent.status == ContentStatus.PUBLISHED
            ).order_by(desc(VideoContent.view_count)).limit(5).all()

            return jsonify({
                'articles': {
                    'total': total_articles,
                    'published': published_articles,
                    'draft': draft_articles
                },
                'videos': {
                    'total': total_videos,
                    'published': published_videos,
                    'draft': draft_videos
                },
                'popular_articles': [{
                    'id': article.id,
                    'title': article.title,
                    'view_count': article.view_count,
                    'published_at': article.published_at.isoformat() if article.published_at else None
                } for article in popular_articles],
                'popular_videos': [{
                    'id': video.id,
                    'title': video.title,
                    'view_count': video.view_count,
                    'published_at': video.published_at.isoformat() if video.published_at else None
                } for video in popular_videos]
            })

    except Exception as e:
        logger.error(f"Error getting CMS analytics: {e}")
        return jsonify({'error': str(e)}), 500
