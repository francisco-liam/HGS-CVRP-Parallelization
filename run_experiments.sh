#!/bin/bash

# List of instances and their corresponding maxIter values
instances=(
  "X-n106-k14 331255"
  "X-n289-k60 376543"
  "X-n359-k29 330907"
  "X-n491-k59 479553"
  "X-n573-k30 181178"
  "X-n627-k43 230672"
  "X-n783-k48 268353"
  "X-n895-k37 237589"
  "X-n936-k151 321974"
  "X-n1001-k43 202652"
)

# Change to the build directory
cd build || exit

# Loop through instances
for instance_data in "${instances[@]}"; do
  # Extract the instance name and maxIter value
  instance=$(echo "$instance_data" | awk '{print $1}')
  maxIter=$(echo "$instance_data" | awk '{print $2}')

  # Extract the number following 'n' in the instance name
  instance_number=$(echo "$instance" | grep -oP '(?<=n)\d+')

  # Loop through seeds 1 to 10
  for seed in {1..10}; do
    # Loop through thread counts 2, 4, and 8
    for threads in 2 4 8; do
      echo "Running instance=$instance with seed=$seed, threads=$threads, and maxIter=$maxIter"
      ./hgs "../Instances/CVRP/$instance.vrp" "${instance_number}-${threads}-${seed}.sol" -seed $seed -maxIter $maxIter -threads $threads
      sleep 5
    done
  done
done

# Return to the original directory
cd - || exit