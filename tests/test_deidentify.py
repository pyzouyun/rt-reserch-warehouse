from etl.deidentify import hash_identifier, research_patient_id


def test_hash_identifier_is_stable_and_salted() -> None:
    first = hash_identifier("PATIENT-001", salt="site-secret")
    second = hash_identifier("PATIENT-001", salt="site-secret")
    other_salt = hash_identifier("PATIENT-001", salt="other-secret")

    assert first == second
    assert first != other_salt
    assert len(first) == 64


def test_research_patient_id_has_nonidentifying_prefix() -> None:
    value = research_patient_id("PATIENT-001", salt="site-secret")

    assert value.startswith("RP-")
    assert "PATIENT" not in value
