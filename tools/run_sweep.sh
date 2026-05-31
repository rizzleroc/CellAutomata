#!/usr/bin/env bash
# Run the full Gray-Scott discovery sweep across N parallel workers (one per
# CPU core). Each worker takes a disjoint --shard i/N slice; numpy is pinned to
# one thread per worker so N workers saturate N cores without oversubscription.
#
#   bash tools/run_sweep.sh [N_workers] [grid] [max_steps] [sample]
#
# Writes discovery/results/gs_shard_<i>.jsonl. Safe to run in the background;
# blocks until every worker exits, then prints a combined summary.
set -uo pipefail
cd "$(dirname "$0")/.."

N="${1:-4}"
GRID="${2:-80}"
STEPS="${3:-1300}"
SAMPLE="${4:-40}"

export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
mkdir -p discovery/results
echo "sweep: $N workers, grid=$GRID steps=$STEPS sample=$SAMPLE"

pids=()
for i in $(seq 0 $((N-1))); do
  out="discovery/results/gs_shard_$(printf '%02d' "$i").jsonl"
  python3 tools/discover.py --shard "$i/$N" --grid "$GRID" --max-steps "$STEPS" \
      --sample "$SAMPLE" --out "$out" > "discovery/results/worker_$i.log" 2>&1 &
  pids+=($!)
  echo "  worker $i -> $out (pid ${pids[-1]})"
done

fail=0
for p in "${pids[@]}"; do
  wait "$p" || fail=1
done

total=$(cat discovery/results/gs_shard_*.jsonl 2>/dev/null | wc -l)
echo "SWEEP COMPLETE: $total total records across $N shards (fail=$fail)"
echo "next: python3 tools/curate_library.py --top 40 --featured 16 --render"