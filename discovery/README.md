# discovery/

Output of the parameter-sweep search (`tools/discover.py`) that feeds the
PLUS replay library (`tools/curate_library.py` → `replay_library/`).

- `results/*.jsonl` — one record per simulation: params, seed, score,
  classification (dead/uniform/stable/living/chaotic), and the detected
  stabilisation generation. **Gitignored** (regenerable, can be large).

Regenerate:

```bash
# run the full Gray-Scott sweep across 4 parallel workers
bash tools/run_sweep.sh 4
# curate the winners into replay_library/
python3 tools/curate_library.py --top 40 --featured 16 --render
```
