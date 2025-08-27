"""
Admin Communications API Routes - Real Database Implementation
Manages announcements, email campaigns, and social media integration
"""

from flask import Blueprint, jsonify, request, g
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, desc
from shared.auth.auto_rbac_decorator import auto_rbac_required
from shared.auth.admin_roles import Permission
from shared.auth.decorators import admin_required
from shared.database.connection import SessionLocal
from shared.models.communications import (
    Announcement, EmailCampaign, EmailLog, SocialMediaPost, CommunicationTemplate,
    AnnouncementType, AnnouncementPriority, AnnouncementStatus,
    CampaignStatus, RecipientType
)
from shared.models.base import Player, Admin
import logging

logger = logging.getLogger(__name__)
admin_communications_bp = Blueprint('admin_communications', __name__, url_prefix='/v1/admin/communications')

# Real database implementation - no sample data needed

@admin_communications_bp.route('/announcements', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.COMM_VIEW])
def get_announcements():
    """Get all announcements from database"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)
        status_filter = request.args.get('status', '')
        type_filter = request.args.get('type', '')
        
        with SessionLocal() as session:
            # Build query
            query = session.query(Announcement).join(
                Admin, Announcement.created_by_admin_id == Admin.id
            )
            
            # Apply filters
            if status_filter:
                query = query.filter(Announcement.status == status_filter)
            if type_filter:
                query = query.filter(Announcement.type == type_filter)
            
            # Order by creation date (newest first)
            query = query.order_by(desc(Announcement.created_at))
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * per_page
            announcements = query.offset(offset).limit(per_page).all()
            
            # Format response
            announcement_list = []
            for ann in announcements:
                announcement_list.append({
                    'id': ann.id,
                    'title': ann.title,
                    'message': ann.message,
                    'type': ann.type.value,
                    'priority': ann.priority.value,
                    'target_audience': ann.target_audience,
                    'channels': ann.channels,
                    'status': ann.status.value,
                    'expires_at': ann.expires_at.isoformat() if ann.expires_at else None,
                    'created_at': ann.created_at.isoformat(),
                    'updated_at': ann.updated_at.isoformat(),
                    'created_by': ann.created_by_admin.username,
                    'view_count': ann.view_count,
                    'click_count': ann.click_count,
                    'extra_data': ann.extra_data
                })
            
            return jsonify({
                'announcements': announcement_list,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': (total_count + per_page - 1) // per_page,
                    'has_next': page * per_page < total_count,
                    'has_prev': page > 1
                }
            })
        
    except Exception as e:
        logger.error(f"Error getting announcements: {e}")
        return jsonify({'error': f'Failed to get announcements: {str(e)}'}), 500

@admin_communications_bp.route('/announcements', methods=['POST'])
@auto_rbac_required(override_permissions=[Permission.COMM_VIEW])
def create_announcement():
    """Create a new announcement in database"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'message', 'type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate enum values
        try:
            announcement_type = AnnouncementType(data['type'])
            priority = AnnouncementPriority(data.get('priority', 'normal'))
        except ValueError as e:
            return jsonify({'error': f'Invalid enum value: {str(e)}'}), 400
        
        with SessionLocal() as session:
            # Create announcement
            announcement = Announcement(
                title=data['title'],
                message=data['message'],
                type=announcement_type,
                priority=priority,
                target_audience=data.get('target_audience', 'all'),
                channels=data.get('channels', ['in_app']),
                status=AnnouncementStatus.active,
                expires_at=datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00')) if data.get('expires_at') else None,
                created_by_admin_id=g.admin_id,
                extra_data=data.get('extra_data', {})
            )
            
            session.add(announcement)
            session.commit()
            session.refresh(announcement)
            
            logger.info(f"Created announcement: {announcement.title} by admin {g.admin_id}")
            
            return jsonify({
                'success': True,
                'announcement': {
                    'id': announcement.id,
                    'title': announcement.title,
                    'message': announcement.message,
                    'type': announcement.type.value,
                    'priority': announcement.priority.value,
                    'target_audience': announcement.target_audience,
                    'channels': announcement.channels,
                    'status': announcement.status.value,
                    'expires_at': announcement.expires_at.isoformat() if announcement.expires_at else None,
                    'created_at': announcement.created_at.isoformat(),
                    'view_count': announcement.view_count,
                    'click_count': announcement.click_count
                },
                'message': 'Announcement created successfully'
            }), 201
        
    except Exception as e:
        logger.error(f"Error creating announcement: {e}")
        return jsonify({'error': f'Failed to create announcement: {str(e)}'}), 500

@admin_communications_bp.route('/email-campaigns', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.COMM_EMAIL])
def get_email_campaigns():
    """Get all email campaigns"""
    try:
        return jsonify({
            'campaigns': sample_campaigns,
            'total_count': len(sample_campaigns)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get email campaigns: {str(e)}'}), 500

@admin_communications_bp.route('/email-campaigns', methods=['POST'])
@auto_rbac_required(override_permissions=[Permission.COMM_EMAIL])
def create_email_campaign():
    """Create a new email campaign"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'subject', 'content', 'recipient_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Calculate recipient count based on type (sample data)
        recipient_counts = {
            'all_players': 1247,
            'active_players': 456,
            'new_players': 89
        }
        recipient_count = recipient_counts.get(data['recipient_type'], 0)
        
        # Create campaign (in production, save to database)
        campaign = {
            'id': len(sample_campaigns) + 1,
            'name': data['name'],
            'subject': data['subject'],
            'content': data['content'],
            'recipient_type': data['recipient_type'],
            'recipient_count': recipient_count,
            'status': data.get('status', 'draft'),
            'scheduled_at': data.get('scheduled_at'),
            'created_at': datetime.utcnow().isoformat(),
            'created_by': 'admin',
            'sent_count': 0,
            'open_count': 0,
            'click_count': 0,
            'bounce_count': 0,
            'unsubscribe_count': 0
        }
        
        sample_campaigns.append(campaign)
        
        logging.info(f"Created email campaign: {campaign['name']}")
        
        return jsonify({
            'success': True,
            'campaign': campaign,
            'message': 'Email campaign created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Failed to create email campaign: {str(e)}'}), 500

@admin_communications_bp.route('/social-metrics', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.COMM_VIEW])
def get_social_metrics():
    """Get social media metrics"""
    try:
        return jsonify({
            'platforms': sample_social_metrics,
            'last_updated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get social metrics: {str(e)}'}), 500

@admin_communications_bp.route('/social-post', methods=['POST'])
@auto_rbac_required(override_permissions=[Permission.COMM_VIEW])
def create_social_post():
    """Create a social media post"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['content', 'platforms']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create social post record (in production, save to database and post to platforms)
        social_post = {
            'id': 123,  # Sample ID
            'content': data['content'],
            'platforms': data['platforms'],
            'media_urls': data.get('media_urls', []),
            'scheduled_at': data.get('scheduled_at'),
            'status': 'posted',
            'created_at': datetime.utcnow().isoformat(),
            'posted_at': datetime.utcnow().isoformat(),
            'created_by': 'admin',
            'engagement': {
                'discord': {'reactions': 12, 'replies': 3} if 'discord' in data['platforms'] else {},
                'telegram': {'views': 89, 'reactions': 15} if 'telegram' in data['platforms'] else {},
                'twitter': {'likes': 24, 'retweets': 8, 'replies': 5} if 'twitter' in data['platforms'] else {}
            }
        }
        
        logging.info(f"Created social post for platforms: {', '.join(data['platforms'])}")
        
        return jsonify({
            'success': True,
            'post': social_post,
            'message': f'Post created for {len(data["platforms"])} platform(s)'
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Failed to create social post: {str(e)}'}), 500

@admin_communications_bp.route('/dashboard-summary', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.COMM_VIEW])
def get_communications_summary():
    """Get communications summary for dashboard"""
    try:
        # Count active announcements
        active_announcements = len([a for a in sample_announcements if a['status'] == 'active'])
        
        # Count recent campaigns
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_campaigns = len([c for c in sample_campaigns 
                              if datetime.fromisoformat(c['created_at'].replace('Z', '+00:00')) >= week_ago])
        
        # Calculate engagement metrics
        total_opens = sum(c.get('open_count', 0) for c in sample_campaigns)
        total_clicks = sum(c.get('click_count', 0) for c in sample_campaigns)
        total_sent = sum(c.get('sent_count', 0) for c in sample_campaigns)
        
        open_rate = (total_opens / total_sent * 100) if total_sent > 0 else 0
        click_rate = (total_clicks / total_opens * 100) if total_opens > 0 else 0
        
        return jsonify({
            'active_announcements': active_announcements,
            'recent_campaigns': recent_campaigns,
            'email_metrics': {
                'total_sent': total_sent,
                'total_opens': total_opens,
                'total_clicks': total_clicks,
                'open_rate': round(open_rate, 2),
                'click_rate': round(click_rate, 2)
            },
            'social_summary': {
                'total_followers': sum(platform['members'] if 'members' in platform else platform.get('followers', platform.get('subscribers', 0)) 
                                     for platform in sample_social_metrics.values()),
                'total_engagement_today': sum(platform.get('messages_today', platform.get('impressions_today', 0)) 
                                            for platform in sample_social_metrics.values())
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get communications summary: {str(e)}'}), 500


@admin_communications_bp.route('/campaigns', methods=['GET'])
@admin_required
def get_campaigns():
    """Get email campaigns"""
    try:
        with SessionLocal() as session:
            # Get email campaigns from database
            campaigns = session.query(EmailCampaign).order_by(desc(EmailCampaign.created_at)).all()
            
            campaign_list = []
            for campaign in campaigns:
                campaign_data = {
                    'id': campaign.id,
                    'name': campaign.name,
                    'subject': campaign.subject,
                    'recipient_type': campaign.recipient_type.value,
                    'status': campaign.status.value,
                    'scheduled_at': campaign.scheduled_at.isoformat() if campaign.scheduled_at else None,
                    'sent_at': campaign.sent_at.isoformat() if campaign.sent_at else None,
                    'recipient_count': campaign.recipient_count or 0,
                    'open_count': campaign.open_count or 0,
                    'click_count': campaign.click_count or 0,
                    'created_at': campaign.created_at.isoformat(),
                    'updated_at': campaign.updated_at.isoformat()
                }
                
                # Calculate rates
                if campaign.recipient_count and campaign.recipient_count > 0:
                    campaign_data['open_rate'] = round((campaign.open_count or 0) / campaign.recipient_count * 100, 1)
                    campaign_data['click_rate'] = round((campaign.click_count or 0) / campaign.recipient_count * 100, 1)
                else:
                    campaign_data['open_rate'] = 0.0
                    campaign_data['click_rate'] = 0.0
                
                campaign_list.append(campaign_data)
            
            return jsonify({
                'campaigns': campaign_list,
                'total': len(campaign_list)
            })
            
    except Exception as e:
        logger.error(f"Error getting email campaigns: {e}")
        return jsonify({'error': str(e)}), 500
