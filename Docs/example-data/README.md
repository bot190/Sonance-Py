# Example Data

These files contain read-only responses captured from a live DSP8-130.

Captured endpoints:

| File | Endpoint |
| --- | --- |
| `general-settings.json` | `/Web/Handler.php?page=general-settings&action=read&r=0.1` |
| `in-out-settings.json` | `/Web/Handler.php?page=in-out-settings&action=read&r=0.2` |
| `eq-settings-preset-0.json` | `/Web/Handler.php?page=eq-settings&action=read&eq-preset=0&r=0.3` |

The documented export GET endpoints were also queried. They return binary
backup data rather than JSON:

| Endpoint | Observed binary prefix |
| --- | --- |
| `/DSP8-130AllSettingsBackup.gen` | `GENERALSConfig-` |
| `/all_eq_settings.alleqs` | `EQALLSETConfig-` |
| `/1_FLAT.eqs` | `EQSINGLEConfig-` |

Write and action URLs were intentionally not executed because they mutate device
state.
