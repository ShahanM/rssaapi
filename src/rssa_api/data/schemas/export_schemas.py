import uuid

from pydantic import BaseModel, ConfigDict, Field

from rssa_api.data.utility import generate_code_from_uuid


class ExportStudy(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True)


class ExportStudyCondition(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True)


class ExportStudyStep(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True)


class ExportSurveyConstruct(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True)


class ExportSurveyItem(BaseModel):
    text: str

    model_config = ConfigDict(from_attributes=True)


class ExportSurveyScaleLevel(BaseModel):
    label: str
    value: int

    model_config = ConfigDict(from_attributes=True)


class ExportParticipantSurveyResponse(BaseModel):
    """Triggers joinedload() for the 1-to-1 context lookups."""

    study_step: ExportStudyStep
    survey_construct: ExportSurveyConstruct
    survey_item: ExportSurveyItem | None = None
    survey_scale_level: ExportSurveyScaleLevel | None = None

    model_config = ConfigDict(from_attributes=True)


class ParticipantExportSchema(BaseModel):
    """The root schema passed to your dynamic repository loader."""

    id: uuid.UUID
    current_status: str
    study_condition: ExportStudyCondition

    survey_responses: list[ExportParticipantSurveyResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


def flatten_participant_for_csv(p: ParticipantExportSchema, header_mapping: dict[str, str]) -> dict[str, str]:
    """Pivots data and builds a dynamic Question Codebook on the fly."""
    flat_row = {
        'Participant_ID': generate_code_from_uuid(p.id),
        'Status': p.current_status,
        'Condition': p.study_condition.name if p.study_condition else 'None',
    }

    for resp in p.survey_responses:
        step_name = resp.study_step.name
        construct_name = resp.survey_construct.name
        item_text = resp.survey_item.text if resp.survey_item else 'General'
        full_header = f'{step_name} | {construct_name} - {item_text}'

        if full_header not in header_mapping:
            header_mapping[full_header] = f'Q_{len(header_mapping) + 1}'

        short_col_header = header_mapping[full_header]
        answer = ''
        if resp.survey_scale_level:
            answer = f'{resp.survey_scale_level.value} - {resp.survey_scale_level.label}'

        flat_row[short_col_header] = answer

    return flat_row
