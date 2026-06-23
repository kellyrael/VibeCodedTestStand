# Measurement Plug-In SDK Reference

## Package

```
pip install ni-measurement-plugin-sdk          # meta-package (installs both)
pip install ni-measurement-plugin-sdk-service   # service runtime only
pip install ni-measurement-plugin-sdk-generator # CLI scaffold tool
```

Import convention:
```python
import ni_measurement_plugin_sdk_service as nims
```

---

## DataType Enum

All supported data types live in `nims.DataType`:

### Scalar Types (for configuration AND output)
| Enum Member | Python Type | Notes |
|---|---|---|
| `DataType.Int32` | `int` | 32-bit signed integer |
| `DataType.Int64` | `int` | 64-bit signed integer |
| `DataType.UInt32` | `int` | 32-bit unsigned integer |
| `DataType.UInt64` | `int` | 64-bit unsigned integer |
| `DataType.Float` | `float` | 32-bit float (Single) |
| `DataType.Double` | `float` | 64-bit float |
| `DataType.Boolean` | `bool` | True/False |
| `DataType.String` | `str` | Unicode string |
| `DataType.Enum` | `Enum` subclass or protobuf enum | Requires `enum_type=` kwarg |
| `DataType.Pin` | `str` | **Deprecated** — use `IOResource` |
| `DataType.Path` | `str` | File path |
| `DataType.IOResource` | `str` | Pin/relay mapped to instrument sessions |

### 1D Array Types (for configuration AND output)
| Enum Member | Python Type |
|---|---|
| `DataType.Int32Array1D` | `list[int]` |
| `DataType.Int64Array1D` | `list[int]` |
| `DataType.UInt32Array1D` | `list[int]` |
| `DataType.UInt64Array1D` | `list[int]` |
| `DataType.FloatArray1D` | `list[float]` |
| `DataType.DoubleArray1D` | `list[float]` |
| `DataType.BooleanArray1D` | `list[bool]` |
| `DataType.StringArray1D` | `list[str]` |
| `DataType.EnumArray1D` | `list[Enum]` |
| `DataType.IOResourceArray1D` | `list[str]` |
| `DataType.PathArray1D` | `list[str]` |

### Output-Only Types (NOT valid for configuration)
| Enum Member | Python Type | Notes |
|---|---|---|
| `DataType.DoubleXYData` | `xydata_pb2.DoubleXYData` | XY plot data |
| `DataType.Double2DArray` | `array_pb2.Double2DArray` | 2D numeric array |
| `DataType.String2DArray` | `array_pb2.String2DArray` | 2D string array |
| `DataType.DoubleXYDataArray1D` | `list[DoubleXYData]` | Array of XY plots |
| `DataType.IOResourceArray1D` | `list[str]` | Multiple pins/relays |

---

## MeasurementService Class

### Constructor
```python
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "MyMeasurement.serviceconfig",
    ui_file_paths=[
        service_directory / "MyMeasurement.measui",
    ],
)
```

Parameters:
- `service_config_path` (Path): Path to the `.serviceconfig` JSON file
- `ui_file_paths` (list[Path]): Paths to `.measui` or `.vi` UI files
- `version` (str): **Deprecated** — use the `version` field in `.serviceconfig` instead
- `service_class` (str | None): Which service class to use from the `.serviceconfig` (defaults to first)

### Key Properties
- `measurement_service.context` — `MeasurementContext` proxy for accessing RPC context during execution
- `measurement_service.measurement_info` — `MeasurementInfo` namedtuple (display_name, version, ui_file_paths)
- `measurement_service.service_info` — `ServiceInfo` with service_class, provided_interfaces, annotations
- `measurement_service.channel_pool` — `GrpcChannelPool` for reusing gRPC channels
- `measurement_service.discovery_client` — `DiscoveryClient` for NI Discovery Service
- `measurement_service.session_management_client` — `SessionManagementClient` for pin-map-based session management

---

## Decorator Pattern

The three decorators must be applied in this exact order (outermost first):

```python
@measurement_service.register_measurement          # 1. MUST be outermost
@measurement_service.configuration("Name", type, default)  # 2. Configs (top-to-bottom = param order)
@measurement_service.output("Name", type)                   # 3. Outputs (top-to-bottom = return order)
def measure(param1, param2, ...):
    ...
    return (output1, output2, ...)
```

### configuration() decorator
```python
@measurement_service.configuration(
    display_name: str,        # Shown in UI. Must match .measui Channel path.
    type: DataType,           # From nims.DataType enum
    default_value: Any,       # Default value matching the type
    *,
    instrument_type: str = "",  # Only for IOResource/Pin types
    enum_type: type[Enum] | None = None,  # Required for Enum/EnumArray1D types
)
```

Display name rules:
- Must start with a letter
- Allowed characters: alphanumeric, spaces, `().,;:!?-_'+`
- Do not use `/`, `\\`, `%`, or `^`
- Safe substitutions: use `per` instead of `/`, `Percent` instead of `%`, and `sq` instead of `^2`

### output() decorator
```python
@measurement_service.output(
    display_name: str,        # Shown in UI. Must match .measui Channel path.
    type: DataType,           # From nims.DataType enum
    *,
    enum_type: type[Enum] | None = None,  # Required for Enum/EnumArray1D types
)
```

### register_measurement decorator
```python
@measurement_service.register_measurement
```
No arguments. Must be the outermost (first) decorator.

---

## MeasurementContext

Accessed via `measurement_service.context` inside the measurement function:

```python
# Cancel callback
def cancel_callback():
    logging.info("Canceling measurement")
measurement_service.context.add_cancel_callback(cancel_callback)

# Pin map context (for session management)
pin_map_ctx = measurement_service.context.pin_map_context

# Time remaining for the RPC
remaining = measurement_service.context.time_remaining

# Abort the RPC
measurement_service.context.abort(grpc.StatusCode.CANCELLED, "Canceled")

# Reserve sessions (pin-map-based)
with measurement_service.context.reserve_session(pin_names) as reservation:
    ...
with measurement_service.context.reserve_sessions(pin_names) as reservation:
    ...
```

---

## Session Management (Pin-Map-Based)

For instrument-based measurements that use NI pin maps:

```python
@measurement_service.configuration(
    "pin_names",
    nims.DataType.IOResourceArray1D,
    ["Pin1"],
    instrument_type=nims.session_management.INSTRUMENT_TYPE_NI_DCPOWER,
)
```

Available instrument type constants:
- `nims.session_management.INSTRUMENT_TYPE_NI_DCPOWER`
- `nims.session_management.INSTRUMENT_TYPE_NI_DMM`
- `nims.session_management.INSTRUMENT_TYPE_NI_SCOPE`
- `nims.session_management.INSTRUMENT_TYPE_NI_FGEN`
- `nims.session_management.INSTRUMENT_TYPE_NI_SWITCH`
- `nims.session_management.INSTRUMENT_TYPE_NI_DIGITAL_PATTERN`
- `nims.session_management.INSTRUMENT_TYPE_NI_DAQMX`
- `nims.session_management.INSTRUMENT_TYPE_NI_VISA`
- `nims.session_management.INSTRUMENT_TYPE_NI_RFSA`
- `nims.session_management.INSTRUMENT_TYPE_NI_RFSG`

Inside the measurement function:
```python
with measurement_service.context.reserve_sessions(pin_names) as reservation:
    with reservation.initialize_nidcpower_sessions() as session_infos:
        for session_info in session_infos:
            channels = session_info.session.channels[session_info.channel_list]
            # Configure and measure...
```

---

## Enum Pattern

Enums must have a 0-valued member:

```python
from enum import Enum

class Color(Enum):
    NONE = 0
    RED = 1
    GREEN = 2
    BLUE = 3

@measurement_service.configuration("Color", nims.DataType.Enum, Color.BLUE, enum_type=Color)
@measurement_service.output("Result Color", nims.DataType.Enum, enum_type=Color)
```

For protobuf enums, define a `.proto` file and generate stubs:
```python
from _stubs import color_pb2

@measurement_service.configuration(
    "Protobuf Color",
    nims.DataType.Enum,
    color_pb2.ProtobufColor.BLACK,
    enum_type=color_pb2.ProtobufColor,
)
```

---

## 2D Array Pattern (Output Only)

```python
from ni.protobuf.types import array_pb2

@measurement_service.output("2D Data", nims.DataType.Double2DArray)
def measure(...):
    result_2d = array_pb2.Double2DArray(
        rows=2, columns=3,
        data=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]  # row-major order
    )
    return (result_2d,)
```

Helper for converting list-of-lists:
```python
def list_to_double2darray(data: list[list[float]]) -> array_pb2.Double2DArray:
    rows = len(data)
    cols = len(data[0]) if rows > 0 else 0
    flat = [val for row in data for val in row]
    return array_pb2.Double2DArray(rows=rows, columns=cols, data=flat)
```

---

## XY Data Pattern (Output Only)

```python
from ni.protobuf.types import xydata_pb2

@measurement_service.output("Waveform", nims.DataType.DoubleXYData)
def measure(...):
    xy = xydata_pb2.DoubleXYData(
        x_data=[0.0, 0.001, 0.002],
        y_data=[1.0, 2.0, 1.5],
    )
    return (xy,)
```

---

## .serviceconfig File Format

```json
{
  "services": [
    {
      "displayName": "My Measurement",
      "version": "1.0.0",
      "serviceClass": "com.example.MyMeasurement_Python",
      "descriptionUrl": "",
      "providedInterfaces": [
        "ni.measurementlink.measurement.v1.MeasurementService",
        "ni.measurementlink.measurement.v2.MeasurementService"
      ],
      "path": "start.bat",
      "annotations": {
        "ni/service.description": "Description of the measurement.",
        "ni/service.collection": "MyCompany.Measurements",
        "ni/service.tags": ["voltage", "dc"]
      }
    }
  ]
}
```

Key fields:
- `displayName`: Shown in InstrumentStudio measurement panel list
- `serviceClass`: Unique identifier. Convention: `<org>.<MeasurementName>_Python`
- `version`: Semantic version string
- `providedInterfaces`: Always include both v1 and v2
- `path`: Launcher script (typically `start.bat`)
- `annotations.ni/service.description`: Human-readable description
- `annotations.ni/service.collection`: Grouping for the measurement
- `annotations.ni/service.tags`: Array of tag strings for filtering

---

## Hosting / Entry Point Pattern

```python
import click
import logging

@click.command
@click.option("-v", "--verbose", "verbosity", count=True,
              help="Enable verbose logging. Repeat to increase verbosity.")
def main(verbosity: int) -> None:
    """Host the measurement service."""
    if verbosity > 1:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=level)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")

if __name__ == "__main__":
    main()
```

---

## pyproject.toml Template

```toml
[tool.poetry]
name = "my-measurement"
version = "0.1.0"
package-mode = false
description = "Description of my measurement."
authors = ["My Name"]

[tool.poetry.dependencies]
python = "^3.10"
ni-measurement-plugin-sdk-service = {version = ">=2.3.1,<4.0"}
click = ">=7.1.2, !=8.1.4"

# Add driver packages as needed:
# nidcpower = { version = ">=1.4.4", extras = ["grpc"] }
# nidmm = { version = ">=1.4.4", extras = ["grpc"] }
# niscope = { version = ">=1.4.4", extras = ["grpc"] }

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
```

Optional `poetry.toml` for in-project virtualenvs:
```toml
[virtualenvs]
in-project = true
```

---

## start.bat Template

If the project uses Poetry (per-plugin virtualenv):
```bat
poetry run python measurement.py
```

If reusing an existing `.venv` from the workspace root (parent directory):
```bat
..\.venv\Scripts\python.exe measurement.py
```

If the plugin folder itself contains a `.venv`:
```bat
.venv\Scripts\python.exe measurement.py
```

---

## _helpers.py Template

```python
"""Helper classes and functions for measurement plug-ins."""

from __future__ import annotations

import logging
import pathlib
from typing import Any, Callable, TypeVar

import click


class TestStandSupport:
    """Class that communicates with TestStand."""

    _PIN_MAP_ID_VAR = "NI.MeasurementPlugIns.PinMapId"

    def __init__(self, sequence_context: Any) -> None:
        self._sequence_context = sequence_context

    def get_active_pin_map_id(self) -> str:
        run_time_variables = self._sequence_context.Execution.RunTimeVariables
        if not run_time_variables.Exists(self._PIN_MAP_ID_VAR, 0x0):
            return ""
        return run_time_variables.GetValString(self._PIN_MAP_ID_VAR, 0x0)

    def resolve_file_path(self, file_path: str) -> str:
        if pathlib.Path(file_path).is_absolute():
            return file_path
        (_, absolute_path, _, _, user_canceled) = (
            self._sequence_context.Engine.FindFileEx(
                fileToFind=file_path,
                absolutePath=None,
                srchDirType=None,
                searchDirectoryIndex=None,
                userCancelled=None,
                searchContext=self._sequence_context.SequenceFile,
            )
        )
        if user_canceled:
            raise RuntimeError("File lookup canceled by user.")
        return absolute_path


def configure_logging(verbosity: int) -> None:
    """Configure logging for this process."""
    if verbosity > 1:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=level)


F = TypeVar("F", bound=Callable)


def verbosity_option(func: F) -> F:
    """Decorator for --verbose command line option."""
    return click.option(
        "-v", "--verbose", "verbosity", count=True,
        help="Enable verbose logging. Repeat to increase verbosity.",
    )(func)
```

---

## Complete Example: Simple DC Voltage Measurement

```python
"""Source and measure a DC voltage with an NI SMU."""

import logging
import pathlib
import sys
import threading
from collections.abc import Iterable
from contextlib import ExitStack

import click
import ni_measurement_plugin_sdk_service as nims
import nidcpower
from _helpers import configure_logging, verbosity_option

script_or_exe = sys.executable if getattr(sys, "frozen", False) else __file__
service_directory = pathlib.Path(script_or_exe).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "DCVoltageMeasurement.serviceconfig",
    ui_file_paths=[service_directory / "DCVoltageMeasurement.measui"],
)


@measurement_service.register_measurement
@measurement_service.configuration(
    "pin_names", nims.DataType.IOResourceArray1D, ["Pin1"],
    instrument_type=nims.session_management.INSTRUMENT_TYPE_NI_DCPOWER,
)
@measurement_service.configuration("voltage_level", nims.DataType.Double, 6.0)
@measurement_service.configuration("current_limit", nims.DataType.Double, 0.01)
@measurement_service.output("voltage_measurements", nims.DataType.DoubleArray1D)
@measurement_service.output("current_measurements", nims.DataType.DoubleArray1D)
@measurement_service.output("in_compliance", nims.DataType.BooleanArray1D)
def measure(
    pin_names: Iterable[str],
    voltage_level: float,
    current_limit: float,
) -> tuple[list[float], list[float], list[bool]]:
    """Source and measure a DC voltage."""
    logging.info("Executing measurement: pin_names=%s voltage_level=%g", pin_names, voltage_level)

    cancellation_event = threading.Event()
    measurement_service.context.add_cancel_callback(cancellation_event.set)

    with measurement_service.context.reserve_sessions(pin_names) as reservation:
        with reservation.initialize_nidcpower_sessions() as session_infos:
            for session_info in session_infos:
                channels = session_info.session.channels[session_info.channel_list]
                channels.source_mode = nidcpower.SourceMode.SINGLE_POINT
                channels.output_function = nidcpower.OutputFunction.DC_VOLTAGE
                channels.current_limit = current_limit
                channels.voltage_level = voltage_level

            with ExitStack() as stack:
                for session_info in session_infos:
                    channels = session_info.session.channels[session_info.channel_list]
                    stack.enter_context(channels.initiate())

                voltages, currents, compliance = [], [], []
                for session_info in session_infos:
                    channels = session_info.session.channels[session_info.channel_list]
                    measurements = channels.measure_multiple()
                    for m in measurements:
                        voltages.append(m.voltage)
                        currents.append(m.current)
                        compliance.append(m.in_compliance)

    logging.info("Completed measurement")
    return (voltages, currents, compliance)


@click.command
@verbosity_option
def main(verbosity: int) -> None:
    """Source and measure a DC voltage with an NI SMU."""
    configure_logging(verbosity)
    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")

if __name__ == "__main__":
    main()
```

---

## Generator CLI

Scaffold a new measurement plug-in:
```bash
ni-measurement-plugin-generator "My Measurement"
```

With all options:
```bash
ni-measurement-plugin-generator "My Measurement" \
    --measurement-version 1.0.0 \
    --ui-file MyMeasurement.measui \
    --service-class com.example.MyMeasurement_Python \
    --description-url https://example.com/docs \
    --directory-out ./my_measurement
```

Generate a measurement client:
```bash
ni-measurement-plugin-client-generator \
    --measurement-service-class "com.example.MyMeasurement_Python" \
    --module-name "my_measurement_client" \
    --class-name "MyMeasurementClient"
```

---

## Static Registration

To make a measurement visible in InstrumentStudio without manually running it:

1. Ensure `.serviceconfig` has `"path": "start.bat"`
2. Copy the measurement directory to:
   `C:\ProgramData\National Instruments\Plug-Ins\Measurements\<measurement_name>\`
3. Re-create the virtual environment in the new location: `poetry install`
4. The NI Discovery Service will auto-discover and launch the measurement

---

## Streaming Measurements

For measurements that update the UI periodically:

```python
@measurement_service.register_measurement
@measurement_service.configuration("Duration", nims.DataType.Double, 10.0)
@measurement_service.output("Current Value", nims.DataType.Double)
def measure(duration: float) -> tuple[float]:
    import time
    start = time.time()
    while time.time() - start < duration:
        if measurement_service.context.time_remaining <= 0:
            break
        current_value = read_sensor()
        yield (current_value,)  # yield instead of return for streaming
        time.sleep(0.1)
```
