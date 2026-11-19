# cycplusSync

Syncs FIT files from a CycPlus M1 bicycle computer to the local machine via BLE (Bluetooth Low Energy).

## Project layout
- `src/cycplussync/__init__.py` — main logic: `BluetoothFileTransfer` class + `main()` entry point
- `src/cycplussync/settings.py` — pydantic-settings `Settings` class
- `pyproject.toml` — uv-managed package; entry point `cycplussync = "cycplussync:main"`
- Rides land in `~/.cycplusSync/profiles/<profile>/rides/`

## Running
```bash
uv run cycplusSync                        # uses defaults from config / env
uv run cycplusSync --profile MyProfile   # override profile
uv run cycplusSync --target-name M1_74F7 # override device name
```

## BLE protocol notes
- Three characteristics: UUID (data/control), UUIDTX (tx notifications), UUIDRX (rx write)
- File transfer is initiated by writing a request bytearray to UUID, waiting for an ack, then looping through COPY/COPYOK until combine=False
- `output.txt` (the device file listing) is saved to the rides directory before filtering
- Transfers are fragile over BLE; the code has retry/stall detection baked in

## Key settings (pydantic-settings, see src/cycplussync/settings.py)
- `target_name` — BLE device name (default: M1_B0ED)
- `target_mac_address` — optional MAC for direct connect
- `profile` — subdirectory under ~/.cycplusSync/profiles/

## Known issues / future work
- BluetoothFileTransfer mixes BLE protocol, device discovery, and file I/O — good candidate for splitting
- `requires-python = ">=3.14"` in pyproject.toml may be more restrictive than needed
- Not fully XDG-compliant on Linux (uses ~/.cycplusSync rather than XDG_DATA_HOME)
