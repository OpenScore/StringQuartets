import json
import subprocess
from pathlib import Path

# Configuration
MUSESCORE_EXECUTABLE = "mscore" 
# ^^ Can use "musescore" if it's in PATH, otherwise specify the path, e.g., >>
MUSESCORE_EXECUTABLE = "/Users/<user>/Applications/MuseScore 3.app/Contents/MacOS/mscore"
DEFAULT_INPUT_DIR = Path("../scores")
OUTPUT_FORMAT = "mxl"
INPUT_EXTENSIONS = ("*.mscz", "*.mscx") # We use mscz/mscx and for MuseScore 3/4 respectively


def convert_directory(
        input_dir: Path = DEFAULT_INPUT_DIR,
        parts: bool = True
):
    # Resolve path to absolute
    input_dir = input_dir.resolve()
    
    if not input_dir.exists():
        print(f"Error: Directory '{input_dir}' does not exist.")
        return

    # Collect all MuseScore files
    files = []
    for ext in INPUT_EXTENSIONS:
        files.extend(input_dir.rglob(ext))
    
    if not files:
        print(f"No MuseScore files found in '{input_dir}'.")
        return

    print(f"Found {len(files)} files in '{input_dir}'. Preparing batch job...")

    # Create job list for JSON
    job_data = []
    for file_path in files:
        output_file = file_path.with_suffix(f".{OUTPUT_FORMAT}")
        if parts:
            output_parts = str(file_path.with_suffix("")) + "-Part-"
            job_data.append({
                "in": str(file_path),
                "out": [
                    # str(output_file), # If main also
                    [output_parts, f".{OUTPUT_FORMAT}"]
                ]
            })
        else:
            job_data.append({
                "in": str(file_path),
                "out": str(output_file)
            })

    # Write temporary JSON job file
    json_file = input_dir / "batch_job.json"
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(job_data, f, indent=2)
        
        print(f"Running conversion via '{MUSESCORE_EXECUTABLE}'...")
        
        # Execute MuseScore with the job file
        # Using check=True raises an error if the command fails
        subprocess.run([MUSESCORE_EXECUTABLE, "-j", str(json_file)], check=True)
        
        print("Batch conversion complete.")
        
    except FileNotFoundError:
        print(f"Error: MuseScore executable '{MUSESCORE_EXECUTABLE}' not found. Please ensure it is installed and in your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Conversion failed with error code {e.returncode}. Check MuseScore output for details.")
    finally:
        # Clean up the temporary JSON file
        if json_file.exists():
            json_file.unlink()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        target_path = Path(sys.argv[1])
    else:
        target_path = DEFAULT_INPUT_DIR
        
    convert_directory(target_path)   
