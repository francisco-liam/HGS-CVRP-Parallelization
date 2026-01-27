#!/bin/bash

# List of instances and their corresponding maxIter values
instances=(
  "X-n147-k7-s4 331255"
  "X-n221-k11-s7 376543"
  "X-n360-k40-s9 330907"
  "X-n469-k26-s10 479553"
  "X-n577-k30-s4 181178"
  "X-n698-k75-s13 230672"
  "X-n759-k98-s10 268353"
  "X-n830-k171-s11 237589"
  "X-n920-k207-s4 321974"
  "X-n1006-k43-s5 202652"
)

# Return per-seed maxIter based on 1-thread stats CSV line count (excluding header).
# Falls back to the default provided in the instances[] list if the CSV is missing or unreadable.
get_seed_max_iter() {
  local instance_number="$1"   # e.g., 106
  local seed="$2"              # e.g., 7
  local default_max_iter="$3"  # fallback value

  # Stats CSV expected at project_root/Experiments/n<instance_number>/1-threads/<instance_number>-1-<seed>.sol_stats.csv
  # We run from build/, so go up one level to project root, then into Experiments/.
  local stats_file="../Experiments/n${instance_number}/1-threads/${instance_number}-1-${seed}.sol_stats.csv"
  if [[ -f "$stats_file" ]]; then
    # Count non-empty data lines excluding the first header line
    local count
    count=$(tail -n +2 "$stats_file" | sed '/^[[:space:]]*$/d' | wc -l)
    if [[ "$count" =~ ^[0-9]+$ ]] && (( count > 0 )); then
      echo "$count"
      return 0
    fi
  fi
  # Fallback
  echo "$default_max_iter"
}

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
    # Determine per-seed maxIter from 1-thread stats (fallback to default if missing)
    seed_maxIter=$(get_seed_max_iter "$instance_number" "$seed" "$maxIter")

    # Loop through thread counts 2, 4, and 8
    for threads in 2 4 8 16; do
      echo "Running instance=$instance seed=$seed threads=$threads maxIter=$seed_maxIter"
      taskset -c 0-15 ./hgs "../Instances/ECVRP/$instance.evrp" "${instance_number}-${threads}-${seed}.sol" -seed "$seed" -maxIter "$seed_maxIter" -threads "$threads"
      sleep 5
    done
  done
done

# Return to the original directory
cd - || exit