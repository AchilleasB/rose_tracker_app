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

    @staticmethod
    def get_tracking_metadata(results: List[Results]) -> Dict[str, Any]:
        """Extract metadata from tracking results"""
        metadata = {
            'total_frames': len(results),
            'unique_objects': TrackingProcessor.count_unique_ids(results),
            'detections_per_frame': []
        }
        
        for result in results:
            frame_metadata = {
                'frame_number': result.frame_id if hasattr(result, 'frame_id') else None,
                'num_detections': len(result.boxes),
                'object_ids': result.boxes.id.int().cpu().tolist() if result.boxes.id is not None else []
            }
            metadata['detections_per_frame'].append(frame_metadata)
        
        return metadata

    @staticmethod
    def filter_results_by_confidence(results: List[Results], min_confidence: float) -> List[Results]:
        """Filter results by minimum confidence threshold"""
        filtered_results = []
        for result in results:
            if result.boxes.conf is not None:
                mask = result.boxes.conf > min_confidence
                result.boxes = result.boxes[mask]
                filtered_results.append(result)
        return filtered_results 