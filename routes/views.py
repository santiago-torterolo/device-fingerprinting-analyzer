"""
HTML view routes for device fingerprinting dashboard.
Renders templates with device, account, and risk data.
"""

from flask import render_template, jsonify, request
from routes import views_bp
from app import db
from src.models import Device, Account, DeviceAccountCrossing


@views_bp.route('/', methods=['GET'])
def index():
    """
    Dashboard home page.
    Displays overview statistics and charts.
    """
    try:
        device_count = db.session.query(Device).count()
        account_count = db.session.query(Account).count()
        crossing_count = db.session.query(DeviceAccountCrossing).count()
        
        risk_distribution = db.session.query(
            Device.risk_level,
            db.func.count(Device.device_id).label('count')
        ).group_by(Device.risk_level).all()
        
        risk_data = {
            'low': 0,
            'medium': 0,
            'high': 0
        }
        for level, count in risk_distribution:
            if level:
                risk_data[level] = count
        
        top_devices = db.session.query(Device).order_by(
            Device.risk_score.desc()
        ).limit(10).all()
        
        stats = {
            'total_devices': device_count,
            'total_accounts': account_count,
            'total_crossings': crossing_count,
            'risk_distribution': risk_data,
            'avg_risk': db.session.query(
                db.func.avg(Device.risk_score)
            ).scalar() or 0.0
        }
        
        return render_template(
            'index.html',
            stats=stats,
            top_devices=[d.to_dict() for d in top_devices]
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@views_bp.route('/graph', methods=['GET'])
def graph():
    """
    Interactive force-directed graph page.
    Shows device-account network visualization.
    """
    return render_template('graph.html')


@views_bp.route('/accounts', methods=['GET'])
def accounts():
    """
    Accounts crossing analysis page.
    DataTable with account details and crossing information.
    """
    account_count = db.session.query(Account).count()
    return render_template('accounts.html', stats={'total_accounts': account_count})


@views_bp.route('/devices/<device_id>', methods=['GET'])
def device_detail(device_id):
    """
    Device detail page.
    Shows device specs and associated accounts.
    """
    try:
        device = db.session.query(Device).filter_by(device_id=device_id).first()
        
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        crossings = db.session.query(DeviceAccountCrossing).filter_by(
            device_id=device_id
        ).all()
        
        associated_accounts = [
            {
                'account': db.session.query(Account).filter_by(
                    account_id=c.account_id
                ).first().to_dict(),
                'crossing': c.to_dict()
            }
            for c in crossings
        ]
        
        return render_template(
            'devices.html',
            device=device.to_dict(),
            associated_accounts=associated_accounts
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@views_bp.route('/risk-report', methods=['GET'])
def risk_report():
    """
    Risk report page.
    Displays heatmaps, distributions, and export options.
    """
    return render_template('risk-report.html')


@views_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    Verifies application and database connectivity.
    """
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'database': 'connected'
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500