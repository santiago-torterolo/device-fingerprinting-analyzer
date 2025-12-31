"""
Device fingerprint matching utilities.
Detects similar devices sharing suspicious attributes.
"""

class DeviceMatcher:
    """Matches devices based on fingerprint similarity."""
    
    def __init__(self):
        self.similarity_threshold = 0.85
    
    def calculate_similarity(self, device1: dict, device2: dict) -> float:
        """Calculate fingerprint similarity score."""
        matches = 0
        total = 0
        
        for field in ['os', 'browser', 'screen_resolution', 'timezone']:
            if device1.get(field) == device2.get(field):
                matches += 1
            total += 1
        
        return matches / total if total > 0 else 0.0
    
    def are_related(self, device1: dict, device2: dict) -> bool:
        """Check if two devices are likely the same."""
        similarity = self.calculate_similarity(device1, device2)
        return similarity >= self.similarity_threshold
