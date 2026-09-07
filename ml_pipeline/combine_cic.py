import os
import glob

def combine_csv():
    data_dir = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(data_dir, "data", "MachineLearningCVE")
    output_file = os.path.join(data_dir, "data", "CIC-IDS2017-combined.csv")
    
    print(f"Searching for CSV files in: {source_dir}")
    csv_files = glob.glob(os.path.join(source_dir, "*.csv"))
    
    if not csv_files:
        print("Error: No CSV files found in the source directory!")
        return
        
    print(f"Found {len(csv_files)} CSV files. Combining them...")
    
    # Read the header from the first file
    first_file = csv_files[0]
    print(f"Reading header from: {os.path.basename(first_file)}")
    with open(first_file, 'r', encoding='utf-8', errors='ignore') as f:
        header = f.readline()
        
    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.write(header)
        
        for file in csv_files:
            filename = os.path.basename(file)
            print(f"Appending lines from: {filename} ...")
            with open(file, 'r', encoding='utf-8', errors='ignore') as infile:
                # Skip header
                infile.readline()
                # Copy lines
                for line in infile:
                    # Ignore empty lines
                    if line.strip():
                        outfile.write(line)
                        
    print(f"Successfully combined all CSVs into: {output_file}")
    print(f"Total file size: {os.path.getsize(output_file) / (1024*1024):.2f} MB")

if __name__ == "__main__":
    combine_csv()
