"""
Fusion Combustibles Lector Package

This package provides a Python bridge to interact with Wayne Fusion fuel dispenser controllers
using pythonnet to load and communicate with the Wayne DLL.
"""

__version__ = "0.1.0"
__author__ = "Kernel Informatica"

from .fusion_controller import FusionController

__all__ = ["FusionController"]
