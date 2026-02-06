"""
Example usage of the Fusion Combustibles Lector package.

This script demonstrates how to connect to a Wayne Fusion controller
and retrieve sales data.
"""

from fusion_reader import FusionController
import logging

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def on_new_sale(sale_data):
    """
    Callback function that gets called when a new sale is detected.
    
    Args:
        sale_data (dict): Dictionary containing sale information
    """
    print("\n" + "="*50)
    print("NEW SALE DETECTED!")
    print("="*50)
    for key, value in sale_data.items():
        print(f"{key}: {value}")
    print("="*50 + "\n")


def example_basic_usage():
    """Example of basic usage with manual connection management."""
    print("\n--- Example 1: Basic Usage ---")
    
    # Configuration
    CONTROLLER_IP = "192.168.1.100"  # Replace with your controller's IP
    DLL_PATH = "C:\\Path\\To\\Wayne\\Fusion.dll"  # Replace with actual DLL path
    
    # Create controller instance
    controller = FusionController(
        controller_ip=CONTROLLER_IP,
        dll_path=DLL_PATH
    )
    
    try:
        # Connect to the controller
        if controller.connect():
            print("Successfully connected!")
            
            # Get the last sale using GetLastSale method
            print("\nGetting last sale...")
            sale = controller.get_last_sale()
            
            if sale:
                print("Last sale data:")
                for key, value in sale.items():
                    print(f"  {key}: {value}")
            else:
                print("No sale data available")
            
            # Get the last sale using GetLastSaleOnFusion method
            print("\nGetting last sale on Fusion...")
            sale_fusion = controller.get_last_sale_on_fusion()
            
            if sale_fusion:
                print("Last sale on Fusion data:")
                for key, value in sale_fusion.items():
                    print(f"  {key}: {value}")
            else:
                print("No sale data available on Fusion")
                
        else:
            print("Failed to connect to controller")
            
    finally:
        # Always disconnect when done
        controller.disconnect()


def example_context_manager():
    """Example using context manager for automatic connection management."""
    print("\n--- Example 2: Using Context Manager ---")
    
    # Configuration
    CONTROLLER_IP = "192.168.1.100"
    DLL_PATH = "C:\\Path\\To\\Wayne\\Fusion.dll"
    
    # Using context manager (automatically connects and disconnects)
    with FusionController(CONTROLLER_IP, DLL_PATH) as controller:
        sale = controller.get_last_sale()
        if sale:
            print("Sale data retrieved:", sale)


def example_continuous_polling():
    """Example of continuous polling for new sales."""
    print("\n--- Example 3: Continuous Polling ---")
    print("Press Ctrl+C to stop polling\n")
    
    # Configuration
    CONTROLLER_IP = "192.168.1.100"
    DLL_PATH = "C:\\Path\\To\\Wayne\\Fusion.dll"
    POLL_INTERVAL = 5  # seconds
    
    controller = FusionController(
        controller_ip=CONTROLLER_IP,
        dll_path=DLL_PATH
    )
    
    try:
        if controller.connect():
            print(f"Connected. Polling every {POLL_INTERVAL} seconds...")
            
            # Start polling (this is blocking)
            # Use use_fusion_method=True to use GetLastSaleOnFusion instead
            controller.poll_for_new_sales(
                callback=on_new_sale,
                interval=POLL_INTERVAL,
                use_fusion_method=False
            )
    finally:
        controller.disconnect()


def example_error_handling():
    """Example with proper error handling."""
    print("\n--- Example 4: Error Handling ---")
    
    from fusion_reader.fusion_controller import (
        FusionConnectionError,
        DLLLoadError,
        FusionControllerError
    )
    
    CONTROLLER_IP = "192.168.1.100"
    DLL_PATH = "C:\\Path\\To\\Wayne\\Fusion.dll"
    
    try:
        controller = FusionController(CONTROLLER_IP, DLL_PATH)
        
        try:
            controller.connect()
            sale = controller.get_last_sale()
            print(f"Sale retrieved: {sale}")
            
        except FusionConnectionError as e:
            print(f"Connection error: {e}")
            
        except FusionControllerError as e:
            print(f"Controller error: {e}")
            
        finally:
            controller.disconnect()
            
    except DLLLoadError as e:
        print(f"Failed to load DLL: {e}")
        print("Please check that:")
        print("1. The DLL path is correct")
        print("2. pythonnet is installed")
        print("3. The DLL is compatible with your system")


if __name__ == "__main__":
    print("Fusion Combustibles Lector - Example Usage")
    print("="*50)
    print("\nNOTE: Before running these examples, you need to:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Update CONTROLLER_IP with your Fusion controller's IP address")
    print("3. Update DLL_PATH with the path to your Wayne Fusion DLL")
    print("4. Ensure the Wayne DLL is accessible on your system")
    print("\n" + "="*50)
    
    # Uncomment the example you want to run:
    
    # example_basic_usage()
    # example_context_manager()
    # example_continuous_polling()
    # example_error_handling()
    
    print("\nUncomment one of the example functions to run it.")
