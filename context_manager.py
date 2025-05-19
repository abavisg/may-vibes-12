import json
import os
import threading
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import copy

logger = logging.getLogger(__name__)

class ContextManager:
    """
    Manages a shared context dictionary accessible to all agents in the system.
    Provides thread-safe access and persistence capabilities.
    """
    
    # Singleton instance
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ContextManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._context = {}
        self._subscribers = {}
        self._context_file = "data/agent_context.json"
        self._backup_directory = "data/context_backups"
        self._initialized = True
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(self._context_file), exist_ok=True)
        os.makedirs(self._backup_directory, exist_ok=True)
        
        # Load existing context if available
        self._load_context()
    
    def get_context(self, path: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the current context or a specific portion of it.
        
        Args:
            path: Optional dot-notation path to get a specific part of the context
                 (e.g., "focus_agent.state.active")
        
        Returns:
            A copy of the requested context to prevent direct modification
        """
        with self._lock:
            if path is None:
                return copy.deepcopy(self._context)
            
            # Navigate through nested dictionaries with the path
            parts = path.split('.')
            current = self._context
            
            try:
                for part in parts:
                    current = current[part]
                return copy.deepcopy(current)
            except (KeyError, TypeError):
                logger.warning(f"Path {path} not found in context")
                return {}
    
    def update_context(self, update: Dict[str, Any], agent_id: str = "system") -> None:
        """
        Update the context with new values.
        
        Args:
            update: Dictionary of updates to apply to the context
            agent_id: ID of the agent making the update (for logging)
        """
        with self._lock:
            if not update:
                return
                
            # Add metadata about the update
            timestamp = datetime.now().isoformat()
            
            # Log the update
            logger.info(f"Context update by {agent_id} at {timestamp}")
            
            # Track what changed for notifications
            changed_keys = self._deep_update(self._context, update)
            
            # Add metadata about this update
            if "metadata" not in self._context:
                self._context["metadata"] = {}
            
            self._context["metadata"]["last_updated"] = timestamp
            self._context["metadata"]["last_updated_by"] = agent_id
            
            # Notify subscribers about the changes
            self._notify_subscribers(changed_keys, agent_id)
    
    def _deep_update(self, target: Dict[str, Any], update: Dict[str, Any], 
                    prefix: str = "") -> list:
        """
        Recursively update nested dictionaries and track changed keys.
        
        Args:
            target: Target dictionary to update
            update: Dictionary with updates to apply
            prefix: Current path prefix for tracking
            
        Returns:
            List of changed keys with their paths
        """
        changed_keys = []
        
        for key, value in update.items():
            path = f"{prefix}.{key}" if prefix else key
            
            # If both are dictionaries, recursively update
            if (key in target and isinstance(target[key], dict) and 
                isinstance(value, dict)):
                nested_changes = self._deep_update(target[key], value, path)
                changed_keys.extend(nested_changes)
            else:
                # Check if value is actually changing
                if key not in target or target[key] != value:
                    target[key] = value
                    changed_keys.append(path)
        
        return changed_keys
    
    def save_context_to_file(self, filename: Optional[str] = None) -> str:
        """
        Save the current context to a file.
        
        Args:
            filename: Optional custom filename, otherwise uses default
            
        Returns:
            Path to the saved file
        """
        with self._lock:
            # Use provided filename or default
            target_file = filename or self._context_file
            
            try:
                with open(target_file, 'w') as f:
                    json.dump(self._context, f, indent=2)
                logger.info(f"Context saved to {target_file}")
                
                # Create a timestamped backup
                self._create_backup()
                
                return target_file
            except Exception as e:
                logger.error(f"Failed to save context: {e}")
                return ""
    
    def _load_context(self) -> None:
        """Load context from the default file if it exists."""
        try:
            if os.path.exists(self._context_file):
                with open(self._context_file, 'r') as f:
                    loaded_context = json.load(f)
                    self._context = loaded_context
                    logger.info(f"Context loaded from {self._context_file}")
        except Exception as e:
            logger.error(f"Failed to load context: {e}")
    
    def _create_backup(self) -> None:
        """Create a timestamped backup of the current context."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self._backup_directory, f"context_{timestamp}.json")
        
        try:
            with open(backup_file, 'w') as f:
                json.dump(self._context, f, indent=2)
            logger.debug(f"Context backup created at {backup_file}")
        except Exception as e:
            logger.error(f"Failed to create context backup: {e}")
    
    def clear_context(self, path: Optional[str] = None) -> None:
        """
        Clear the entire context or a specific part of it.
        
        Args:
            path: Optional dot-notation path to clear a specific part of the context
                 (e.g., "focus_agent.state")
        """
        with self._lock:
            if path is None:
                # Clear everything except metadata
                metadata = self._context.get("metadata", {})
                self._context.clear()
                self._context["metadata"] = metadata
                self._context["metadata"]["cleared_at"] = datetime.now().isoformat()
                logger.info("Context cleared")
            else:
                # Navigate to and clear the specified path
                parts = path.split('.')
                current = self._context
                
                try:
                    # Navigate to the parent of the target
                    for part in parts[:-1]:
                        current = current[part]
                    
                    # Clear the target
                    if parts[-1] in current:
                        del current[parts[-1]]
                        logger.info(f"Cleared context at path: {path}")
                except (KeyError, TypeError):
                    logger.warning(f"Path {path} not found for clearing")
    
    def subscribe(self, callback, agent_id: str, paths: Optional[list] = None) -> None:
        """
        Subscribe to context changes.
        
        Args:
            callback: Function to call when context changes
            agent_id: ID of the subscribing agent
            paths: Optional list of paths to subscribe to (if None, subscribes to all changes)
        """
        with self._lock:
            self._subscribers[agent_id] = {
                "callback": callback,
                "paths": paths
            }
            logger.debug(f"Agent {agent_id} subscribed to context changes")
    
    def unsubscribe(self, agent_id: str) -> None:
        """
        Unsubscribe from context changes.
        
        Args:
            agent_id: ID of the agent to unsubscribe
        """
        with self._lock:
            if agent_id in self._subscribers:
                del self._subscribers[agent_id]
                logger.debug(f"Agent {agent_id} unsubscribed from context changes")
    
    def _notify_subscribers(self, changed_keys: list, source_agent_id: str) -> None:
        """
        Notify subscribers about context changes.
        
        Args:
            changed_keys: List of changed keys with their paths
            source_agent_id: ID of the agent that made the changes
        """
        if not changed_keys:
            return
            
        for agent_id, subscription in self._subscribers.items():
            # Don't notify the agent that made the changes
            if agent_id == source_agent_id:
                continue
                
            callback = subscription["callback"]
            subscribed_paths = subscription["paths"]
            
            # If subscribed to all changes or if any of the changed keys match subscribed paths
            if subscribed_paths is None or any(
                any(key.startswith(path) for path in subscribed_paths)
                for key in changed_keys
            ):
                try:
                    callback(changed_keys, source_agent_id)
                except Exception as e:
                    logger.error(f"Error in context change callback for {agent_id}: {e}")


# Create a singleton instance
_context_manager = ContextManager()

# Public API functions that use the singleton

def get_context(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the current context or a specific portion of it.
    
    Args:
        path: Optional dot-notation path to get a specific part of the context
             (e.g., "focus_agent.state.active")
    
    Returns:
        A copy of the requested context
    """
    return _context_manager.get_context(path)

def update_context(update: Dict[str, Any], agent_id: str = "system") -> None:
    """
    Update the context with new values.
    
    Args:
        update: Dictionary of updates to apply to the context
        agent_id: ID of the agent making the update (for logging)
    """
    _context_manager.update_context(update, agent_id)

def save_context_to_file(filename: Optional[str] = None) -> str:
    """
    Save the current context to a file.
    
    Args:
        filename: Optional custom filename, otherwise uses default
        
    Returns:
        Path to the saved file
    """
    return _context_manager.save_context_to_file(filename)

def clear_context(path: Optional[str] = None) -> None:
    """
    Clear the entire context or a specific part of it.
    
    Args:
        path: Optional dot-notation path to clear a specific part of the context
             (e.g., "focus_agent.state")
    """
    _context_manager.clear_context(path)

def subscribe(callback, agent_id: str, paths: Optional[list] = None) -> None:
    """
    Subscribe to context changes.
    
    Args:
        callback: Function to call when context changes
        agent_id: ID of the subscribing agent
        paths: Optional list of paths to subscribe to (if None, subscribes to all changes)
    """
    _context_manager.subscribe(callback, agent_id, paths)

def unsubscribe(agent_id: str) -> None:
    """
    Unsubscribe from context changes.
    
    Args:
        agent_id: ID of the agent to unsubscribe
    """
    _context_manager.unsubscribe(agent_id) 