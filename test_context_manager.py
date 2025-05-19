#!/usr/bin/env python3
import context_manager as cm
import time
import threading
import logging
import json
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def callback_function(changed_keys, source_agent):
    """Example callback for context changes"""
    logger.info(f"Context change callback: {changed_keys} from {source_agent}")

def test_basic_operations():
    """Test basic operations of the context manager"""
    logger.info("Testing basic operations...")
    
    # Clear existing context
    cm.clear_context()
    
    # Add a test entry
    test_data = {"test_agent": {"status": "active", "value": 42}}
    cm.update_context(test_data, "test_script")
    
    # Retrieve and verify
    context = cm.get_context()
    assert "test_agent" in context, "Failed to store data in context"
    assert context["test_agent"]["value"] == 42, "Failed to retrieve correct value"
    
    # Test path-based access
    value = cm.get_context("test_agent.value")
    assert value == 42, "Path-based access failed"
    
    # Test nested updates
    cm.update_context({"test_agent": {"nested": {"deep": "value"}}}, "test_script")
    deep_value = cm.get_context("test_agent.nested.deep")
    assert deep_value == "value", "Nested update failed"
    
    logger.info("Basic operations passed!")

def test_subscriptions():
    """Test subscription and notification system"""
    logger.info("Testing subscriptions...")
    
    # Clear existing context
    cm.clear_context()
    
    # Set up a subscription
    cm.subscribe(callback_function, "subscriber_agent", ["test_agent"])
    
    # Update something that should trigger the subscription
    cm.update_context({"test_agent": {"triggered": True}}, "other_agent")
    
    # Update something that shouldn't trigger the subscription
    cm.update_context({"unrelated_agent": {"data": "value"}}, "other_agent")
    
    # Clean up
    cm.unsubscribe("subscriber_agent")
    
    logger.info("Subscription test complete - check logs for callback execution")

def test_persistence():
    """Test saving and loading context"""
    logger.info("Testing persistence...")
    
    # Set up a test context
    cm.clear_context()
    test_data = {
        "agent1": {"value": 100},
        "agent2": {"nested": {"data": "test"}}
    }
    cm.update_context(test_data, "test_script")
    
    # Save to a test file
    test_file = "data/test_context.json"
    saved_path = cm.save_context_to_file(test_file)
    assert os.path.exists(saved_path), "Context file wasn't saved"
    
    # Read the file directly to verify
    with open(saved_path, 'r') as f:
        saved_data = json.load(f)
    
    assert "agent1" in saved_data, "Data not properly saved"
    assert saved_data["agent1"]["value"] == 100, "Incorrect data saved"
    
    # Clean up
    if os.path.exists(saved_path):
        os.remove(saved_path)
    
    logger.info("Persistence test passed!")

def test_thread_safety():
    """Test thread safety with multiple threads updating the context"""
    logger.info("Testing thread safety...")
    
    # Clear existing context
    cm.clear_context()
    
    # Initialize the thread_test section in the context
    cm.update_context({"thread_test": {}}, "test_script")
    
    def worker(agent_id, iterations):
        """Worker function to update context from a thread"""
        for i in range(iterations):
            cm.update_context({
                "thread_test": {
                    agent_id: {
                        "iteration": i,
                        "timestamp": time.time()
                    }
                }
            }, agent_id)
            time.sleep(0.01)  # Small delay
    
    # Create and start multiple threads
    threads = []
    for i in range(5):
        agent_id = f"agent_{i}"
        t = threading.Thread(target=worker, args=(agent_id, 10))
        threads.append(t)
        t.start()
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    # Verify results
    context = cm.get_context("thread_test")
    for i in range(5):
        agent_id = f"agent_{i}"
        assert agent_id in context, f"Missing data for {agent_id}"
        assert context[agent_id]["iteration"] == 9, f"Incorrect final iteration for {agent_id}"
    
    logger.info("Thread safety test passed!")

def main():
    """Run all tests"""
    logger.info("Starting context manager tests...")
    
    # Run tests
    test_basic_operations()
    test_subscriptions()
    test_persistence()
    test_thread_safety()
    
    logger.info("All tests completed successfully!")

if __name__ == "__main__":
    main() 