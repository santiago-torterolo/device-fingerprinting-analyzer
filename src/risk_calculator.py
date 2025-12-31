"""
Risk scoring engine for device fingerprinting.
Calculates fraud risk based on device characteristics and account behavior.
"""

from typing import Dict, List, Any


class RiskCalculator:
    """Main risk calculation engine."""
    
    def __init__(self):
        self.weights = {
            'vpn': 25.0,
            'datacenter': 30.0,
            'multi_account': 20.0,
            'new_account': 15.0,
            'high_velocity': 10.0,
            'suspicious_os': 8.0
        }
    
    def calculate_device_risk(self, device: Dict, accounts: List[Dict], 
                            ip_data: Dict, matcher=None) -> Dict[str, Any]:
        """Calculate comprehensive risk score for device."""
        score = 0.0
        
        # VPN/Datacenter risk
        if device.get('is_vpn'):
            score += self.weights['vpn']
        if device.get('is_datacenter'):
            score += self.weights['datacenter']
        
        # Multi-account risk
        account_count = len(accounts)
        if account_count > 3:
            score += self.weights['multi_account'] * (account_count / 3)
        
        # Account quality risk
        suspicious_accounts = sum(1 for acc in accounts 
                                if acc.get('risk_score', 0) > 60)
        if suspicious_accounts > 0:
            score += 15.0
        
        # Risk level determination
        if score >= 70:
            risk_level = 'high'
        elif score >= 40:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'risk_score': round(score, 2),
            'risk_level': risk_level,
            'factors': {
                'vpn': device.get('is_vpn', False),
                'datacenter': device.get('is_datacenter', False),
                'account_count': account_count,
                'suspicious_accounts': suspicious_accounts
            }
        }
    def get_rules(self) -> List[Dict]:
        """Return the current set of risk rules and their weights."""
        return [
            {'rule': 'VPN Detection', 'weight': self.weights['vpn'], 'category': 'Network'},
            {'rule': 'Datacenter IP', 'weight': self.weights['datacenter'], 'category': 'Network'},
            {'rule': 'Multi-account Device (>3)', 'weight': self.weights['multi_account'], 'category': 'Behavior'},
            {'rule': 'New Account link', 'weight': self.weights['new_account'], 'category': 'Identity'},
            {'rule': 'High velocity crossings', 'weight': self.weights['high_velocity'], 'category': 'Behavior'},
            {'rule': 'Suspicious OS/UA', 'weight': self.weights['suspicious_os'], 'category': 'Device'},
        ]
