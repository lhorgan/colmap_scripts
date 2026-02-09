def plot_trajectory(input_file_path, output_file_path):
    with open(input_file_path) as f:
        lines = f.readlines()

    with open(output_file_path, 'w') as f:
        # write header meta-data
        f.write('ply\n')
        f.write('format ascii 1.0\n')
        f.write('comment Right-Handed System\n')
        f.write(f'element vertex {len(lines)-1}\n')
        f.write('property float x\n')
        f.write('property float y\n')
        f.write('property float z\n')
        f.write('property uchar red\n')
        f.write('property uchar green\n')
        f.write('property uchar blue\n')
        f.write('end_header\n')

        for line in lines[1:]:
            tx, ty, tz = [float(t) for t in line.split(" ")[1:4]]
            f.write(f"{tx} {ty} {tz} 255 0 0\n")

#plot_trajectory(input_file_path="/home/luke/Documents/pamir_reconstructions/partial/Pamir1kf/svin.txt", output_file_path="/home/luke/Documents/pamir_reconstructions/partial/Pamir1kf/svin.ply")
#plot_trajectory(input_file_path="/home/luke/pamir/Combined_exhaustive/matched/svin_2.txt", output_file_path="/home/luke/pamir/Combined_exhaustive/matched/svin_2.ply")

#plot_trajectory(input_file_path="/home/luke/pamir/Combined_exhaustive/svin_noninv.txt", output_file_path="/home/luke/pamir/Combined_exhaustive/svin_noninv.ply")
plot_trajectory(input_file_path="/home/luke/Documents/titanic/svin_scaffold.txt", output_file_path="/home/luke/Documents/titanic/svin_scaffold.ply")