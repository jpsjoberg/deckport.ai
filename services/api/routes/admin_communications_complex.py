"""

Admin Communications API Routes
Manages announcements, email campaigns, and social media integration
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func, and_, desc
from shared.models.base import db, Player
from shared.auth.auto_rbac_decorator import auto_rbac_required
import logging
from shared.auth.admin_roles import Permission

admin_communications_bp = Blueprint('admin_communications', __name__, url_prefix='/v1/admin/communications')

    """Decorator to require admin authentication"""
    
    def decorated_function(*args, **kwargs):
        auth_result = verify_admin_token(request)
        if not auth_result['valid']:
            return jsonify({'error': 'Admin authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# In-memory storage for demo purposes (would use database in production)
announcements = []
email_campaigns = []
social_metrics = {
    'discord': {'members': 1247, 'online': 342, 'messages_today': 89},
    'telegram': {'subscribers': 892, 'active_today': 156, 'messages_today': 45},
    'twitter': {'followers': 3421, 'impressions_today': 12890, 'engagement_rate': 4.2}
}

@admin_communications_bp.route('/announcements', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.COMM_VIEW])
def get_announcements():
    """Get all announcements"""
    try:
        # Sort by creation date, most recent first
        sorted_announcements = sorted(announcements, key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'announcements': sorted_announcements,
            'total_count': len(announcements)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get announcements: {str(e)}'}), 500

@admin_communications_bp.route('/announcements', methods=['POST'])
@auto_rbac_required(override_permissions=[Permission.COMM_VIEW])
def create_announcement():
    """Create a new announcement"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'message', 'type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create announcement
        announcement = {
            'id': len(announcements) + 1,
            'title': data['title'],
            'message': data['message'],
            'type': data['type'],  # 'info', 'warning', 'success', 'error'
            'priority': data.get('priority', 'normal'),  # 'low', 'normal', 'high', 'urgent'
            'target_audience': data.get('target_audience', 'all'),  # 'all', 'players', 'console_operators'
            'channels': data.get('channels', ['in_app']),  # 'in_app', 'email', 'discord', 'telegram'
            'expires_at': data.get('expires_at'),
            'created_at': datetime.utcnow().isoformat(),
            'created_by': 'admin',  # Would get from JWT in production
            'status': 'active',
            'view_count': 0,
            'click_count': 0
        }
        
        announcements.append(announcement)
        
        # In production, you would:
        # 1. Save to database
        # 2. Send to notification service
        # 3. Trigger email/social media posting if requested
        
        logging.info(f"Created announcement: {announcement['title']}")
        
        return jsonify({
            'success': True,
            'announcement': announcement,
            'message': 'Announcement created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Failed to create announcement: {str(e)}'}), 500

@admin_communications_bp.route('/announcements/<int:announcement_id>', methods=['PUT'])
@auto_rbac_required(override_permissions=[Permission.COMM_VIEW])
def update_announcement(announcement_id):
    """Update an existing announcement"""
    try:
        data = request.get_json()
        
        # Find announcement
        announcement = next((a for a in announcements if a['id'] == announcement_id), None)
        if not announcement:
            return jsonify({'error': 'Announcement not found'}), 404
        
        # Update fields
        updatable_fields = ['title', 'message', 'type', 'priority', 'target_audience', 'channels', 'expires_at', 'status']
        for field in updatable_fields:
            if field in data:
                announcement[field] = data[field]
        
        announcement['updated_at'] = datetime.utcnow().isoformat()
        
        return jsonify({
            'success': True,
            'announcement': announcement,
            'message': 'Announcement updated successfully'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to update announcement: {str(e)}'}), 500

@admin_communications_bp.route('/announcements/<int:announcement_id>', methods=['DELETE'])
@auto_rbac_required(override_permissions=[Permission.COMM_VIEW])
def delete_announcement(announcement_id):
    """Delete an announcement"""
    try:
        global announcements
        announcements = [a for a in announcements if a['id'] != announcement_id]
        
        return jsonify({
            'success': True,
            'message': 'Announcement deleted successfully'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to delete announcement: {str(e)}'}), 500

@admin_communications_bp.route('/email-campaigns', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.COMM_EMAIL])
def_campaigns():
    """Get all email campaigns"""
    try:
        # Sort by creation date, most recent first
        sorted_campaigns = sorted(email_campaigns, key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'campaigns': sorted_campaigns,
            'total_count': len(email_campaigns)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get email campaigns: {str(e)}'}), 500

@admin_communications_bp.route('/email-campaigns', methods=['POST'])
@auto_rbac_required(override_permissions=[Permission.COMM_EMAIL])
def_campaign():
    """Create a new email campaign"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'subject', 'content', 'recipient_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Calculate recipient count based on type
        recipient_count = 0
        if data['recipient_type'] == 'all_players':
            recipient_count = db.session.query(func.count(Player.id)).scalar()
        elif data['recipient_type'] == 'active_players':
            # Players who have activated cards in the last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recipient_count = db.session.query(func.count(func.distinct(Player.id))).join(
                Player.nfc_cards
            ).filter(
                and_(
                    Player.nfc_cards.any(),
                    Player.updated_at >= thirty_days_ago
                )
            ).scalar()
        elif data['recipient_type'] == 'new_players':
            # Players registered in the last 7 days
            week_ago = datetime.utcnow() - timedelta(days=7)
            recipient_count = db.session.query(func.count(Player.id)).filter(
                Player.created_at >= week_ago
            ).scalar()
        
        # Create campaign
        campaign = {
            'id': len(email_campaigns) + 1,
            'name': data['name'],
            'subject': data['subject'],
            'content': data['content'],
            'recipient_type': data['recipient_type'],
            'recipient_count': recipient_count,
            'status': data.get('status', 'draft'),  # 'draft', 'scheduled', 'sending', 'sent', 'failed'
            'scheduled_at': data.get('scheduled_at'),
            'created_at': datetime.utcnow().isoformat(),
            'created_by': 'admin',
            'sent_count': 0,
            'open_count': 0,
            'click_count': 0,
            'bounce_count': 0,
            'unsubscribe_count': 0
        }
        
        email_campaigns.append(campaign)
        
        logging.info(f"Created email campaign: {campaign['name']}")
        
        return jsonify({
            'success': True,
            'campaign': campaign,
            'message': 'Email campaign created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Failed to create email campaign: {str(e)}'}), 500

@admin_communications_bp.route('/email-campaigns/<int:campaign_id>/send', methods=['POST'])
@auto_rbac_required(override_permissions=[Permission.COMM_EMAIL])
def_campaign(campaign_id):
    """Send an email campaign"""
    try:
        # Find campaign
        campaign = next((c for c in email_campaigns if c['id'] == campaign_id), None)
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404
        
        if campaign['status'] != 'draft':
            return jsonify({'error': 'Only draft campaigns can be sent'}), 400
        
        # In production, this would:
        # 1. Queue the campaign for sending
        # 2. Start background job to send emails
        # 3. Update status to 'sending'
        # 4. Track delivery, opens, clicks, etc.
        
        campaign['status'] = 'sending'
        campaign['sent_at'] = datetime.utcnow().isoformat()
        campaign['sent_count'] = campaign['recipient_count']  # Simulate immediate sending
        
        # Simulate some engagement metrics
        campaign['open_count'] = int(campaign['sent_count'] * 0.25)  # 25% open rate
        campaign['click_count'] = int(campaign['open_count'] * 0.15)  # 15% click rate
        campaign['status'] = 'sent'
        
        logging.info(f"Sent email campaign: {campaign['name']} to {campaign['sent_count']} recipients")
        
        return jsonify({
            'success': True,
            'campaign': campaign,
            'message': f'Campaign sent to {campaign["sent_count"]} recipients'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to send campaign: {str(e)}'}), 500

@admin_communications_bp.route('/social-metrics', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.COMM_VIEW])
def get_social_metrics():
    """Get social media metrics"""
    try:
        # In production, this would fetch real data from social media APIs
        return jsonify({
            'platforms': social_metrics,
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
        
        # Create social post record
        social_post = {
            'id': len(announcements) + len(email_campaigns) + 1,  # Simple ID generation
            'content': data['content'],
            'platforms': data['platforms'],  # ['discord', 'telegram', 'twitter']
            'media_urls': data.get('media_urls', []),
            'scheduled_at': data.get('scheduled_at'),
            'status': 'draft',
            'created_at': datetime.utcnow().isoformat(),
            'created_by': 'admin',
            'engagement': {
                'discord': {'reactions': 0, 'replies': 0},
                'telegram': {'views': 0, 'reactions': 0},
                'twitter': {'likes': 0, 'retweets': 0, 'replies': 0}
            }
        }
        
        # In production, this would:
        # 1. Save to database
        # 2. Queue for posting to social platforms
        # 3. Handle media uploads
        # 4. Schedule posts if requested
        
        # Simulate posting
        social_post['status'] = 'posted'
        social_post['posted_at'] = datetime.utcnow().isoformat()
        
        # Simulate some engagement
        for platform in data['platforms']:
            if platform == 'discord':
                social_post['engagement']['discord'] = {'reactions': 12, 'replies': 3}
            elif platform == 'telegram':
                social_post['engagement']['telegram'] = {'views': 89, 'reactions': 15}
            elif platform == 'twitter':
                social_post['engagement']['twitter'] = {'likes': 24, 'retweets': 8, 'replies': 5}
        
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
        active_announcements = len([a for a in announcements if a['status'] == 'active'])
        
        # Count recent campaigns
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_campaigns = len([c for c in email_campaigns 
                              if datetime.fromisoformat(c['created_at'].replace('Z', '+00:00')) >= week_ago])
        
        # Calculate engagement metrics
        total_opens = sum(c.get('open_count', 0) for c in email_campaigns)
        total_clicks = sum(c.get('click_count', 0) for c in email_campaigns)
        total_sent = sum(c.get('sent_count', 0) for c in email_campaigns)
        
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
                                     for platform in social_metrics.values()),
                'total_engagement_today': sum(platform.get('messages_today', platform.get('impressions_today', 0)) 
                                            for platform in social_metrics.values())
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get communications summary: {str(e)}'}), 500
