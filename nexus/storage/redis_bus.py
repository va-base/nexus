"""Redis event bus adapter"""
import json
from typing import Dict, Any, Optional, Callable
import redis
from nexus.config import settings


class RedisEventBus:
    """Redis Streams event bus"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.redis_url
        self.client = redis.from_url(self.redis_url, decode_responses=True)
    
    def publish(self, stream: str, event: Dict[str, Any]) -> str:
        """Publish an event to a stream"""
        message_id = self.client.xadd(stream, {"data": json.dumps(event)})
        return message_id
    
    def consume(self, stream: str, group: str, consumer: str, 
                callback: Callable[[Dict[str, Any]], None],
                block: int = 5000, count: int = 10):
        """Consume events from a stream"""
        try:
            self.client.xgroup_create(stream, group, id='0', mkstream=True)
        except redis.exceptions.ResponseError:
            pass  # Group already exists
        
        while True:
            messages = self.client.xreadgroup(
                group, consumer, {stream: '>'}, 
                block=block, count=count
            )
            
            for stream_name, stream_messages in messages:
                for message_id, message_data in stream_messages:
                    try:
                        event = json.loads(message_data['data'])
                        callback(event)
                        self.client.xack(stream, group, message_id)
                    except Exception as e:
                        print(f"Error processing message {message_id}: {e}")
    
    def get_stream_length(self, stream: str) -> int:
        """Get the length of a stream"""
        return self.client.xlen(stream)
    
    def close(self):
        """Close the Redis connection"""
        self.client.close()
