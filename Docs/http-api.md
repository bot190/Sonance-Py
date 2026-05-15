# Sonance DSP HTTP API

This document describes the HTTP API shape inferred from the bundled amplifier
web pages in `WebPages/`.

The amplifier exposes an unauthenticated HTTP endpoint that accepts `GET`
requests and returns JSON. The web UI sends all requests to:

```text
/Web/Handler.php
```

Every web UI request includes an `r` query parameter containing a random number.
This appears to be a cache buster.

```text
r=<random_float>
```

Writes return a refreshed JSON state object for the page. The client can usually
treat a successful write response as the updated state without issuing a
separate read.

## General Settings

Read:

```text
GET /Web/Handler.php?page=general-settings&action=read&r=<random>
```

Write:

```text
GET /Web/Handler.php?page=general-settings&action=write&name=<name>&value=<value>&r=<random>
```

Known names:

| Name | Values / notes |
| --- | --- |
| `ip-address` | IPv4 address |
| `ip-subnet-mask` | IPv4 subnet mask |
| `dhcp-switch` | `on`, `off` |
| `flash-power-switch` | `on`, `off` |
| `auto-on-method` | `trigger`, `trigger_green`, `ip`, `ir`, `audio`, `console` |
| `auto-on-delay` | `0`, `2`, `4`, `6`, `8`, `10`, `12`, `14`, `16`, `18`, `20` |
| `amplifier-name` | text |
| `dealer-name` | text |
| `installer-name` | text |
| `customer-name` | text |
| `installition-date` | text; misspelled in the web UI/API |
| `firmware-version` | read-only in the web UI |
| `amplifier-model` | read-only in the web UI |
| `serial-number` | read-only in the web UI |

Expected response keys include:

```text
ip-address
ip-subnet-mask
dhcp-switch
flash-power-switch
auto-on-method
auto-on-delay
amplifier-name
dealer-name
firmware-version
amplifier-model
installer-name
serial-number
customer-name
installition-date
```

## Input / Output Settings

Read:

```text
GET /Web/Handler.php?page=in-out-settings&action=read&r=<random>
```

Write:

```text
GET /Web/Handler.php?page=in-out-settings&action=write&name=<name>&index=<index>&value=<value>&r=<random>
```

Indexes are zero-based and generally correspond to channel/input/output array
positions returned by the read endpoint.

Known names:

| Name | Values / notes |
| --- | --- |
| `input-name` | text |
| `level-trim-dB` | `-6` through `6`, step `0.5` |
| `output-name` | text |
| `stereo-or-mono` | `stereo`, `mono` |
| `dsp-preset` | value from `dsp-preset-items` |
| `output-group` | value from `output-group-items` |
| `bridge-mode` | value from `bridge-mode-items` |
| `source-1` | input index |
| `source-2` | input index |
| `mode-source` | `mute`, `off`, `mix` |
| `output-volume` | `-70` through `12` |
| `turn-on-volume` | `-70` through `12` |
| `maximum-volume` | `-70` through `12` |
| `gain-offset` | `-6` through `6`, step `0.5` |
| `mute-volume` | `on`, `off` |

Expected response keys include:

```text
input-titles
input-names
level-trim-dBs
output-titles
output-names
stereo-or-mono
dsp-presets
dsp-preset-items
output-groups
output-group-items
bridge-modes
bridge-mode-items
sources-1
sources-2
mode-sources
output-volumes
turn-on-volumes
maximum-volumes
gain-offset
mute-volumes
```

## EQ Settings

Read:

```text
GET /Web/Handler.php?page=eq-settings&action=read&eq-preset=<preset>&r=<random>
```

Write a preset-level setting:

```text
GET /Web/Handler.php?page=eq-settings&action=write&eq-preset=<preset>&name=<name>&value=<value>&r=<random>
```

Write an indexed EQ setting:

```text
GET /Web/Handler.php?page=eq-settings&action=write&eq-preset=<preset>&name=<name>&index=<index>&value=<value>&r=<random>
```

Run an EQ action:

```text
GET /Web/Handler.php?page=eq-settings&action=do&eq-preset=<preset>&name=<name>&value=<value>&r=<random>
```

Write an in/out setting through the EQ page:

```text
GET /Web/Handler.php?page=eq-settings&action=write&name=<name>&index=<index>&value=<value>&r=<random>
```

Known preset-level names:

| Name | Values / notes |
| --- | --- |
| `eq-preset-name` | text with spaces removed by the web UI |
| `reset` | value is the current preset index |
| `limiter-limiters` | `off`, `-3db`, `-6db`, `-12db` |
| `delay-seconds` | numeric text |
| `delay-feet` | numeric text |
| `delay-meters` | numeric text |

Known indexed EQ names:

| Name | Values / notes |
| --- | --- |
| `parametric-eq-on-or-off` | `on`, `off` |
| `parametric-eq-freq` | `20` through `20000` |
| `parametric-eq-q` | `0.3` through `24` |
| `parametric-eq-gain` | `-12` through `12` |
| `tilt-control-on-or-off` | `on`, `off` |
| `tilt-control-freq` | numeric text |
| `tilt-control-gain` | numeric text |
| `crossover-on-or-off` | `on`, `off` |
| `crossover-freq` | numeric text |
| `crossover-filter-type` | `bw-6db`, `bw-12db`, `bw-18db`, `bw-24db` |

Known EQ actions:

| Name | Values / notes |
| --- | --- |
| `pink-noise-generator-on-or-off` | `on`, `off` |
| `pink-noise-generator-level` | `-50` through `12` |

Known in/out names used from the EQ page:

| Name | Values / notes |
| --- | --- |
| `source-select` | input index |
| `output-volume` | `-50` through `12` in the EQ page UI |
| `mute-volume` | `on`, `off` |
| `output-name` | text |
| `dsp-preset` | value from `eq-presets` |
| `copy` | `index=<from_preset>&value=<to_preset>` |

Expected response keys include:

```text
amplifier-model
input-names
source-select
output-volumes
mute-volumes
output-titles
output-names
dsp-presets
eq-presets
current-eq-preset
parametric-eq
tilt
crossover
limiter-limiters
delay
```

## Parametric EQ Extra Parameters

The web UI sends additional computed parameters for indexed parametric EQ
writes:

```text
extraB=<computed_frequency_value>
extraG=<computed_gain_value>
extraA=<computed_q_gain_frequency_value>
```

These are sent with:

```text
parametric-eq-on-or-off
parametric-eq-freq
parametric-eq-q
parametric-eq-gain
```

The calculation is implemented in `WebPages/EQSettings.htm` in:

```text
getExtraFreq(index)
getExtraGain(index)
getExtraA(index)
```

The web UI comment says these functions are only for `2-150` and `2-750`, but
the active JavaScript path sends them for all models.

## File Import / Export Endpoints

The web UI also exposes form-based import/export endpoints.

General settings restore:

```text
POST Handler.php?page=general-settings
multipart/form-data file=<file>
```

General settings export:

```text
GET <amplifier-model>AllSettingsBackup.gen
```

EQ all presets import:

```text
POST Handler.php?page=eq-settings&file=all
multipart/form-data file=<file>
```

EQ all presets export:

```text
GET all_eq_settings.alleqs
```

EQ single preset import:

```text
POST Handler.php?page=eq-settings&file=single&eq-preset=<preset>
multipart/form-data file=<file>
```

EQ single preset export:

```text
GET <preset_number>_<preset_name>.eqs
```

## Client Notes

- Use URL/query parameter encoding. The original web UI concatenates raw values,
  but text fields can contain characters that must be escaped.
- Treat indexes as zero-based internally unless a public API intentionally maps
  them to user-facing channel labels.
- Boolean-like values are lower-case strings: `on` and `off`.
- Many numeric values are sent as query strings by the UI. A client may accept
  numbers and serialize them as query parameters.
- There is no authentication in the observed web UI.
- The observed API does not advertise versioning. Model and firmware should be
  read from `general-settings` and retained for compatibility decisions.
