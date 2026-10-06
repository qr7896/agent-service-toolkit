from langchain_core.messages import HumanMessage, SystemMessage

from evals.e1c_evaluation_2_controller_generation_dev import messages


def test_a_output_instructions_system_data_human_and_final_request():
    frozen = {"issue": "SYNTHETIC_PUBLIC_ISSUE_TOKEN", "windows": [], "public_fixture_facts": []}
    value = messages(frozen, "A")
    assert isinstance(value[0], SystemMessage)
    assert frozen["issue"] not in value[0].content
    assert isinstance(value[1], HumanMessage) and frozen["issue"] in value[1].content
    assert isinstance(value[-1], HumanMessage) and "Now generate" in value[-1].content
    assert '"source"' in value[-1].content and "No execution metadata" in value[-1].content


def test_b_retains_seven_field_oracle_contract():
    frozen = {"issue": "SYNTHETIC_PUBLIC_ISSUE_TOKEN", "windows": [], "public_fixture_facts": []}
    value = messages(frozen, "B")
    assert isinstance(value[0], SystemMessage) and frozen["issue"] not in value[0].content
    assert "control_action" in value[-1].content and "expected_quote" in value[-1].content
