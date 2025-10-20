"""Basic Modbus TCP communication example with Inspire Hand."""

import time

import numpy as np

from inspire_api import InspireHandModbus


def main():
    """Demonstrate basic Modbus TCP communication with the Inspire Hand."""
    # Initialize the hand
    # Change IP/port to match your setup
    hand = InspireHandModbus(ip="192.168.11.210", port=6000, generation=4, debug=True)

    print("Connecting to Inspire Hand via Modbus TCP...")
    if not hand.connect():
        print("Failed to connect!")
        return

    print(f"Connected successfully to {hand.get_ip()}:{hand.get_port()}!")

    try:
        # Reset any errors
        print("\nResetting errors...")
        hand.reset_error()

        # Return to zero position
        print("\nReturning to zero position...")
        hand.return_to_zero()
        time.sleep(2)

        # Read current position
        current_pos = hand.get_angle_actual()
        print(f"Current position: {current_pos}")

        # Set specific angles for each joint
        print("\nSetting joint angles to [500, 500, 500, 500, 500, 0]...")
        angles = np.array([500, 500, 500, 500, 500, 0], dtype=np.int32)
        hand.set_angle(angles)
        time.sleep(2)

        # Read current position again
        current_pos = hand.get_angle_actual()
        print(f"Current position: {current_pos}")

        # Set speed (affects how fast joints move)
        print("\nSetting joint speeds...")
        speeds = np.array([200, 200, 200, 200, 200, 100], dtype=np.int32)
        hand.set_speed(speeds)

        # Set force (affects grip strength)
        print("\nSetting joint forces...")
        forces = np.array([300, 300, 300, 300, 300, 200], dtype=np.int32)
        hand.set_force(forces)

        # Close the hand
        print("\nClosing the hand...")
        hand.perform_close()
        time.sleep(2)

        # Open the hand
        print("\nOpening the hand...")
        hand.perform_open()
        time.sleep(2)

        # Read sensor data
        print("\nReading sensor data...")
        print(f"Current angles: {hand.get_angle_actual()}")
        print(f"Target angles: {hand.get_angle_set()}")
        print(f"Force actual: {hand.get_force_actual()}")
        print(f"Temperature: {hand.get_temperature()}")
        print(f"Status: {hand.get_status()}")
        print(f"Errors: {hand.get_error()}")

        # Return to zero before disconnecting
        print("\nReturning to zero position...")
        hand.return_to_zero()
        time.sleep(2)

    finally:
        # Always disconnect
        print("\nDisconnecting...")
        hand.disconnect()
        print("Done!")


def context_manager_example():
    """Demonstrate using the hand with context manager (automatically connects/disconnects)."""
    print("\n=== Context Manager Example ===")

    with InspireHandModbus(ip="192.168.11.210", port=6000, generation=4) as hand:
        print("Connected (via context manager)")

        # Perform a simple open-close cycle
        hand.perform_open()
        time.sleep(1)
        hand.perform_close()
        time.sleep(1)
        hand.return_to_zero()

        print("Operations complete")

    print("Disconnected automatically")


if __name__ == "__main__":
    # Run basic example
    main()

    # Uncomment to run context manager example
    # context_manager_example()
