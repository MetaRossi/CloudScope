import logging
from typing import Callable, TypeVar, Any
from typing import Dict

# Define a type variable for class methods
T = TypeVar('T', bound=Callable[..., Any])


def require_initialization(func):
    """Decorator to ensure a class or instance is initialized before method access."""
    def wrapper(*args, **kwargs):
        cls = args[0] if isinstance(args[0], type) else args[0].__class__
        if not cls.is_initialized():
            logging.warning(f"{cls.__name__} is not initialized.")
            return None
        return func(*args, **kwargs)
    return wrapper


class SingletonMeta(type):
    """
    A metaclass that creates a Singleton instance of a class.
    Singleton pattern is a design pattern that restricts the instantiation of a class to a single instance.
    Forces initialization of the instance before accessing any methods or attributes.
    """
    _instances: Dict[Any, Any] = {}  # Dictionary to hold the instances of the classes
    _is_initialized: Dict[Any, bool] = {}  # Dictionary to hold the initialization status of the instances

    def __call__(cls, *args, **kwargs):
        """Overrides the call method to return the existing instance if it exists, else creates a new one."""
        # If the class instance does not exist in the dictionary
        if cls not in cls._instances:
            # Create a new instance
            instance = super().__call__(*args, **kwargs)
            # Store the instance in the dictionary
            cls._instances[cls] = instance
            # Mark as not initialized
            cls._is_initialized[cls] = False

        # Return the instance of the class
        return cls._instances[cls]

    @property
    def instance(cls):
        """
        Ensure the singleton instance is returned
        This allows access to the instance through the class

        Example usage:
        @classmethod
        def update_setting1(cls, value: str):
            cls.instance.setting1 = value
        """
        return cls()

    def initialize(cls, **kwargs):
        """Initialize the singleton instance with given keyword arguments, only if it hasn't been initialized."""
        if not cls._is_initialized.get(cls, False):
            instance = cls.instance
            instance.initialize(**kwargs)
            cls._is_initialized[cls] = True
        else:
            logging.warning(f"{cls.__name__} is already initialized.")

    @property
    def is_initialized(cls) -> bool:
        """Check if the singleton instance has been initialized."""
        return cls._is_initialized.get(cls, False)
