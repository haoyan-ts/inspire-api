"""Example of using pre-programmed action sequences."""

import time

import numpy as np

from inspire_api import InspireHandSerial


def main():
    """Demonstrate using action sequences with the Inspire Hand."""
    # Action sequences work with both serial and Modbus
    hand = InspireHandSerial(port="COM3", generation=3, debug=True)

    print("Connecting to Inspire Hand...")
    if not hand.connect():
        print("Failed to connect!")
        return

    print("Connected successfully!")

    try:
        # Reset errors
        hand.reset_error()
        time.sleep(0.5)

        # Action sequences are pre-programmed gestures stored in the hand
        # The exact sequences depend on your hand's firmware configuration

        print("\n=== Running Action Sequences ===")

        # Set action sequence ID (0-7 typically available)
        print("\nSetting action sequence 0...")
        hand.set_action_sequence(hand_id=1, sequence_id=0)
        time.sleep(0.5)

        # Run the sequence
        print("Running action sequence 0...")
        hand.run_action_sequence(hand_id=1)
        time.sleep(3)  # Wait for sequence to complete

        # Check current position
        current_pos = hand.get_angle_actual()
        print(f"Position after sequence 0: {current_pos}")

        # Try another sequence
        print("\nSetting action sequence 1...")
        hand.set_action_sequence(hand_id=1, sequence_id=1)
        time.sleep(0.5)

        print("Running action sequence 1...")
        hand.run_action_sequence(hand_id=1)
        time.sleep(3)

        current_pos = hand.get_angle_actual()
        print(f"Position after sequence 1: {current_pos}")

        # Cycle through multiple sequences
        print("\n=== Cycling Through Sequences ===")
        for seq_id in range(3):
            print(f"\nRunning sequence {seq_id}...")
            hand.set_action_sequence(hand_id=1, sequence_id=seq_id)
            time.sleep(0.3)
            hand.run_action_sequence(hand_id=1)
            time.sleep(2)

        # Return to neutral position
        print("\nReturning to zero position...")
        hand.return_to_zero()
        time.sleep(2)

    finally:
        print("\nDisconnecting...")
        hand.disconnect()
        print("Done!")


def custom_gesture_sequence():
    """Example of creating a custom gesture sequence programmatically."""
    print("\n=== Custom Gesture Sequence ===")

    with InspireHandSerial(port="COM3", generation=3) as hand:
        # Define a sequence of positions
        positions = [
            np.array([0, 0, 0, 0, 0, 0], dtype=np.int32),  # Fully closed
            np.array([500, 500, 500, 500, 500, 0], dtype=np.int32),  # Half open
            np.array([1000, 1000, 1000, 1000, 1000, 0], dtype=np.int32),  # Fully open
            np.array([800, 200, 200, 200, 200, 0], dtype=np.int32),  # Pinch gesture
            np.array([200, 800, 800, 800, 800, 0], dtype=np.int32),  # Grip gesture
            np.array([0, 0, 0, 0, 0, 0], dtype=np.int32),  # Back to closed
        ]

        speeds = np.array([150, 150, 150, 150, 150, 100], dtype=np.int32)
        hand.set_speed(speeds)

        print("Executing custom gesture sequence...")
        for i, pos in enumerate(positions):
            print(f"  Position {i + 1}/{len(positions)}: {pos}")
            hand.set_angle(pos)
            time.sleep(1.5)  # Wait between positions

        print("Custom sequence complete!")


if __name__ == "__main__":
    # Run main example
    main()

    # Uncomment to run custom gesture example
    # custom_gesture_sequence()
