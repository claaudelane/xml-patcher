# Mean‑Reversal XML‑Patcher

> **Purpose:** Automate the safe, repeatable editing of **StrategyQuant X** template files (e.g. `Mean‑Reversal.xml`) so that daily build‑log insights can be applied—and audited—in seconds.
>
> **Key guarantees**
> 1. Original SQX tag order & hidden attributes **never change** ➜ GUI won't revert to defaults.
> 2. All edits are driven by a human‑readable **YAML diff** ➜ no code‑changes for new runs.
> 3. Every patch run emits a `.diff` file ➜ perfect traceability of strategy evolution.

---

## ✨ Features

| Feature | Benefit |
|---------|---------|
| **Encoding‑safe loader** | Converts Windows‑1252 SQX exports to UTF‑8 once → no garbling. |
| **Param map & upsert** | Each editable field is mapped to an XPath; script overwrites or creates the node. |
| **YAML‑driven** | Tweaking two numbers = edit YAML, re‑run — no Python edits needed. |
| **Diff logger** | Unified diff (`.diff`) shows exactly what changed this run. |
| **Dry‑run validator** | Ensures every key in YAML exists in the template; aborts if not. |
| **Rolling OOS helper** | Auto‑creates 10×3‑month OOS blocks when `oos_blocks: rolling_3m_10` is set. |

---

## 🗂️ Repo Layout

```text
├── patcher.py              # main CLI script
├── hf_mean_rev.yaml        # Master YAML diff for high‑freq mean‑reversal template
├── template/               # untouched original templates
│   └── Mean‑Reversal.xml
├── out/                    # patched XML + diff logs per run
│   ├── Mean‑Reversal_20250423_1630.xml
│   └── Mean‑Reversal_20250423_1630.diff
└── tests/                  # pytest sanity checks
```

---

## 🚀 Quick start

```bash
# 1.  Clone the repo & enter it
$ git clone https://github.com/YOUR_HANDLE/mean-reversal-xml-patcher.git
$ cd mean-reversal-xml-patcher

# 2.  Install deps (only PyYAML)
$ pip install -r requirements.txt

# 3.  Run the patcher
$ python patcher.py \
    --template template/Mean-Reversal.xml \
    --cfg hf_mean_rev.yaml \
    --out out/Mean-Reversal_final.xml

# 4.  Import out/Mean-Reversal_final.xml into SQX ➜ verify ranking, SL/PT, etc.
```

> **Tip:** add `--dry-run` to see the planned changes without writing files.

---

## 🔧 YAML Schema (excerpt)

```yaml
trading_options:
  MaxTradesPerDay: 6
  DontTradeOnWeekends: true
  ReservedBars: 50
  RealisticGapsHandling: true
  ExitOnFriday: true
  FridayExitTime: 2300  # seconds after Saturday 00:00

build_mode:
  generationType: genetic-evolution   # mandatory if you swap modes
  PopulationSize: 200
  MaxGenerations: 50
  Islands: 4
  # … additional GA flags …

slpt:
  MinSLInPips: 5
  MaxSLInPips: 25
  UsePercentSL: true
  MinSLInPercent: 1
  MaxSLInPercent: 10

blocks:
  enable_only:
    - ADXCrossDown                  # all others auto‑disabled

data_setup:
  symbol: EURUSD_darwinex
  timeframe: M15
  date_from: 2020-04-17
  date_to: 2025-04-18
  oos_blocks: rolling_3m_10         # helper generates 10 rolling OOS ranges

ranking:
  goals: {NumberOfTrades: 20, ReturnDDRatio: 40, SQNScore: 40}
  filters:
    NetProfit_IS: 0
    NumberOfTrades_IS: 80
    ReturnDDRatio_IS: 1.0
    ReturnDDRatio_OOS: 0.8
    ProfitFactor_IS: 1.10
    ProfitFactor_OOS: 1.10
    Stability_IS: 0.50
    Symmetry_IS: 30
```

> **Extendable:** Any key not mapped today is simply ignored; add new key‑to‑XPath entries in `patcher.py:param_map` to make them editable.

---

## 🛠 Development & Testing

```bash
# run unit tests
$ pytest -q

# lint
$ ruff check patcher.py
```

* **tests/test_roundtrip.py** validates:
  * Structural parity (no extra/missing tags)
  * All YAML keys applied
  * Re‑parse after write succeeds

---

## 🤝 Contributing

1. **Fork** & create feature branch.
2. Add/extend **param_map** in `patcher.py` to support new editable keys.
3. Include a unit test showing the new key is applied.
4. Open PR – description should list YAML → XPath mapping & any new deps.

---

## 📜 License

MIT © 2025 Franck LeClerc – feel free to use and adapt.