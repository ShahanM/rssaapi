from enum import Enum
from typing import Any


class Tags(Enum):
    movie = 'Movies'
    study = 'Studies'
    study_step = 'Study Steps'
    page = 'Pages'
    survey = 'Survey page contents'
    construct = 'Survey Constructs'
    scale = 'Construct Scales'
    levels = 'Scale levels'
    response = 'Responses'
    participant = 'Participants'
    feedback = 'Feedbacks'
    user = ('Auth0 Users',)
    condition = 'Study conditions'
    item = 'Construct items'


class RSTagsEnum(Enum):
    rssa = 'Recommender System for Self Actualization'


admin_tags_metadata: list[dict[str, Any]] = [
    {
        'name': Tags.movie.value,
        'description': 'This is the movie dataset adapated from the MovieLens dataset from GroupLens.',
        'externalDocs': {
            'description': 'Movielens Dataset can be found at the GroupLens website.',
            'url': 'https://grouplens.org/datasets/movielens/',
        },
    },
    {
        'name': Tags.study.value,
        'description': 'The /studies/ endpoint is used to manage studies.' + ' It is only available to admin users.',
    },
    {
        'name': Tags.study_step.value,
        'description': '',
    },
]
