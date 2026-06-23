# GitHub Copilot Instructions

This project uses a set of NI (National Instruments) / Emerson Test & Measurement skills located in
.agents/skills/. Copilot should consult the relevant skill's SKILL.md and reference files when
answering questions or generating code related to the topics below.

## Available Skills

| Skill Folder | Topic | Trigger Keywords |
|---|---|---|
| `ni-hw-drivers` | NI Python instrument drivers (nidcpower, nidmm, niscope, nifgen, niswitch, nidigital, nise) | NI hardware, nimi-python, SMU, DMM, oscilloscope, fgen, signal generator, switch, PXI |
| `ni-hw-drivers-csharp` | NI instrument drivers for C# (.NET) | C#, .NET, NI drivers, RFmx, RFSA, RFSG |
| `creating-teststand-sequences` | NI TestStand sequence creation and automation | TestStand, sequence, .seq file, test sequence, step |
| `measurement-plugin` | NI Measurement Plugin SDK (Python & .NET) | measurement plugin, InstrumentStudio, MeasurementLink |
| `ni-measurement-data-services` | NI Measurement Data Services (MDS) for storing/retrieving test data | MDS, measurement data, datastore, publish results |
| `ni-datastore-query-odata` | Querying NI SystemLink/DataFinder via OData | OData, SystemLink, data query, DataFinder |
| `ni-systemlink-testmonitor-reporting` | NI SystemLink TestMonitor result/step publishing and troubleshooting | SystemLink, TestMonitor, publish results, TLS, REQUESTS_CA_BUNDLE |
| `ni-dependency-management` | NI package and dependency management | feeds, packages, nipkg, nimi-python versions |
| `ni-measurement-gui-winforms` | Building WinForms GUIs for NI measurement workflows | WinForms, GUI, measurement UI |
| `ni-rf` | RF measurement workflows (RFmx, RFSA, RFSG) | RF, RFmx, RFSA, RFSG, spectrum, signal analyzer |
| `ni-rf-hw-specs` | NI RF hardware specifications (VST family) | VST, PXIe-5840, PXIe-5860, RF hardware specs |
| `ni-tclk-synchronization` | NI TClk multi-device synchronization | TClk, synchronization, multi-device, timing |
| `nisyscfg-equipment-discovery` | NI System Configuration for hardware discovery | NI System Configuration, nisyscfg, hardware discovery, instrument discovery |

## General Guidelines

- When writing Python code for NI instruments, always read .agents/skills/ni-hw-drivers/SKILL.md
  and the relevant driver reference (e.g., 
eferences/nifgen.md) before generating code.
- When creating or modifying TestStand sequences, read .agents/skills/creating-teststand-sequences/SKILL.md.
- When creating or troubleshooting SystemLink TestMonitor publishing, read .agents/skills/ni-systemlink-testmonitor-reporting/SKILL.md.
- Use context managers (with statements) for all NI instrument sessions.
- Follow the patterns in the skill reference files exactly -- do not invent method names or enum values.
- When in doubt about an API, refer to the reference .md files in the skill's 
eferences/ folder.
