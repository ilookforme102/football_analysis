def update_offset_file(filename):
    """Reads and updates the offset in the file based on specified conditions."""
    try:
        # Read current offset value from the file
        with open(filename, 'r') as file:
            content = file.read()
            if content:
                offset = int(content)
            else:
                offset = 0

        # If the offset is already 0, indicate no further action and stop
        if offset == 0:
            print("Offset is already at 0, no further action taken.")
            return

        # Update the offset value based on conditions
        if offset <= 15:
            offset += 5
        else:
            offset = 0

        # Write the updated offset back to the file
        with open(filename, 'w') as file:
            file.write(str(offset))

    except FileNotFoundError:
        # If the file doesn't exist, create it and initialize to 0
        with open(filename, 'w') as file:
            file.write("0")
    except ValueError:
        # If the file contains non-numeric data, reset to 0
        with open(filename, 'w') as file:
            file.write("0")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    filename = "offset.txt"
    update_offset_file(filename)

if __name__ == "__main__":
    main()
