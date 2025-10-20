"""Example of reading tactile sensor data from Generation 4 hardware."""

import time

import numpy as np

from inspire_api import GenerationError, InspireHandModbus


def main():
    """Demonstrate reading tactile sensor data from Gen4 Inspire Hand."""
    # Gen4 hardware required for tactile sensors
    hand = InspireHandModbus(ip="192.168.11.210", port=6000, generation=4, debug=False)

    print("Connecting to Inspire Hand Gen4...")
    if not hand.connect():
        print("Failed to connect!")
        return

    print("Connected successfully!")

    try:
        # Get all tactile data at once
        print("\n=== Reading All Tactile Sensors ===")
        tactile_data = hand.get_all_tactile_data()

        print(f"\nTimestamp: {tactile_data.timestamp}")

        # Print finger sensor data
        print("\n--- Finger Sensors ---")
        print(f"Pinky top shape: {tactile_data.pinky.top.shape}")
        print(f"Pinky tip shape: {tactile_data.pinky.tip.shape}")
        print(f"Pinky base shape: {tactile_data.pinky.base.shape}")

        print(f"\nRing top shape: {tactile_data.ring.top.shape}")
        print(f"Ring tip shape: {tactile_data.ring.tip.shape}")
        print(f"Ring base shape: {tactile_data.ring.base.shape}")

        print(f"\nMiddle top shape: {tactile_data.middle.top.shape}")
        print(f"Middle tip shape: {tactile_data.middle.tip.shape}")
        print(f"Middle base shape: {tactile_data.middle.base.shape}")

        print(f"\nIndex top shape: {tactile_data.index.top.shape}")
        print(f"Index tip shape: {tactile_data.index.tip.shape}")
        print(f"Index base shape: {tactile_data.index.base.shape}")

        # Thumb has an extra segment (mid)
        print(f"\nThumb top shape: {tactile_data.thumb.top.shape}")
        print(f"Thumb tip shape: {tactile_data.thumb.tip.shape}")
        print(f"Thumb mid shape: {tactile_data.thumb.mid.shape}")
        print(f"Thumb base shape: {tactile_data.thumb.base.shape}")

        # Palm data
        print(f"\nPalm shape: {tactile_data.palm.shape}")

        # Read specific sensor
        print("\n=== Reading Specific Sensors ===")

        # Read thumb tip sensor
        thumb_tip = hand.get_tactile_data("thumb", "tip")
        print(f"\nThumb tip pressure data:\n{thumb_tip}")
        print(f"Max pressure point: {np.max(thumb_tip)}")
        print(f"Min pressure point: {np.min(thumb_tip)}")
        print(f"Average pressure: {np.mean(thumb_tip):.2f}")

        # Read index finger tip
        index_tip = hand.get_tactile_data("index", "tip")
        print(f"\nIndex tip pressure data shape: {index_tip.shape}")
        print(f"Max pressure: {np.max(index_tip)}")

        # Read palm sensor
        palm = hand.get_tactile_data("palm")
        print(f"\nPalm pressure data shape: {palm.shape}")
        print(f"Max pressure: {np.max(palm)}")

        # Continuous monitoring example
        print("\n=== Continuous Monitoring (5 seconds) ===")
        print("Press Ctrl+C to stop...")

        try:
            start_time = time.time()
            while time.time() - start_time < 5:
                # Read specific sensor quickly
                thumb_tip = hand.get_tactile_data("thumb", "tip")
                max_pressure = np.max(thumb_tip)
                avg_pressure = np.mean(thumb_tip)

                print(
                    f"Thumb tip - Max: {max_pressure:4d}, Avg: {avg_pressure:6.2f}",
                    end="\r",
                )
                time.sleep(0.1)  # 10 Hz update rate

        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")

        print("\n\nDone reading tactile sensors!")

    except GenerationError as e:
        print(f"\nError: {e}")
        print("Tactile sensors require Generation 4 hardware!")

    finally:
        # Always disconnect
        print("\nDisconnecting...")
        hand.disconnect()


def compare_fingers_example():
    """Example comparing pressure across different fingers."""
    print("\n=== Comparing Finger Pressures ===")

    with InspireHandModbus(ip="192.168.11.210", generation=4) as hand:
        # Get all tactile data
        data = hand.get_all_tactile_data()

        # Calculate average pressure for each finger tip
        pressures = {
            "Pinky": (
                float(np.mean(data.pinky.tip)) if data.pinky.tip.size > 0.0 else 0.0
            ),
            "Ring": float(np.mean(data.ring.tip)) if data.ring.tip.size > 0.0 else 0.0,
            "Middle": (
                float(np.mean(data.middle.tip)) if data.middle.tip.size > 0.0 else 0.0
            ),
            "Index": (
                float(np.mean(data.index.tip)) if data.index.tip.size > 0.0 else 0.0
            ),
            "Thumb": (
                float(np.mean(data.thumb.tip)) if data.thumb.tip.size > 0.0 else 0.0
            ),
        }

        print("\nFinger Tip Pressures (Average):")
        for finger, pressure in pressures.items():
            print(f"  {finger:8s}: {pressure:6.2f}")

        # Find which finger has highest pressure
        max_finger = np.argmax(list(pressures.values()))
        print(
            f"\nHighest pressure: {list(pressures.keys())[max_finger]} ({pressures[list(pressures.keys())[max_finger]]:.2f})"
        )


if __name__ == "__main__":
    # Run main example
    main()

    # Uncomment to run comparison example
    # compare_fingers_example()
