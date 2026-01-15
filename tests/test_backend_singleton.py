import pytest
from mkv_episode_matcher.backend.dependencies import get_engine, get_engine_status
from mkv_episode_matcher.core.engine import MatchEngineV2
import threading

def test_engine_singleton():
    """Verify that get_engine returns the same instance."""
    engine1 = get_engine()
    engine2 = get_engine()
    
    assert engine1 is engine2
    assert isinstance(engine1, MatchEngineV2)

def test_engine_status_updates():
    """Verify status reports correctly."""
    status = get_engine_status()
    # Since we called get_engine above, it should be ready
    assert status["status"] == "ready"
    assert status["loaded"] is True

def test_singleton_thread_safety():
    """Verify singleton handles concurrent access (simulated)."""
    instances = []
    
    def get_instance():
        instances.append(get_engine())
        
    threads = [threading.Thread(target=get_instance) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    # All instances should be identical
    first = instances[0]
    for inst in instances[1:]:
        assert inst is first
