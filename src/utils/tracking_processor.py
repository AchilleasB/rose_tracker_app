from typing import List, Dict, Any
from ultralytics.engine.results import Results

class TrackingProcessor:
    """Utility class for processing tracking results"""
    
    @staticmethod
    def count_unique_ids(results: List[Results]) -> int:
        """Count unique tracked object IDs from results"""
        unique_ids = set()
        for result in results:
            if result.boxes.id is not None:
                unique_ids.update(result.boxes.id.int().cpu().tolist())
        return len(unique_ids)
