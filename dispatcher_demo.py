import pandas as pd
import argparse
from solar_processing.pi_dispatcher import PlantformMQTTDispatcher

def run_test(target: str, broker_ip: str):
    dispatcher = PlantformMQTTDispatcher(broker_ip=broker_ip, topic="prototypes")

    print(f"Sending test payload for {target} to {broker_ip} on topic 'prototypes'...")

    if target == "plantform":    
        times = pd.date_range('2026-07-21 00:00', periods=24, freq='h')
        percentages = [
            0, 0, 0, 0, 0, 0, 0, 0,
            51.4, 71.7, 88.2, 96.2, 98.4, 94.8, 85.4, 70.3, 51.0, 29.5,
            0, 0, 0, 0, 0 ,0
        ]
        df = pd.DataFrame({"power_percentage": percentages}, index=times)
        success = dispatcher.dispatch_schedule(df)

    elif target == "energyshape":
        gain_value = "5"
        success = dispatcher.dispatch_gain(gain_value)

    else:
        print(f"Unknown target: {target}")
        return

    if success:
        print("Successfully dispatched retained payload to Plantform")
    else:
        print("Failed to dispatch payload")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dispatch MQTT test instructions")
    parser.add_argument(
        "--target",
        choices=["plantform", "energyshape"],
        default="plantform",
        help="Specify which device cammand profile to test"
    )
    parser.add_argument(
        "--ip",
        default="127.0.0.1",
        help="MQTT broker IP address"
    )
    args = parser.parse_args()
    run_test(target=args.target, broker_ip=args.ip)