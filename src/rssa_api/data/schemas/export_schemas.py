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
    is_negative: bool

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


# def flatten_participant_for_csv(p: ParticipantExportSchema, header_mapping: dict[str, str]) -> dict[str, str]:
# def flatten_participant_for_csv(
#     p: ParticipantExportSchema,
#     header_mapping: dict[str, str],
#     construct_registry: dict[str, str],
#     used_acronyms: set[str],
#     item_counters: dict[str, int],
# ) -> dict[str, str]:
#     """Pivots data and builds a dynamic Question Codebook on the fly."""
#     flat_row = {
#         'Participant_ID': generate_code_from_uuid(p.id),
#         'Status': p.current_status,
#         'Condition': p.study_condition.name if p.study_condition else 'None',
#     }

#     for resp in p.survey_responses:
#         step_name = resp.study_step.name
#         construct_name = resp.survey_construct.name
#         item_text = ''
#         is_neg = False
#         if resp.survey_item:
#             item_text = resp.survey_item.text
#             is_neg = resp.survey_item.is_negative
#         else:
#             item_text = 'General'

#         full_header = f'{step_name} | {construct_name} - {item_text}'

#         if full_header not in header_mapping:
#             if construct_name not in construct_registry:
#                 words = construct_name.split()
#                 acronym_chars = []
#                 for word in words:
#                     if not word:
#                         continue
#                     if not word[0].isalpha():
#                         break
#                     acronym_chars.append(word[0].upper())
#                 base_acronym = ''.join(word[0].upper() for word in words if word)
#                 if not base_acronym:
#                     base_acronym = 'Q'
#                 candidate = base_acronym
#                 counter = 1
#                 while candidate in used_acronyms:
#                     counter += 1
#                     candidate = f'{base_acronym}{counter}'

#                 construct_registry[construct_name] = candidate
#                 used_acronyms.add(candidate)
#                 item_counters[construct_name] = 0
#             item_counters[construct_name] += 1
#             item_num = item_counters[construct_name]
#             acronym = construct_registry[construct_name]
#             header_mapping[full_header] = f'{acronym}_{item_num}'

#         short_col_header = header_mapping[full_header]
#         short_col_header_label = f'{header_mapping[full_header]}_wlabel'
#         answer = ''
#         value = 0
#         if resp.survey_scale_level:
#             value = resp.survey_scale_level.value * -1 if is_neg else resp.survey_scale_level.value
#             answer = f'{resp.survey_scale_level.value} - {resp.survey_scale_level.label}'

#         flat_row[short_col_header_label] = answer
#         flat_row[short_col_header] = str(value)


#     return flat_row
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
        # Extract base properties
        step_name = resp.study_step.name
        construct_name = resp.survey_construct.name

        item_text = resp.survey_item.text if resp.survey_item else 'General'
        is_neg = resp.survey_item.is_negative if resp.survey_item else False

        full_header = f'{step_name} | {construct_name} - {item_text}'

        # Get our dynamic shortcode using the helper
        short_col_header = _get_or_create_shortcode(
            full_header, construct_name, header_mapping, construct_registry, used_acronyms, item_counters
        )

        # Format the CSV output values
        short_col_header_label = f'{short_col_header}_wlabel'
        answer = ''
        value = 0

        if resp.survey_scale_level:
            value = resp.survey_scale_level.value * -1 if is_neg else resp.survey_scale_level.value
            answer = f'{resp.survey_scale_level.value} - {resp.survey_scale_level.label}'

        flat_row[short_col_header_label] = answer
        flat_row[short_col_header] = str(value)

    return flat_row
