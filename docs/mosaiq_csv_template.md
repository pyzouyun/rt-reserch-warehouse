# MOSAIQ CSV Templates

The prototype avoids direct MOSAIQ database access. Export approved, read-only CSV files and place them in `data_templates/` or another folder passed to the importer.

## `mosaiq_patient.csv`

Columns: `PatientID`, `Sex`, `BirthYear`, `DiagnosisCode`, `DiagnosisText`.

`PatientID` is hashed and converted into `research_patient_id`. Do not export names, phone numbers, national IDs, addresses, or free text containing identifiers.

## `mosaiq_prescription.csv`

Columns: `PatientID`, `CourseID`, `PlanID`, `PrescriptionDoseGy`, `Fractions`, `DosePerFractionGy`, `Site`, `Technique`.

Rows load into `mosaiq_prescription`. `CourseID` and `PlanID` are hashed before storage.

## `mosaiq_fraction.csv`

Columns: `PatientID`, `CourseID`, `PlanID`, `FractionNumber`, `TreatmentDate`, `MachineName`, `DeliveredMU`, `Status`.

Rows load into `treatment_fraction`.

## `mosaiq_workflow.csv`

Columns: `PatientID`, `CourseID`, `WorkflowStep`, `Status`, `ScheduledDate`, `CompletedDate`, `OwnerRole`.

Rows load into `mosaiq_workflow`.
