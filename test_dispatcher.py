import pandas as pd
from solar_processing.pi_dispatcher import PlantformMQTTDispatcher

def run_test():
    df = pd.DataFrame({
        'power_percentage': [51.4, 71.7, 88.2, 96.2, 98.4, 94.8, 85.4, 70.3, 51.0, 29.4]
    }, index = pd.date_range('2026-07-21 08:00', period=10, freq='h'))

    pi_ip = <PI IP ADDRESS HERE>

    dispatcher = PlantformMQTTDispatcher(broker_ip=pi_ip)

    print(f"Sending test payload to {pi_ip}...")
    success = dispatcher.dispatch(df)

    if success:
        print("Successfully dispatched payload to Plantform")

    if __name__ == "__main__":
        run_test()