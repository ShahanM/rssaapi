ADMIN_USERS_TAG = 'Users [Admin]'
ADMIN_MOVIES_TAG = 'Movies [Admin]'
ADMIN_STUDIES_TAG = 'Studies [Admin]'
ADMIN_STUDY_CONDITIONS_TAG = 'Study Conditions [Admin]'
ADMIN_STUDY_STEPS_TAG = 'Study Steps [Admin]'
ADMIN_STEP_PAGES_TAG = 'Step Pages [Admin]'
ADMIN_SURVEY_CONSTRUCTS_TAG = 'Survey Constructs [Admin]'
ADMIN_CONSTRUCT_ITEMS_TAG = 'Construct Items [Admin]'
ADMIN_CONSTRUCT_SCALES_TAG = 'Construct Scales [Admin]'
ADMIN_SCALE_LEVELS_TAG = 'Scale Levels [Admin]'
ADMIN_SURVEY_PAGES_TAG = 'Survey Page Content [Admin]'

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
