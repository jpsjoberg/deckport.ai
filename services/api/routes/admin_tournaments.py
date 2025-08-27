"""
Admin tournament management routes - Real data from database
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timezone, timedelta
from sqlalchemy import and_, or_, desc, func, text
from shared.database.connection import SessionLocal
from shared.models.base import Player
from shared.models.tournaments import (
    Tournament, TournamentParticipant, TournamentMatch, PlayerWallet, WalletTransaction,
    TournamentStatus, TournamentType, TransactionType
)
from shared.auth.auto_rbac_decorator import auto_rbac_required
from shared.auth.admin_roles import Permission
import logging

logger = logging.getLogger(__name__)

admin_tournaments_bp = Blueprint('admin_tournaments', __name__, url_prefix='/v1/admin/tournaments')

@admin_tournaments_bp.route('/stats', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.GAME_TOURNAMENTS])
def get_tournament_stats():
    """Get real tournament statistics"""
    try:
        with SessionLocal() as session:
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Active tournaments
            active_tournaments = session.query(Tournament).filter(
                Tournament.status == TournamentStatus.IN_PROGRESS
            ).count()
            
            # Scheduled tournaments
            scheduled_tournaments = session.query(Tournament).filter(
                Tournament.status == TournamentStatus.REGISTRATION_OPEN
            ).count()
            
            # Total participants across all active/scheduled tournaments
            total_participants = session.query(func.sum(
                session.query(TournamentParticipant).filter(
                    TournamentParticipant.tournament_id == Tournament.id,
                    TournamentParticipant.is_active == True
                ).count()
            )).filter(
                or_(
                    Tournament.status == TournamentStatus.IN_PROGRESS,
                    Tournament.status == TournamentStatus.REGISTRATION_OPEN
                )
            ).scalar() or 0
            
            # Total prize pool across all active/scheduled tournaments
            total_prize_pool = session.query(func.coalesce(func.sum(Tournament.prize_pool), 0)).filter(
                or_(
                    Tournament.status == TournamentStatus.IN_PROGRESS,
                    Tournament.status == TournamentStatus.REGISTRATION_OPEN
                )
            ).scalar() or 0
            
            # Recent tournament activity
            recent_tournaments = session.query(Tournament).filter(
                Tournament.created_at >= now - timedelta(hours=24)
            ).order_by(desc(Tournament.created_at)).limit(5).all()
            
            recent_activity = []
            for tournament in recent_tournaments:
                recent_activity.append({
                    'type': 'tournament_created',
                    'tournament_id': tournament.id,
                    'tournament_name': tournament.name,
                    'time': tournament.created_at.isoformat(),
                    'participants': len(tournament.participants)
                })
            
            stats = {
                'active_tournaments': active_tournaments,
                'scheduled_tournaments': scheduled_tournaments,
                'total_participants': total_participants,
                'total_prize_pool': float(total_prize_pool),
                'recent_activity': recent_activity,
                'last_updated': now.isoformat()
            }
            
            return jsonify(stats)
            
    except Exception as e:
        logger.error(f"Error getting tournament stats: {e}")
        return jsonify({'error': 'Failed to retrieve tournament statistics'}), 500

@admin_tournaments_bp.route('/', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.GAME_TOURNAMENTS])
def get_tournaments():
    """Get all tournaments with real data"""
    try:
        with SessionLocal() as session:
            # Get all tournaments
            tournaments = session.query(Tournament).order_by(desc(Tournament.created_at)).all()
            
            tournament_list = []
            for tournament in tournaments:
                # Count participants from database
                participant_count = session.query(TournamentParticipant).filter(
                    TournamentParticipant.tournament_id == tournament.id
                ).count()
                active_participants = session.query(TournamentParticipant).filter(
                    TournamentParticipant.tournament_id == tournament.id,
                    TournamentParticipant.is_active == True
                ).count()
                
                tournament_data = {
                    'id': tournament.id,
                    'name': tournament.name,
                    'description': tournament.description,
                    'status': tournament.status.value,
                    'tournament_type': tournament.tournament_type.value,
                    'entry_fee': float(tournament.entry_fee),
                    'total_prize_pool': float(tournament.prize_pool),
                    'max_participants': tournament.max_participants,
                    'participants': participant_count,
                    'active_participants': active_participants,
                    'matches_total': 0,  # TODO: Implement match tracking
                    'matches_completed': 0,
                    'matches_active': 0,
                    'registration_start': tournament.registration_start.isoformat() if tournament.registration_start else None,
                    'registration_end': tournament.registration_end.isoformat() if tournament.registration_end else None,
                    'start_time': tournament.start_time.isoformat(),
                    'end_time': tournament.end_time.isoformat() if tournament.end_time else None,
                    'created_at': tournament.created_at.isoformat(),
                    'updated_at': tournament.updated_at.isoformat()
                }
                tournament_list.append(tournament_data)
            
            return jsonify({
                'tournaments': tournament_list,
                'total': len(tournament_list)
            })
            
    except Exception as e:
        logger.error(f"Error getting tournaments: {e}")
        return jsonify({'error': 'Failed to retrieve tournaments'}), 500

@admin_tournaments_bp.route('/', methods=['POST'])
@auto_rbac_required(override_permissions=[Permission.GAME_TOURNAMENTS])
def create_tournament():
    """Create a new tournament"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['name', 'format', 'max_participants', 'start_time']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        with SessionLocal() as session:
            # Parse start time
            try:
                start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid start_time format'}), 400
            
            # Determine fee structure
            fee_type = TournamentFeeType.FREE
            entry_fee = 0
            house_percentage = 0
            
            if data.get('fee_type') == 'entry_fee':
                fee_type = TournamentFeeType.ENTRY_FEE
                entry_fee = float(data.get('entry_fee', 0))
                house_percentage = float(data.get('house_percentage', 10))  # Default 10% house cut
            
            # Calculate base prize pool
            base_prize_pool = float(data.get('base_prize_pool', 0))
            
            # Create tournament
            tournament = Tournament(
                name=data['name'],
                description=data.get('description'),
                format=TournamentFormat(data['format']),
                max_participants=int(data['max_participants']),
                min_participants=int(data.get('min_participants', 2)),
                fee_type=fee_type,
                entry_fee=entry_fee,
                house_percentage=house_percentage,
                base_prize_pool=base_prize_pool,
                total_prize_pool=base_prize_pool,  # Will be updated as players register
                start_time=start_time,
                registration_start=datetime.now(timezone.utc),
                registration_end=start_time - timedelta(minutes=30),  # Close registration 30 min before start
                auto_start_when_full=data.get('auto_start_when_full', False),
                public_registration=data.get('public_registration', True),
                status=TournamentStatus.REGISTRATION_OPEN
            )
            
            session.add(tournament)
            session.commit()
            
            logger.info(f"Created tournament: {tournament.name} (ID: {tournament.id})")
            
            return jsonify({
                'success': True,
                'tournament_id': tournament.id,
                'message': f'Tournament "{tournament.name}" created successfully'
            })
            
    except Exception as e:
        logger.error(f"Error creating tournament: {e}")
        return jsonify({'error': 'Failed to create tournament'}), 500

@admin_tournaments_bp.route('/<int:tournament_id>', methods=['GET'])
@auto_rbac_required(override_permissions=[Permission.GAME_TOURNAMENTS])
def get_tournament_details(tournament_id):
    """Get detailed tournament information"""
    try:
        with SessionLocal() as session:
            tournament = session.query(Tournament).filter(Tournament.id == tournament_id).first()
            
            if not tournament:
                return jsonify({'error': 'Tournament not found'}), 404
            
            # Get participants with player details
            participants = []
            for participant in tournament.participants:
                participants.append({
                    'id': participant.id,
                    'player_id': participant.player.id,
                    'player_name': participant.player.display_name or f"Player {participant.player.id}",
                    'player_email': participant.player.email,
                    'registered_at': participant.registered_at.isoformat(),
                    'entry_fee_paid': float(participant.entry_fee_paid),
                    'is_active': participant.is_active,
                    'matches_played': participant.matches_played,
                    'matches_won': participant.matches_won,
                    'matches_lost': participant.matches_lost,
                    'final_position': participant.final_position,
                    'prize_amount': float(participant.prize_amount),
                    'prize_paid': participant.prize_paid
                })
            
            # Get matches
            matches = []
            for match in tournament.matches:
                matches.append({
                    'id': match.id,
                    'round_number': match.round_number,
                    'match_number': match.match_number,
                    'player1_name': match.player1.display_name or f"Player {match.player1.id}",
                    'player2_name': match.player2.display_name or f"Player {match.player2.id}",
                    'winner_name': match.winner.display_name if match.winner else None,
                    'status': match.status,
                    'scheduled_at': match.scheduled_at.isoformat() if match.scheduled_at else None,
                    'started_at': match.started_at.isoformat() if match.started_at else None,
                    'completed_at': match.completed_at.isoformat() if match.completed_at else None
                })
            
            tournament_data = {
                'id': tournament.id,
                'name': tournament.name,
                'description': tournament.description,
                'status': tournament.status.value,
                'format': tournament.format.value,
                'fee_type': tournament.fee_type.value,
                'entry_fee': float(tournament.entry_fee),
                'house_percentage': float(tournament.house_percentage),
                'base_prize_pool': float(tournament.base_prize_pool),
                'total_prize_pool': float(tournament.prize_pool),
                'max_participants': tournament.max_participants,
                'min_participants': tournament.min_participants,
                'current_round': tournament.current_round,
                'total_rounds': tournament.total_rounds,
                'auto_start_when_full': tournament.auto_start_when_full,
                'public_registration': tournament.public_registration,
                'registration_start': tournament.registration_start.isoformat() if tournament.registration_start else None,
                'registration_end': tournament.registration_end.isoformat() if tournament.registration_end else None,
                'start_time': tournament.start_time.isoformat(),
                'end_time': tournament.end_time.isoformat() if tournament.end_time else None,
                'created_at': tournament.created_at.isoformat(),
                'updated_at': tournament.updated_at.isoformat(),
                'participants': participants,
                'matches': matches
            }
            
            return jsonify(tournament_data)
            
    except Exception as e:
        logger.error(f"Error getting tournament details: {e}")
        return jsonify({'error': 'Failed to retrieve tournament details'}), 500

@admin_tournaments_bp.route('/<int:tournament_id>/start', methods=['POST'])
@auto_rbac_required(override_permissions=[Permission.GAME_TOURNAMENTS])
def start_tournament(tournament_id):
    """Start a tournament manually"""
    try:
        with SessionLocal() as session:
            tournament = session.query(Tournament).filter(Tournament.id == tournament_id).first()
            
            if not tournament:
                return jsonify({'error': 'Tournament not found'}), 404
            
            if tournament.status != TournamentStatus.REGISTRATION_OPEN:
                return jsonify({'error': f'Tournament cannot be started from status: {tournament.status.value}'}), 400
            
            # Check minimum participants
            active_participants = len([p for p in tournament.participants if p.is_active])
            if active_participants < tournament.min_participants:
                return jsonify({'error': f'Not enough participants. Need at least {tournament.min_participants}, have {active_participants}'}), 400
            
            # Update tournament status
            tournament.status = TournamentStatus.IN_PROGRESS
            tournament.start_time = datetime.now(timezone.utc)
            tournament.current_round = 1
            
            # TODO: Generate tournament bracket/matches based on format
            # This would be implemented based on the tournament format
            
            session.commit()
            
            logger.info(f"Started tournament: {tournament.name} (ID: {tournament.id})")
            
            return jsonify({
                'success': True,
                'message': f'Tournament "{tournament.name}" started successfully'
            })
            
    except Exception as e:
        logger.error(f"Error starting tournament: {e}")
        return jsonify({'error': 'Failed to start tournament'}), 500
