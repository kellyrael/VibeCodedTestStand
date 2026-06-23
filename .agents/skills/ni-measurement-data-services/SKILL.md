---
name: ni-measurement-data-services
description: >
  Generate correct Python code for logging measurement data to NI Measurement Data Services (MDS)
  using the ni.datastore package. Covers the DataStoreClient and MetadataStoreClient APIs for
  creating test results, steps, publishing measurements and conditions, querying data, and
  registering metadata (UUTs, operators, test stations, hardware items, software items).
  Use this skill whenever the user mentions MDS, Measurement Data Services, ni.datastore,
  DataStoreClient, data logging, test results, publishing measurements, or asks to store
  measurement data in a centralized data service. Also trigger when the user asks about
  querying historical test results, conditions, or measurement data from MDS.
  Also trigger when the user says "add logging", "log results", "measurement logging",
  "log to MDS", "log measurements", "add measurement logging", "record results",
  or any variation of logging or recording test/measurement data.
argument-hint: "Describe the measurement data to log, read, or the metadata to register"
user-invocable: true
---

# Measurement Data Services (MDS) Skill

When this skill is triggered, read the full reference file before generating any code or guidance:

**Reference file**: [ni_datastore.md](./references/ni_datastore.md)

That file contains the complete, verified patterns for:

- Package info, installation, and prerequisites
- Data model hierarchy (TestResult → Step → Measurement/Condition)
- DataStoreClient API — create_test_result, create_step, publish_measurement, publish_measurement_batch, publish_condition, publish_condition_batch, read_data, and all query methods
- MetadataStoreClient API — create/get/query for Uut, UutInstance, Operator, TestStation, HardwareItem, SoftwareItem, TestDescription, TestAdapter, ExtensionSchema
- Outcome enum (PASSED, FAILED, INDETERMINATE, UNSPECIFIED)
- TestResult, Step, PublishedMeasurement, PublishedCondition type constructors with all parameters
- Complete examples: logging a measurement sweep, querying/reading back data, full metadata + data pipeline
- 8 common mistakes and how to avoid them

Always read the reference file first — do not generate MDS code from memory alone.

## References

- [ni_datastore.md (Python API - primary)](./references/ni_datastore.md)
- [MDS Python API](./references/MDS-Python-API.md)
- [MDS C# API](./references/MDS-CSharp-API.md)
- [MDS C# Publish](./references/MDS-CSharp-Publish-Skill.md)
