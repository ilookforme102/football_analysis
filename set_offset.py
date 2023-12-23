import datetime
import time

def reset_offset_at_midnight(filename):
    """Resets the offset value in the file to 0 at 23:59:00."""
    with open(filename, 'w') as file:
        file.write("0")
    print("Offset reset to 0 at 23:59:00")

def main():
    filename = "offset.txt"
    reset_offset_at_midnight(filename)
    time.sleep(1)  # To prevent multiple resets within the same minute

if __name__ == "__main__":
    main()
