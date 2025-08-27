"""
Public CMS Routes
Public endpoints for serving news articles and videos to the frontend
"""

import logging
from flask import Blueprint, jsonify, request
from sqlalchemy import desc, and_
from sqlalchemy.orm import joinedload

from shared.database.connection import SessionLocal
from shared.models.cms import (
    NewsArticle, VideoContent, ContentView, ContentStatus
)

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
cms_public_bp = Blueprint('cms_public', __name__, url_prefix='/v1/cms')


@cms_public_bp.route('/news', methods=['GET'])
def get_public_news():
    """Get published news articles for public consumption"""
    try:
        with SessionLocal() as session:
            page = int(request.args.get('page', 1))
            page_size = min(int(request.args.get('page_size', 10)), 50)
            content_type = request.args.get('type')
            featured_only = request.args.get('featured') == 'true'

            query = session.query(NewsArticle).filter(
                NewsArticle.status == ContentStatus.published
            ).options(joinedload(NewsArticle.author))

            # Apply filters
            if content_type:
                query = query.filter(NewsArticle.content_type == content_type)
            if featured_only:
                query = query.filter(NewsArticle.is_featured == True)

            # Get total count
            total = query.count()

            # Apply pagination and ordering
            articles = query.order_by(
                desc(NewsArticle.is_pinned),
                desc(NewsArticle.published_at)
            ).offset((page - 1) * page_size).limit(page_size).all()

            article_list = []
            for article in articles:
                article_data = {
                    'id': article.id,
                    'title': article.title,
                    'slug': article.slug,
                    'excerpt': article.excerpt,
                    'content_type': article.content_type.value,
                    'featured_image_url': article.featured_image_url,
                    'is_featured': article.is_featured,
                    'is_pinned': article.is_pinned,
                    'tags': article.tags or [],
                    'view_count': article.view_count,
                    'like_count': article.like_count,
                    'published_at': article.published_at.isoformat() if article.published_at else None,
                    'author': {
                        'email': article.author.email.split('@')[0] if article.author else 'Deckport Team'
                    }
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
        logger.error(f"Error getting public news: {e}")
        return jsonify({'error': 'Failed to load news'}), 500


@cms_public_bp.route('/news/<slug>', methods=['GET'])
def get_public_article(slug: str):
    """Get a specific published article by slug"""
    try:
        with SessionLocal() as session:
            article = session.query(NewsArticle).filter(
                and_(
                    NewsArticle.slug == slug,
                    NewsArticle.status == ContentStatus.published
                )
            ).options(joinedload(NewsArticle.author)).first()

            if not article:
                return jsonify({'error': 'Article not found'}), 404

            # Track view
            try:
                view = ContentView(
                    article_id=article.id,
                    ip_address=request.remote_addr or '0.0.0.0',
                    user_agent=request.headers.get('User-Agent'),
                    referrer=request.headers.get('Referer')
                )
                session.add(view)
                
                # Increment view count
                article.view_count += 1
                session.commit()
            except Exception as e:
                logger.warning(f"Failed to track view for article {article.id}: {e}")

            return jsonify({
                'id': article.id,
                'title': article.title,
                'slug': article.slug,
                'excerpt': article.excerpt,
                'content': article.content,
                'content_type': article.content_type.value,
                'featured_image_url': article.featured_image_url,
                'gallery_images': article.gallery_images or [],
                'is_featured': article.is_featured,
                'is_pinned': article.is_pinned,
                'meta_title': article.meta_title,
                'meta_description': article.meta_description,
                'tags': article.tags or [],
                'view_count': article.view_count,
                'like_count': article.like_count,
                'share_count': article.share_count,
                'published_at': article.published_at.isoformat() if article.published_at else None,
                'author': {
                    'email': article.author.email.split('@')[0] if article.author else 'Deckport Team'
                }
            })

    except Exception as e:
        logger.error(f"Error getting article {slug}: {e}")
        return jsonify({'error': 'Failed to load article'}), 500


@cms_public_bp.route('/videos', methods=['GET'])
def get_public_videos():
    """Get published videos for public consumption"""
    try:
        with SessionLocal() as session:
            page = int(request.args.get('page', 1))
            page_size = min(int(request.args.get('page_size', 12)), 50)
            video_type = request.args.get('type')
            featured_only = request.args.get('featured') == 'true'
            trending_only = request.args.get('trending') == 'true'

            query = session.query(VideoContent).filter(
                VideoContent.status == ContentStatus.published
            ).options(joinedload(VideoContent.author))

            # Apply filters
            if video_type:
                query = query.filter(VideoContent.video_type == video_type)
            if featured_only:
                query = query.filter(VideoContent.is_featured == True)
            if trending_only:
                query = query.filter(VideoContent.is_trending == True)

            # Get total count
            total = query.count()

            # Apply pagination and ordering
            videos = query.order_by(
                desc(VideoContent.is_featured),
                desc(VideoContent.published_at)
            ).offset((page - 1) * page_size).limit(page_size).all()

            video_list = []
            for video in videos:
                # Format duration
                duration_formatted = None
                if video.duration_seconds:
                    minutes = video.duration_seconds // 60
                    seconds = video.duration_seconds % 60
                    duration_formatted = f"{minutes}:{seconds:02d}"

                video_data = {
                    'id': video.id,
                    'title': video.title,
                    'slug': video.slug,
                    'description': video.description,
                    'video_type': video.video_type.value,
                    'platform': video.platform.value,
                    'video_url': video.video_url,
                    'embed_code': video.embed_code,
                    'thumbnail_url': video.thumbnail_url,
                    'duration_seconds': video.duration_seconds,
                    'duration_formatted': duration_formatted,
                    'is_featured': video.is_featured,
                    'is_trending': video.is_trending,
                    'tags': video.tags or [],
                    'view_count': video.view_count,
                    'like_count': video.like_count,
                    'published_at': video.published_at.isoformat() if video.published_at else None,
                    'author': {
                        'email': video.author.email.split('@')[0] if video.author else 'Deckport Team'
                    }
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
        logger.error(f"Error getting public videos: {e}")
        return jsonify({'error': 'Failed to load videos'}), 500


@cms_public_bp.route('/videos/<slug>', methods=['GET'])
def get_public_video(slug: str):
    """Get a specific published video by slug"""
    try:
        with SessionLocal() as session:
            video = session.query(VideoContent).filter(
                and_(
                    VideoContent.slug == slug,
                    VideoContent.status == ContentStatus.published
                )
            ).options(joinedload(VideoContent.author)).first()

            if not video:
                return jsonify({'error': 'Video not found'}), 404

            # Track view
            try:
                view = ContentView(
                    video_id=video.id,
                    ip_address=request.remote_addr or '0.0.0.0',
                    user_agent=request.headers.get('User-Agent'),
                    referrer=request.headers.get('Referer')
                )
                session.add(view)
                
                # Increment view count
                video.view_count += 1
                session.commit()
            except Exception as e:
                logger.warning(f"Failed to track view for video {video.id}: {e}")

            # Format duration
            duration_formatted = None
            if video.duration_seconds:
                minutes = video.duration_seconds // 60
                seconds = video.duration_seconds % 60
                duration_formatted = f"{minutes}:{seconds:02d}"

            return jsonify({
                'id': video.id,
                'title': video.title,
                'slug': video.slug,
                'description': video.description,
                'video_type': video.video_type.value,
                'platform': video.platform.value,
                'video_url': video.video_url,
                'embed_code': video.embed_code,
                'thumbnail_url': video.thumbnail_url,
                'duration_seconds': video.duration_seconds,
                'duration_formatted': duration_formatted,
                'is_featured': video.is_featured,
                'is_trending': video.is_trending,
                'meta_title': video.meta_title,
                'meta_description': video.meta_description,
                'tags': video.tags or [],
                'view_count': video.view_count,
                'like_count': video.like_count,
                'share_count': video.share_count,
                'watch_time_seconds': video.watch_time_seconds,
                'published_at': video.published_at.isoformat() if video.published_at else None,
                'author': {
                    'email': video.author.email.split('@')[0] if video.author else 'Deckport Team'
                }
            })

    except Exception as e:
        logger.error(f"Error getting video {slug}: {e}")
        return jsonify({'error': 'Failed to load video'}), 500


@cms_public_bp.route('/featured', methods=['GET'])
def get_featured_content():
    """Get featured news and videos for homepage"""
    try:
        with SessionLocal() as session:
            # Get featured articles
            featured_articles = session.query(NewsArticle).filter(
                and_(
                    NewsArticle.status == ContentStatus.published,
                    NewsArticle.is_featured == True
                )
            ).order_by(desc(NewsArticle.published_at)).limit(3).all()

            # Get featured videos
            featured_videos = session.query(VideoContent).filter(
                and_(
                    VideoContent.status == ContentStatus.published,
                    VideoContent.is_featured == True
                )
            ).order_by(desc(VideoContent.published_at)).limit(3).all()

            # Format articles
            articles_data = []
            for article in featured_articles:
                articles_data.append({
                    'id': article.id,
                    'title': article.title,
                    'slug': article.slug,
                    'excerpt': article.excerpt,
                    'content_type': article.content_type.value,
                    'featured_image_url': article.featured_image_url,
                    'view_count': article.view_count,
                    'published_at': article.published_at.isoformat() if article.published_at else None
                })

            # Format videos
            videos_data = []
            for video in featured_videos:
                duration_formatted = None
                if video.duration_seconds:
                    minutes = video.duration_seconds // 60
                    seconds = video.duration_seconds % 60
                    duration_formatted = f"{minutes}:{seconds:02d}"

                videos_data.append({
                    'id': video.id,
                    'title': video.title,
                    'slug': video.slug,
                    'description': video.description,
                    'video_type': video.video_type.value,
                    'thumbnail_url': video.thumbnail_url,
                    'duration_formatted': duration_formatted,
                    'view_count': video.view_count,
                    'published_at': video.published_at.isoformat() if video.published_at else None
                })

            return jsonify({
                'featured_articles': articles_data,
                'featured_videos': videos_data
            })

    except Exception as e:
        logger.error(f"Error getting featured content: {e}")
        return jsonify({'error': 'Failed to load featured content'}), 500
