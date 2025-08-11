"""
Glasses Stream System
A modular system for capturing and processing iPhone screen mirror streams
"""

__version__ = "0.1.0"

from .core.config import StreamConfig
from .core.capture import StreamCapture
from .renderers.overlay import OverlayRenderer
from .controllers.movement import MovementController

__all__ = [
    'StreamConfig',
    'StreamCapture', 
    'OverlayRenderer',
    'MovementController'
]