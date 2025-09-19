import serial
import time
ser = serial.Serial('COM3', 115200, timeout=1)
time.sleep(2)  # give time for Pico to reset

print("Enter a number (0 to turn OFF LEDs, 1–7 to turn ON specific LED).")
print("Type 'q' to quit.")

while True:
    user_input = input("Enter 0–7: ").strip()

    if user_input.lower() == 'q':
        print("Exiting...")
        break

    # Only accept single characters '0'–'7'
    if user_input in [str(i) for i in range(0, 8)]:
        ser.write(user_input.encode())   # send to Pico
        print(f"Sent: {user_input}")
    else:
        print("Invalid input! Please enter 0–7 or 'q' to quit.")

ser.close()