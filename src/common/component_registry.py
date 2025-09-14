"""
Component Registry System

A central registry for managing inter-component dependencies and services.
This enables clean dependency injection, service discovery, and loose coupling
between different parts of the MCP server.
"""

import logging
from typing import Dict, Any, Optional, Type, TypeVar, Callable, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
import threading
from enum import Enum

# Setup logging
try:
    from src.common.config_manager import _logger
except ImportError:
    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger(__name__)

T = TypeVar('T')


class ComponentType(str, Enum):
    """Types of components that can be registered."""
    
    DATABASE = "database"
    HTTP_CLIENT = "http_client"
    CONFIGURATION = "configuration"
    CACHE = "cache"
    LOGGER = "logger"
    PLUGIN = "plugin"
    SERVICE = "service"
    CUSTOM = "custom"


class ComponentLifecycle(str, Enum):
    """Component lifecycle states."""
    
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ComponentInfo:
    """Information about a registered component."""
    
    name: str
    component_type: ComponentType
    instance: Any
    lifecycle: ComponentLifecycle = ComponentLifecycle.REGISTERED
    dependencies: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}


class ComponentRegistry:
    """
    Central registry for managing components and their dependencies.
    
    Provides:
    - Service registration and discovery
    - Dependency injection
    - Lifecycle management
    - Event notifications
    """
    
    _instance: Optional['ComponentRegistry'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'ComponentRegistry':
        """Singleton pattern implementation."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """Initialize the component registry."""
        if self._initialized:
            return
            
        self._components: Dict[str, ComponentInfo] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()
        self._initialized = True
        
        _logger.info("Component registry initialized")
    
    def register_component(
        self,
        name: str,
        instance: Any,
        component_type: ComponentType = ComponentType.CUSTOM,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a component in the registry.
        
        Args:
            name: Unique component name
            instance: Component instance  
            component_type: Type of component
            dependencies: List of dependency component names
            metadata: Additional component metadata
        """
        with self._lock:
            if name in self._components:
                _logger.warning(f"Component '{name}' is already registered, replacing")
            
            component_info = ComponentInfo(
                name=name,
                component_type=component_type,
                instance=instance,
                dependencies=dependencies or [],
                metadata=metadata or {}
            )
            
            self._components[name] = component_info
            
            _logger.info(f"Registered component '{name}' of type '{component_type}'")
            self._emit_event("component_registered", {"name": name, "type": component_type})
    
    def get_component(self, name: str) -> Optional[Any]:
        """
        Get a component by name.
        
        Args:
            name: Component name
            
        Returns:
            Component instance or None if not found
        """
        with self._lock:
            component_info = self._components.get(name)
            return component_info.instance if component_info else None
    
    def get_component_info(self, name: str) -> Optional[ComponentInfo]:
        """
        Get component information by name.
        
        Args:
            name: Component name
            
        Returns:
            ComponentInfo or None if not found
        """
        with self._lock:
            return self._components.get(name)
    
    def get_components_by_type(self, component_type: ComponentType) -> Dict[str, Any]:
        """
        Get all components of a specific type.
        
        Args:
            component_type: Component type to filter by
            
        Returns:
            Dictionary of component name -> instance
        """
        with self._lock:
            return {
                name: info.instance
                for name, info in self._components.items()
                if info.component_type == component_type
            }
    
    def remove_component(self, name: str) -> bool:
        """
        Remove a component from the registry.
        
        Args:
            name: Component name to remove
            
        Returns:
            True if component was removed, False if not found
        """
        with self._lock:
            if name in self._components:
                component_info = self._components.pop(name)
                _logger.info(f"Removed component '{name}'")
                self._emit_event("component_removed", {"name": name})
                return True
            return False
    
    def update_lifecycle(self, name: str, lifecycle: ComponentLifecycle) -> bool:
        """
        Update component lifecycle state.
        
        Args:
            name: Component name
            lifecycle: New lifecycle state
            
        Returns:
            True if updated, False if component not found
        """
        with self._lock:
            if name in self._components:
                old_lifecycle = self._components[name].lifecycle
                self._components[name].lifecycle = lifecycle
                
                _logger.debug(f"Component '{name}' lifecycle: {old_lifecycle} -> {lifecycle}")
                self._emit_event("lifecycle_changed", {
                    "name": name,
                    "old_state": old_lifecycle,
                    "new_state": lifecycle
                })
                return True
            return False
    
    def check_dependencies(self, name: str) -> Dict[str, bool]:
        """
        Check if all dependencies for a component are satisfied.
        
        Args:
            name: Component name
            
        Returns:
            Dictionary of dependency name -> availability status
        """
        with self._lock:
            component_info = self._components.get(name)
            if not component_info:
                return {}
            
            dependency_status = {}
            for dep_name in component_info.dependencies:
                dependency_status[dep_name] = dep_name in self._components
                
            return dependency_status
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Get the complete dependency graph.
        
        Returns:
            Dictionary of component name -> list of dependencies
        """
        with self._lock:
            return {
                name: info.dependencies.copy()
                for name, info in self._components.items()
            }
    
    def initialize_components(self) -> Dict[str, bool]:
        """
        Initialize all components in dependency order.
        
        Returns:
            Dictionary of component name -> initialization success status
        """
        initialization_results = {}
        
        # Topological sort for dependency order
        sorted_components = self._topological_sort()
        
        for component_name in sorted_components:
            try:
                self.update_lifecycle(component_name, ComponentLifecycle.INITIALIZING)
                
                component_info = self._components[component_name]
                component = component_info.instance
                
                # Call initialize method if available
                if hasattr(component, 'initialize'):
                    component.initialize()
                
                self.update_lifecycle(component_name, ComponentLifecycle.INITIALIZED)
                initialization_results[component_name] = True
                
                _logger.info(f"Initialized component '{component_name}'")
                
            except Exception as e:
                _logger.error(f"Failed to initialize component '{component_name}': {e}")
                self.update_lifecycle(component_name, ComponentLifecycle.ERROR)
                initialization_results[component_name] = False
        
        return initialization_results
    
    def shutdown_components(self) -> Dict[str, bool]:
        """
        Shutdown all components in reverse dependency order.
        
        Returns:
            Dictionary of component name -> shutdown success status
        """
        shutdown_results = {}
        
        # Reverse dependency order
        sorted_components = list(reversed(self._topological_sort()))
        
        for component_name in sorted_components:
            try:
                self.update_lifecycle(component_name, ComponentLifecycle.STOPPING)
                
                component_info = self._components[component_name]
                component = component_info.instance
                
                # Call shutdown method if available
                if hasattr(component, 'shutdown'):
                    component.shutdown()
                elif hasattr(component, 'close'):
                    component.close()
                
                self.update_lifecycle(component_name, ComponentLifecycle.STOPPED)
                shutdown_results[component_name] = True
                
                _logger.info(f"Shutdown component '{component_name}'")
                
            except Exception as e:
                _logger.error(f"Failed to shutdown component '{component_name}': {e}")
                self.update_lifecycle(component_name, ComponentLifecycle.ERROR)
                shutdown_results[component_name] = False
        
        return shutdown_results
    
    def _topological_sort(self) -> List[str]:
        """
        Perform topological sort of components based on dependencies.
        
        Returns:
            List of component names in dependency order
        """
        # Simplified topological sort (Kahn's algorithm)
        in_degree = {name: 0 for name in self._components}
        
        # Calculate in-degrees
        for name, info in self._components.items():
            for dep in info.dependencies:
                if dep in in_degree:
                    in_degree[name] += 1
        
        # Queue of nodes with no incoming edges
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            # Reduce in-degree for dependents
            for name, info in self._components.items():
                if current in info.dependencies:
                    in_degree[name] -= 1
                    if in_degree[name] == 0:
                        queue.append(name)
        
        return result
    
    def add_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        Add an event handler for component events.
        
        Args:
            event_type: Type of event to listen for
            handler: Callable to handle the event
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        
        self._event_handlers[event_type].append(handler)
        _logger.debug(f"Added event handler for '{event_type}'")
    
    def remove_event_handler(self, event_type: str, handler: Callable) -> bool:
        """
        Remove an event handler.
        
        Args:
            event_type: Event type
            handler: Handler to remove
            
        Returns:
            True if handler was removed, False if not found
        """
        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
                _logger.debug(f"Removed event handler for '{event_type}'")
                return True
            except ValueError:
                pass
        return False
    
    def _emit_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Emit an event to all registered handlers.
        
        Args:
            event_type: Type of event
            event_data: Event data
        """
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event_data)
            except Exception as e:
                _logger.error(f"Error in event handler for '{event_type}': {e}")
    
    def get_status_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the registry status.
        
        Returns:
            Dictionary with registry status information
        """
        with self._lock:
            lifecycle_counts = {}
            type_counts = {}
            
            for info in self._components.values():
                # Count by lifecycle
                lifecycle_counts[info.lifecycle] = lifecycle_counts.get(info.lifecycle, 0) + 1
                
                # Count by type
                type_counts[info.component_type] = type_counts.get(info.component_type, 0) + 1
            
            return {
                "total_components": len(self._components),
                "lifecycle_distribution": lifecycle_counts,
                "type_distribution": type_counts,
                "registered_events": list(self._event_handlers.keys()),
                "components": list(self._components.keys())
            }
    
    def clear(self) -> None:
        """Clear all registered components (for testing)."""
        with self._lock:
            self._components.clear()
            self._event_handlers.clear()
            _logger.info("Component registry cleared")


# Convenience functions for common patterns

def register_database_pool(name: str, pool: Any) -> None:
    """Register a database connection pool."""
    registry = ComponentRegistry()
    registry.register_component(
        name=name,
        instance=pool,
        component_type=ComponentType.DATABASE,
        metadata={"pool_type": type(pool).__name__}
    )


def register_http_client(name: str, client: Any, dependencies: Optional[List[str]] = None) -> None:
    """Register an HTTP client."""
    registry = ComponentRegistry()
    registry.register_component(
        name=name,
        instance=client,
        component_type=ComponentType.HTTP_CLIENT,
        dependencies=dependencies or [],
        metadata={"client_type": type(client).__name__}
    )


def register_configuration(name: str, config: Any) -> None:
    """Register a configuration object."""
    registry = ComponentRegistry()
    registry.register_component(
        name=name,
        instance=config,
        component_type=ComponentType.CONFIGURATION,
        metadata={"config_type": type(config).__name__}
    )


def get_database_pool(name: str = "default") -> Optional[Any]:
    """Get a database pool by name."""
    registry = ComponentRegistry()
    return registry.get_component(name)


def get_http_client(name: str = "default") -> Optional[Any]:
    """Get an HTTP client by name."""
    registry = ComponentRegistry()
    return registry.get_component(name)


def get_configuration(name: str = "default") -> Optional[Any]:
    """Get a configuration object by name."""
    registry = ComponentRegistry()
    return registry.get_component(name)


# Decorators for automatic registration

def register_as_component(
    name: str,
    component_type: ComponentType = ComponentType.CUSTOM,
    dependencies: Optional[List[str]] = None
):
    """
    Decorator to automatically register a class instance as a component.
    
    Args:
        name: Component name
        component_type: Component type
        dependencies: List of dependency names
    """
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            
            # Register after initialization
            registry = ComponentRegistry()
            registry.register_component(
                name=name,
                instance=self,
                component_type=component_type,
                dependencies=dependencies or []
            )
        
        cls.__init__ = new_init
        return cls
    
    return decorator


if __name__ == "__main__":
    """Example usage and testing."""
    
    # Example components
    class DatabasePool:
        def __init__(self, connection_string: str):
            self.connection_string = connection_string
        
        def initialize(self):
            print(f"Initializing database pool: {self.connection_string}")
        
        def shutdown(self):
            print("Shutting down database pool")
    
    class HTTPClient:
        def __init__(self, base_url: str):
            self.base_url = base_url
        
        def initialize(self):
            print(f"Initializing HTTP client: {self.base_url}")
    
    # Create registry
    registry = ComponentRegistry()
    
    # Register components
    db_pool = DatabasePool("postgresql://localhost/test")
    http_client = HTTPClient("https://api.example.com")
    
    registry.register_component("database", db_pool, ComponentType.DATABASE)
    registry.register_component(
        "http_client",
        http_client,
        ComponentType.HTTP_CLIENT,
        dependencies=["database"]  # HTTP client depends on database
    )
    
    # Show status
    print("Registry Status:")
    import json
    print(json.dumps(registry.get_status_summary(), indent=2))
    
    # Initialize components
    print("\nInitializing components:")
    init_results = registry.initialize_components()
    print(f"Initialization results: {init_results}")
    
    # Shutdown components
    print("\nShutting down components:")
    shutdown_results = registry.shutdown_components()
    print(f"Shutdown results: {shutdown_results}")
    
    # Example of using convenience functions
    print("\nUsing convenience functions:")
    register_database_pool("main_db", db_pool)
    retrieved_pool = get_database_pool("main_db")
    print(f"Retrieved pool: {retrieved_pool}")
