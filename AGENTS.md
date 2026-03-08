# AlphaScope Agent Notes

## Historical Decisions

- AlphaScope uses a unified QuantConnect Lean-style `quant-core` architecture: `ingestion + universe + indicators + engine`.
- This decision intentionally avoids a fragmented multi-layer pipeline because the market snapshot, active universe logic, and indicator computation all need to share a single synchronized context per trading day.
- Compared with ad-hoc pipelines, the unified engine is more professional for quant systems because it provides deterministic daily execution, a single plugin contract, easier backtesting portability, and cleaner migration toward research/live parity.

## Adding Indicators

1. Create a new Python file in `packages/quant-core/src/quant_core/indicators/`.
2. Subclass `BaseIndicator` and define `indicator_key`.
3. Implement `compute(self, context, definition)`.
4. Add a matching row to `indicator_definitions` if you want it enabled with custom config.
5. Restart the server or rerun the fetch job.

## Active Theme Upgrade Example

- Active themes are implemented as a special universe selection plus `ThemeVolumeIndicator`.
- If you want a stronger rolling-window theme filter, keep the indicator unchanged and update the universe policy in `packages/quant-core/src/quant_core/universe/active_themes.py`.
- Example upgrades: momentum-weighted theme turnover, decay-based expiration, minimum persistence days, or rank-stability filters.

## Important Notes

- Local package management must follow the machine standard:
  - use `nvm`
  - use Node `v24.14.0`
  - use `corepack`-managed `pnpm`
  - prefer the shell-provided `node/npm/npx/corepack/pnpm` from `~/.nvm/versions/node/v24.14.0/bin`
  - treat `/opt/homebrew/bin/node|npm|npx` as fallback only, not the primary toolchain
- Active themes default to AkShare `stock_board_concept_name_em` and are sorted by turnover descending.
- The default behavior selects the top 20 themes, then applies `threshold`, `window_days`, and `expire_days` from `indicator_definitions.config`.
- Future rolling-window or expiration logic changes should be made in `packages/quant-core/src/quant_core/universe/active_themes.py`, not scattered across indicators.
- `stock_kline_daily` is populated from `packages/quant-core/src/quant_core/universe/tracked_equities.py`. Adjust `TRACKING_TOP_TURNOVER_COUNT`, `TRACKING_LIMIT_UP_POOL_COUNT`, and `TRACKING_INCLUDE_SYMBOLS` when you need broader or narrower daily kline coverage.
