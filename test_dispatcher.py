import pandas as pd
from solar_processing.pi_dispatcher import PlantformMQTTDispatcher

def run_test():
    
    times = pd.date_range('2026-07-21 00:00', periods=22, freq='h')
    percentages = [
        0, 0, 0, 0, 0, 0, 0, 0,
        51.4, 71.7, 88.2, 96.2, 98.4, 94.8, 85.4, 70.3, 51.0, 29.4,
        0, 0, 0, 0
    ]
    df = pd.DataFrame({"power_percentage": percentages}, index=times) 

    pi_ip = '100.95.20.33' #melina pc tailscale ip
    #pi_ip = '100.95.222.26' #raspberrypi

    dispatcher = PlantformMQTTDispatcher(broker_ip=pi_ip, topic="prototypes/schedule")

    print(f"Sending test payload to {pi_ip} on topic 'prototypes/schedule'...")
    success = dispatcher.dispatch(df)

    if success:
        print("Successfully dispatched retained payload to Plantform")
    else:
        print("Failed to dispatch payload")

if __name__ == "__main__":
    run_test()