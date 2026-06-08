"""Documentation metadata for the Admin API."""

ADMIN_USERS_TAG = 'Users'
ADMIN_MOVIES_TAG = 'Movies'
ADMIN_STUDIES_TAG = 'Studies'
ADMIN_STUDY_CONDITIONS_TAG = 'Study Conditions'
ADMIN_STUDY_STEPS_TAG = 'Study Steps'
ADMIN_STEP_PAGES_TAG = 'Step Pages'
ADMIN_SURVEY_CONSTRUCTS_TAG = 'Survey Constructs'
ADMIN_CONSTRUCT_ITEMS_TAG = 'Construct Items'
ADMIN_CONSTRUCT_SCALES_TAG = 'Construct Scales'
ADMIN_SCALE_LEVELS_TAG = 'Scale Levels'
ADMIN_SURVEY_PAGES_TAG = 'Survey Page Content'
ADMIN_STUDY_PARTICIPANTS_TAG = 'Study Participants'

admin_tags_metadata = [
    {
        'name': ADMIN_MOVIES_TAG,
        'description': 'This is the movie dataset adapated from the MovieLens dataset from GroupLens.',
        'externalDocs': {
            'description': 'Movielens Dataset can be found at the GroupLens website.',
            'url': 'https://grouplens.org/datasets/movielens/',
        },
    },
    {
        'name': ADMIN_STUDIES_TAG,
        'description': 'The /studies/ endpoint is used to manage studies.' + ' It is only available to admin users.',
    },
]
