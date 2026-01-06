from enum import Enum
from typing import Any, Dict, List


class Tags(Enum):
    movie = 'Movie'
    study = 'Study'
    survey = 'Survey'
    response = 'Response'
    participant = 'Participant'
    feedback = 'Feedback'


class RSTagsEnum(Enum):
    rssa = 'Recommender System for Self Actualization'


tags_metadata: List[Dict[str, Any]] = [
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
        'description': 'The study endpoint is primarily used to navigate through the study steps.',
    },
    {
        'name': Tags.participant.value,
        'description': 'The user API is used to record study participant responses.',
    },
]
