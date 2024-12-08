import json
import os
import pickle

def pickle_to_human_readable(filename):
    # Load the pickle file
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        print(f"File '{filename}' is empty or does not exist.")
        return

    try:
        with open(filename, 'rb') as f:
            data = pickle.load(f)
    except EOFError:
        print("EOFError: Ran out of input - The pickle file may be empty or corrupted.")
        return
    except pickle.UnpicklingError:
        print("UnpicklingError: The pickle file could not be read.")
        return
    except Exception as e:
        print(f"Error reading pickle file: {e}")
        return

    # Convert to human-readable format (JSON format, for example)
    try:
        # Attempt to convert to JSON (if the data is serializable to JSON)
        readable_data = json.dumps(data.__dict__, indent=4)  # Converting to a dictionary for JSON
    except TypeError:
        # If it's not JSON serializable, you could try str or repr to convert to a string
        readable_data = str(data)

    # Save to a human-readable file
    human_readable_filename = filename + "_r.json"
    with open(human_readable_filename, 'w') as f:
        f.write(readable_data)
        print(f"Human-readable file saved to {human_readable_filename}")




pickle_to_human_readable("log.txt")