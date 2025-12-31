"""
REST API endpoints for device fingerprinting data.
Serves JSON data for frontend visualizations and external consumers.
"""

from flask import Blueprint, jsonify, request
from sqlalchemy import func
from app import db
from src.models import Device, Account, DeviceAccountCrossing
from src.risk_calculator import RiskCalculator
from src.device_matcher import DeviceMatcher

api_bp = Blueprint('api', __name__)


@api_bp.route('/devices', methods=['GET'])
def get_devices():
    """Get list of devices with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = Device.query.order_by(Device.last_seen.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'devices': [d.to_dict() for d in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@api_bp.route('/accounts', methods=['GET'])
def get_accounts():
    """Get list of accounts."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = Account.query.order_by(Account.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'accounts': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages
    })


@api_bp.route('/graph-data', methods=['GET'])
def get_graph_data():
    """
    Get D3.js compatible graph data (nodes and links).
    Nodes: Devices and Accounts.
    Links: Crossings.
    """
    limit = request.args.get('limit', 100, type=int)
    
    # Fetch recent crossings
    crossings = DeviceAccountCrossing.query.order_by(
        DeviceAccountCrossing.first_seen.desc()
    ).limit(limit).all()
    
    nodes = {}
    links = []
    
    for c in crossings:
        # Device Node
        if c.device_id not in nodes:
            device = db.session.get(Device, c.device_id)
            if device:
                nodes[c.device_id] = {
                    'id': c.device_id,
                    'group': 'device',
                    'risk_score': float(device.risk_score),
                    'label': f"{device.os} - {device.browser}"
                }
        
        # Account Node
        if c.account_id not in nodes:
            account = db.session.get(Account, c.account_id)
            if account:
                nodes[c.account_id] = {
                    'id': c.account_id,
                    'group': 'account',
                    'risk_score': float(account.risk_score),
                    'label': f"Account ({account.kyc_level})"
                }
        
        # Link
        if c.device_id in nodes and c.account_id in nodes:
            links.append({
                'source': c.device_id,
                'target': c.account_id,
                'value': 1,
                'risk_flag': c.risk_flag
            })
    
    return jsonify({
        'nodes': list(nodes.values()),
        'links': links
    })


@api_bp.route('/calculate-risk', methods=['POST'])
def calculate_risk():
    """
    Trigger risk calculation for a specific device.
    """
    data = request.get_json()
    device_id = data.get('device_id')
    
    if not device_id:
        return jsonify({'error': 'device_id required'}), 400
        
    device = db.session.get(Device, device_id)
    if not device:
        return jsonify({'error': 'Device not found'}), 404
        
    # Load related data
    crossings = DeviceAccountCrossing.query.filter_by(device_id=device_id).all()
    accounts = [db.session.get(Account, c.account_id) for c in crossings]
    
    # Calculate
    calculator = RiskCalculator()
    matcher = DeviceMatcher() # In real app, load this from cache/db
    
    # Mocking ip_data for now
    ip_data = {'country': 'DE'}
    
    risk_result = calculator.calculate_device_risk(
        device.to_dict(), 
        [a.to_dict() for a in accounts if a],
        ip_data,
        matcher
    )
    
    # Update DB
    device.risk_score = risk_result['risk_score']
    device.risk_level = risk_result['risk_level']
    db.session.commit()
    
    return jsonify(risk_result)


@api_bp.route('/rules', methods=['GET'])
def get_rules():
    """Get the active list of risk scoring rules."""
    calculator = RiskCalculator()
    return jsonify(calculator.get_rules())


@api_bp.route('/search', methods=['GET'])
def search():
    """Global search for devices or accounts by hash."""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 4:
        return jsonify({'results': []})
    
    devices = Device.query.filter(Device.device_hash.ilike(f"%{query}%")).limit(5).all()
    accounts = Account.query.filter(Account.account_hash.ilike(f"%{query}%")).limit(5).all()
    
    results = []
    for d in devices:
        results.append({'type': 'device', 'id': d.device_id, 'hash': d.device_hash, 'label': f"{d.os} {d.browser}"})
    for a in accounts:
        results.append({'type': 'account', 'id': a.account_id, 'hash': a.account_hash, 'label': f"Account ({a.kyc_level})"})
        
    return jsonify({'results': results})


@api_bp.route('/stats/distribution', methods=['GET'])
def get_stats_distribution():
    """Get distribution data for charts (OS and Browser)."""
    os_dist = db.session.query(Device.os, func.count(Device.device_id)).group_by(Device.os).all()
    browser_dist = db.session.query(Device.browser, func.count(Device.device_id)).group_by(Device.browser).all()
    
    return jsonify({
        'os': [{'label': row[0], 'value': row[1]} for row in os_dist],
        'browser': [{'label': row[0], 'value': row[1]} for row in browser_dist]
    })


@api_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Fetch simulated high-risk alerts."""
    # In a real app, this would query a dedicated alerts table
    recent_risky = Device.query.filter(Device.risk_score > 60).order_by(Device.created_at.desc()).limit(10).all()
    
    alerts = []
    for d in recent_risky:
        alerts.append({
            'timestamp': d.created_at.isoformat(),
            'message': f"Critical risk detected on {d.os}/{d.browser}",
            'id': d.device_id,
            'score': float(d.risk_score)
        })
    return jsonify(alerts)
