# echo "Running Pamir0"
# sh run_423.sh /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered Pamir0 > /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Pamir0/log.txt 2>&1

# echo "Running Pamir1"
# sh run_423.sh /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered Pamir1 > /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Pamir1/log.txt 2>&1

# echo "Running Pamir2"
# sh run_423.sh /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered Pamir2 > /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Pamir2/log.txt 2>&1

# echo "Running Combined"
# sh run_423.sh /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered Combined > /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Combined/log.txt 2>&1

# echo "Running Pamir0_incref"
# sh run_423.sh /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered Pamir0_incref > /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Pamir0_incref/log2.txt 2>&1

# echo "Running Pamir1_incref"
# sh run_423.sh /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered Pamir1_incref > /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Pamir1_incref/log2.txt 2>&1

# echo "Running Pamir2_incref"
# sh run_423.sh /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered Pamir2_incref > /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Pamir2_incref/log2.txt 2>&1

# echo "Running Combined with Exhaustive Matcher"
# sh run_423.sh /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered Combined_exhaustive_incref > /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Combined_exhaustive_incref/log3.txt 2>&1

# echo "Running Combined with the Sequential Matcher, no bad images, incremental model refiner"
# sh run_423.sh /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Combined_seq_incref_filtered > /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Combined_seq_incref_filtered/log2.txt 2>&1

# echo "Running tiny without poses"
# sh run_423.sh /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Tiny_no_poses > /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Tiny_no_poses/log.txt 2>&1

# echo "Running Pamir1 and Pamir2 with sequential matcher"
# sh run_423.sh /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered Pamir1_and_Pamir2_ex_inc > /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Pamir1_and_Pamir2_ex_inc/log.txt 2>&1

# echo "Tiny"
# sh run_423.sh /mnt/Data2/luke/pamir/reconstructions/oneframe/SmallTests Tiny_1 > /mnt/Data2/luke/pamir/reconstructions/oneframe/SmallTests/Tiny_1/log2.txt 2>&1

echo "Combined"
sh run_423.sh /mnt/Data3/luke/underwater/reconstructions Combined > /mnt/Data3/luke/underwater/reconstructions/Combined/log1.txt 2>&1