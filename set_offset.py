import datetime
import time

def reset_offset_at_midnight(filename):
    """Resets the offset value in the file to 0 at 23:59:50."""
    with open(filename, 'w') as file:
        file.write("0")
    print("Offset reset to 0 at 23:59:50")

def main():
    filename = "offset.txt"
    while True:
        # Check current time
        current_time = datetime.datetime.now()
        if current_time.hour == 23 and current_time.minute == 59 and current_time.second == 50:
            reset_offset_at_midnight(filename)
            time.sleep(1)  # To prevent multiple resets within the same minute
            break  # Exit the loop after resetting

        time.sleep(0.5)  # Check the time every half second

if __name__ == "__main__":
    main()
