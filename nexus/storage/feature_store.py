"""Feature store adapter"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from nexus.storage.postgres import PostgresStore


class FeatureStore:
    """Feature store for computed metrics"""
    
    def __init__(self, postgres_store: Optional[PostgresStore] = None):
        self.store = postgres_store or PostgresStore()
    
    def write_feature(self, entity_type: str, entity_id: UUID, 
                     feature_name: str, feature_value: float,
                     feature_metadata: Optional[Dict[str, Any]] = None,
                     valid_until: Optional[datetime] = None):
        """Write a feature value"""
        import json
        query = """
            INSERT INTO features (entity_type, entity_id, feature_name, feature_value,
                                 feature_metadata, computed_at, valid_until)
            VALUES (:entity_type, :entity_id, :feature_name, :feature_value,
                    :feature_metadata, :computed_at, :valid_until)
        """
        self.store.execute(query, {
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "feature_name": feature_name,
            "feature_value": feature_value,
            "feature_metadata": json.dumps(feature_metadata or {}),
            "computed_at": datetime.utcnow(),
            "valid_until": valid_until
        })
    
    def read_feature(self, entity_type: str, entity_id: UUID, 
                    feature_name: str) -> Optional[float]:
        """Read the latest feature value"""
        query = """
            SELECT feature_value
            FROM features
            WHERE entity_type = :entity_type
              AND entity_id = :entity_id
              AND feature_name = :feature_name
              AND (valid_until IS NULL OR valid_until > NOW())
            ORDER BY computed_at DESC
            LIMIT 1
        """
        result = self.store.fetch_one(query, {
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "feature_name": feature_name
        })
        return result[0] if result else None
