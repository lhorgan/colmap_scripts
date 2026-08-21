import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--svin_files", type=str, nargs="+", required=True)
    parser.add_argument("--output", type=str, required=True)

    args = parser.parse_args()

    output = []
    for svin_file_path in args.svin_files:
        print(svin_file_path)

        with open(svin_file_path, "r") as f:
            lines = f.readlines()
            comment = lines[0]
            output = output + lines[1:]
        
    output = [comment] + output

    print("WRITING TO ", args.output)
    with open(args.output, "w+") as f:
        f.write("".join(output))