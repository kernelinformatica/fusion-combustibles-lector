"""
FusionController: Main class for connecting to and reading data from Wayne Fusion controllers.

This module provides a Python interface to Wayne Fusion fuel dispenser controllers through
the Wayne DLL using pythonnet.
"""

import logging
from typing import Optional, Dict, Any
import clr  # pythonnet

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FusionControllerError(Exception):
    """Base exception for FusionController errors."""
    pass


class FusionConnectionError(FusionControllerError):
    """Raised when connection to the controller fails."""
    pass


class DLLLoadError(FusionControllerError):
    """Raised when the Wayne DLL cannot be loaded."""
    pass


class FusionController:
    """
    Interface to Wayne Fusion fuel dispenser controller.
    
    This class provides methods to connect to a Fusion controller via IP address
    and retrieve sales data using the Wayne DLL.
    
    Attributes:
        controller_ip (str): IP address of the Fusion controller
        dll_path (str): Path to the Wayne DLL file
        connected (bool): Connection status
    """
    
    def __init__(self, controller_ip: str, dll_path: str, dll_namespace: str = "Wayne.Fusion"):
        """
        Initialize the FusionController.
        
        Args:
            controller_ip (str): IP address of the Fusion controller
            dll_path (str): Path to the Wayne DLL file
            dll_namespace (str): Namespace and class name in the DLL (default: "Wayne.Fusion")
                               Format should be "Namespace.ClassName" or just "ClassName"
            
        Raises:
            DLLLoadError: If the DLL cannot be loaded
        """
        self.controller_ip = controller_ip
        self.dll_path = dll_path
        self.dll_namespace = dll_namespace
        self.connected = False
        self._fusion_instance = None
        
        logger.info(f"Initializing FusionController for IP: {controller_ip}")
        self._load_dll()
    
    def _load_dll(self):
        """
        Load the Wayne DLL using pythonnet.
        
        Raises:
            DLLLoadError: If the DLL cannot be loaded
        """
        try:
            logger.info(f"Loading Wayne DLL from: {self.dll_path}")
            # Add reference to the Wayne DLL
            clr.AddReference(self.dll_path)
            
            # Import the class from the DLL using the configured namespace
            # The namespace should be provided in the format "Namespace.ClassName" or "ClassName"
            logger.info(f"Importing class from namespace: {self.dll_namespace}")
            
            # Split namespace to get the module and class
            parts = self.dll_namespace.rsplit('.', 1)
            if len(parts) == 2:
                # Format: "Namespace.ClassName"
                module_name, class_name = parts
                # Dynamically import the module
                import importlib
                module = importlib.import_module(module_name)
                self._fusion_class = getattr(module, class_name)
            else:
                # Format: "ClassName" - import from root
                class_name = parts[0]
                # Try to import directly
                import sys
                # The class should be available in sys.modules after AddReference
                for mod_name, mod in sys.modules.items():
                    if hasattr(mod, class_name):
                        self._fusion_class = getattr(mod, class_name)
                        break
                else:
                    raise ImportError(f"Could not find class '{class_name}' in loaded DLL")
            
            logger.info(f"Wayne DLL loaded successfully. Class: {self._fusion_class}")
            
        except Exception as e:
            error_msg = (
                f"Failed to load Wayne DLL: {str(e)}\n"
                f"Please verify:\n"
                f"  1. DLL path is correct: {self.dll_path}\n"
                f"  2. DLL namespace is correct: {self.dll_namespace}\n"
                f"  3. pythonnet is properly installed\n"
                f"Common namespace formats:\n"
                f"  - 'Wayne.Fusion' for Wayne.dll with Fusion class\n"
                f"  - 'WayneFusion' for a class named WayneFusion\n"
                f"  - 'FusionController' for a class named FusionController"
            )
            logger.error(error_msg)
            raise DLLLoadError(error_msg) from e
    
    def connect(self) -> bool:
        """
        Establish connection to the Fusion controller.
        
        Returns:
            bool: True if connection is successful, False otherwise
            
        Raises:
            FusionConnectionError: If connection cannot be established
        """
        try:
            logger.info(f"Connecting to Fusion controller at {self.controller_ip}")
            
            # Create instance of the Fusion controller class
            # The actual method might vary - this is based on common patterns
            self._fusion_instance = self._fusion_class(self.controller_ip)
            
            # Attempt to connect
            # The actual method name should be verified from Wayne DLL documentation
            if hasattr(self._fusion_instance, 'Connect'):
                result = self._fusion_instance.Connect()
            elif hasattr(self._fusion_instance, 'Open'):
                result = self._fusion_instance.Open()
            else:
                # Assume connection is implicit on instantiation
                result = True
            
            self.connected = bool(result)
            
            if self.connected:
                logger.info("Successfully connected to Fusion controller")
            else:
                logger.warning("Failed to connect to Fusion controller")
                
            return self.connected
            
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(error_msg)
            raise FusionConnectionError(error_msg) from e
    
    def disconnect(self):
        """Disconnect from the Fusion controller."""
        if self.connected and self._fusion_instance:
            try:
                logger.info("Disconnecting from Fusion controller")
                
                # Attempt to disconnect using common method names
                if hasattr(self._fusion_instance, 'Disconnect'):
                    self._fusion_instance.Disconnect()
                elif hasattr(self._fusion_instance, 'Close'):
                    self._fusion_instance.Close()
                    
                self.connected = False
                logger.info("Disconnected successfully")
                
            except Exception as e:
                logger.error(f"Error during disconnect: {str(e)}")
    
    def get_last_sale(self) -> Optional[Dict[str, Any]]:
        """
        Get the last sale transaction from the controller.
        
        This method corresponds to the GetLastSale method mentioned in page 22
        of the Wayne Fusion documentation.
        
        Returns:
            dict: Dictionary containing sale information, or None if no sale available
                Expected keys might include:
                - transaction_id: Transaction identifier
                - pump_number: Pump/nozzle number
                - product: Fuel product type
                - volume: Volume dispensed
                - price_per_unit: Price per liter/gallon
                - total_amount: Total transaction amount
                - timestamp: Transaction timestamp
                
        Raises:
            FusionConnectionError: If not connected to controller
            FusionControllerError: If operation fails
        """
        if not self.connected:
            raise FusionConnectionError("Not connected to controller. Call connect() first.")
        
        try:
            logger.info("Retrieving last sale from controller")
            
            # Call the GetLastSale method from the Wayne DLL
            sale_data = self._fusion_instance.GetLastSale()
            
            if sale_data is None:
                logger.info("No new sale available")
                return None
            
            # Convert the .NET object to a Python dictionary
            # The actual properties depend on the Wayne DLL structure
            sale_dict = self._convert_sale_to_dict(sale_data)
            
            logger.info(f"Retrieved sale: {sale_dict}")
            return sale_dict
            
        except Exception as e:
            error_msg = f"Error getting last sale: {str(e)}"
            logger.error(error_msg)
            raise FusionControllerError(error_msg) from e
    
    def get_last_sale_on_fusion(self) -> Optional[Dict[str, Any]]:
        """
        Get the last sale transaction using the GetLastSaleOnFusion method.
        
        This method corresponds to the GetLastSaleOnFusion method mentioned in page 29
        of the Wayne Fusion documentation. This may provide additional information or
        use a different protocol than GetLastSale.
        
        Returns:
            dict: Dictionary containing sale information, or None if no sale available
                
        Raises:
            FusionConnectionError: If not connected to controller
            FusionControllerError: If operation fails
        """
        if not self.connected:
            raise FusionConnectionError("Not connected to controller. Call connect() first.")
        
        try:
            logger.info("Retrieving last sale on Fusion from controller")
            
            # Call the GetLastSaleOnFusion method from the Wayne DLL
            sale_data = self._fusion_instance.GetLastSaleOnFusion()
            
            if sale_data is None:
                logger.info("No new sale available on Fusion")
                return None
            
            # Convert the .NET object to a Python dictionary
            sale_dict = self._convert_sale_to_dict(sale_data)
            
            logger.info(f"Retrieved sale on Fusion: {sale_dict}")
            return sale_dict
            
        except Exception as e:
            error_msg = f"Error getting last sale on Fusion: {str(e)}"
            logger.error(error_msg)
            raise FusionControllerError(error_msg) from e
    
    def _convert_sale_to_dict(self, sale_data) -> Dict[str, Any]:
        """
        Convert .NET sale object to Python dictionary.
        
        Args:
            sale_data: .NET object containing sale information
            
        Returns:
            dict: Python dictionary with sale information
        """
        # This conversion depends on the actual structure of the Wayne DLL's sale object
        # Common properties in fuel dispenser sales:
        sale_dict = {}
        
        # List of common property names to check
        property_names = [
            'TransactionId', 'TransactionID', 'TxnId',
            'PumpNumber', 'Pump', 'NozzleNumber', 'Nozzle',
            'Product', 'ProductName', 'Grade',
            'Volume', 'Quantity', 'Liters', 'Gallons',
            'PricePerUnit', 'UnitPrice', 'PPU',
            'TotalAmount', 'Amount', 'Total', 'Price',
            'Timestamp', 'DateTime', 'Date', 'Time',
            'Status', 'State',
        ]
        
        for prop_name in property_names:
            if hasattr(sale_data, prop_name):
                value = getattr(sale_data, prop_name)
                # Convert to Python types
                if value is not None:
                    sale_dict[prop_name] = self._convert_to_python_type(value)
        
        return sale_dict
    
    def _convert_to_python_type(self, value):
        """
        Convert .NET types to Python types.
        
        Args:
            value: Value to convert
            
        Returns:
            Python-native type
        """
        # Handle common .NET types
        if hasattr(value, 'ToString'):
            # For .NET DateTime, Decimal, etc.
            return str(value)
        return value
    
    def poll_for_new_sales(self, callback, interval: int = 5, use_fusion_method: bool = False):
        """
        Continuously poll for new sales and execute callback when found.
        
        Args:
            callback: Function to call with sale data when new sale is detected
            interval: Polling interval in seconds (default: 5)
            use_fusion_method: If True, use GetLastSaleOnFusion instead of GetLastSale
            
        Note:
            This is a blocking operation. Consider running in a separate thread
            or process for non-blocking behavior.
        """
        import time
        
        logger.info(f"Starting sale polling with {interval}s interval")
        last_sale_id = None
        
        try:
            while True:
                try:
                    # Get sale using specified method
                    if use_fusion_method:
                        sale = self.get_last_sale_on_fusion()
                    else:
                        sale = self.get_last_sale()
                    
                    # Check if this is a new sale
                    if sale:
                        current_sale_id = sale.get('TransactionId') or sale.get('TransactionID')
                        
                        if current_sale_id and current_sale_id != last_sale_id:
                            logger.info(f"New sale detected: {current_sale_id}")
                            callback(sale)
                            last_sale_id = current_sale_id
                    
                except Exception as e:
                    logger.error(f"Error during polling: {str(e)}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Polling stopped by user")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
    
    def __repr__(self):
        """String representation."""
        status = "connected" if self.connected else "disconnected"
        return f"FusionController(ip={self.controller_ip}, status={status})"
