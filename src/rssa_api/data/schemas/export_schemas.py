import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field

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
    is_negative: bool

    model_config = ConfigDict(from_attributes=True)


class ExportSurveyScaleLevel(BaseModel):
    label: str
    value: int

    model_config = ConfigDict(from_attributes=True)


class StudyAttentionCheckMinimalRead(BaseModel):
    expected_survey_scale_level_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class ExportParticipantAttentionCheckResponse(BaseModel):
    responded_survey_scale_level_id: uuid.UUID | None = Field(exclude=True, repr=False)
    study_attention_check: StudyAttentionCheckMinimalRead = Field(exclude=True, repr=False)

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    def passed_attention(self) -> bool:
        if not self.responded_survey_scale_level_id:
            return False
        return self.responded_survey_scale_level_id == self.study_attention_check.expected_survey_scale_level_id


class ExportParticipantSurveyResponse(BaseModel):
    """Triggers joinedload() for the 1-to-1 context lookups."""

    study_step: ExportStudyStep
    survey_construct: ExportSurveyConstruct
    survey_item: ExportSurveyItem | None = None
    survey_scale_level: ExportSurveyScaleLevel | None = None

    model_config = ConfigDict(from_attributes=True)


class ParticipantExportSchema(BaseModel):
    """The root schema passed to the dynamic repository loader."""

    id: uuid.UUID
    current_status: str
    study_condition: ExportStudyCondition

    survey_responses: list[ExportParticipantSurveyResponse] = Field(default_factory=list)
    attention_check_responses: list[ExportParticipantAttentionCheckResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DynamicPayload(BaseModel):
    """Schema for dynamic payload with extra fields."""

    experiment_condition: str | None = None
    extra: dict[str, Any] = {}

    model_config = {'extra': 'allow'}


class ExportParticipantStudyInteraction(BaseModel):
    context_tag: str = Field(exclude=True, repr=False)
    created_at: datetime = Field(exclude=True, repr=False)
    payload_json: dict[str, Any]
    model_config = ConfigDict(from_attributes=True)


class ParticipantExplicitInteractionsSchema(BaseModel):
    """The root schema passed to the dynamic repository loader for the interaction data."""

    id: uuid.UUID
    current_status: str
    study_condition: ExportStudyCondition

    activity_responses: list[ExportParticipantStudyInteraction] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ExportParticipantFeedback(BaseModel):
    response_text: str
    model_config = ConfigDict(from_attributes=True)


class ParticipantFeedbackSchema(BaseModel):
    id: uuid.UUID
    current_status: str
    study_condition: ExportStudyCondition
    freeform_responses: list[ExportParticipantFeedback]
    model_config = ConfigDict(from_attributes=True)


def _build_base_acronym(construct_name: str) -> str:
    """Extracts the base acronym, stopping at the first non-alpha word."""
    words = construct_name.split()
    acronym_chars = []

    for word in words:
        if not word:
            continue
        if not word[0].isalpha():
            break
        acronym_chars.append(word[0].upper())

    return ''.join(acronym_chars) or 'Q'


def _get_or_create_shortcode(
    full_header: str,
    construct_name: str,
    header_mapping: dict[str, str],
    construct_registry: dict[str, str],
    used_acronyms: set[str],
    item_counters: dict[str, int],
) -> str:
    """Fetches existing shortcode or generates a new one, handling collisions."""
    if full_header in header_mapping:
        return header_mapping[full_header]

    if construct_name not in construct_registry:
        base_acronym = _build_base_acronym(construct_name)
        candidate = base_acronym
        counter = 1

        while candidate in used_acronyms:
            counter += 1
            candidate = f'{base_acronym}{counter}'

        construct_registry[construct_name] = candidate
        used_acronyms.add(candidate)
        item_counters[construct_name] = 0

    item_counters[construct_name] += 1
    shortcode = f'{construct_registry[construct_name]}_{item_counters[construct_name]}'

    header_mapping[full_header] = shortcode
    return shortcode


def flatten_participant_for_csv(
    p: ParticipantExportSchema,
    header_mapping: dict[str, str],
    construct_registry: dict[str, str],
    used_acronyms: set[str],
    item_counters: dict[str, int],
) -> dict[str, str]:
    """Pivots participant survey data into a flat CSV row format."""
    flat_row = {
        'Participant_ID': generate_code_from_uuid(p.id),
        'Status': p.current_status,
        'Condition': p.study_condition.name if p.study_condition else 'None',
    }

    for resp in p.survey_responses:
        step_name = resp.study_step.name
        step_name = resp.study_step.name
        construct_name = resp.survey_construct.name

        item_text = resp.survey_item.text if resp.survey_item else 'General'
        is_neg = resp.survey_item.is_negative if resp.survey_item else False

        full_header = f'{step_name} | {construct_name} - {item_text}'

        short_col_header = _get_or_create_shortcode(
            full_header, construct_name, header_mapping, construct_registry, used_acronyms, item_counters
        )

        short_col_header_label = f'{short_col_header}_wlabel'
        answer = ''
        value = 0

        if resp.survey_scale_level:
            value = resp.survey_scale_level.value * -1 if is_neg else resp.survey_scale_level.value
            answer = f'{resp.survey_scale_level.value} - {resp.survey_scale_level.label}'

        flat_row[short_col_header_label] = answer
        flat_row[short_col_header] = str(value)

    for i, resp in enumerate(p.attention_check_responses, 1):
        col_header_label = f'attention_check_{i}'
        short_header_label = f'achk_{i}'
        header_mapping[col_header_label] = short_header_label
        flat_row[short_header_label] = str(resp.passed_attention)

    return flat_row


def flatten_participant_interactions(p: ParticipantExplicitInteractionsSchema) -> dict[str, str]:
    """Pivots participant interaction data into a flat row format."""
    flat_row = {
        'Participant_ID': generate_code_from_uuid(p.id),
        'Status': p.current_status,
        'Condition': p.study_condition.name if p.study_condition else 'None',
    }
    sorted_interactions = sorted(p.activity_responses, key=lambda x: x.created_at)
    for i, interaction in enumerate(sorted_interactions):
        payload_data = interaction.payload_json.copy()

        extra_fields = payload_data.pop('extra', {})
        if isinstance(extra_fields, dict):
            payload_data.update(extra_fields)

        for key, value in payload_data.items():
            col_name = f'{key}_{i}'
            flat_row[col_name] = str(value) if value is not None else ''

    return flat_row


def flatten_participant_feedback(p: ParticipantFeedbackSchema) -> dict[str, str]:
    """Pivots participant feedback data into a flat row format."""
    flat_row = {
        'Participant_ID': generate_code_from_uuid(p.id),
        'Status': p.current_status,
        'Condition': p.study_condition.name if p.study_condition else 'None',
    }

    for i, response in enumerate(p.freeform_responses):
        col_name = f'feedback_{i}'
        flat_row[col_name] = response.response_text or ''

    return flat_row
