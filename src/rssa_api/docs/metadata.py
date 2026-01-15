"""Metadata for API documentation."""

from enum import Enum
from typing import Any


class ResourceTagsEnum(Enum):
    """Tags for resource endpoints."""

    movie = 'Resource: Movie'
    study = 'Resource: Study'
    survey = 'Resource: Survey'
    response = 'Resource: Response'
    participant = 'Resouce: Participant'
    feedback = 'Resource: Feedback'


class RSTagsEnum(Enum):
    """Tags for the Recommender System."""

    rssa = 'Recommender System for Self Actualization'


tags_metadata: list[dict[str, Any]] = [
    {
        'name': ResourceTagsEnum.movie.value,
        'description': 'This is the movie dataset adapated from the MovieLens dataset of IMDB movies.',
        'externalDocs': {
            'description': 'Movielens Dataset can be found at the MovieLens website.',
            'url': 'https://grouplens.org/datasets/movielens/',
        },
    },
    {
        'name': ResourceTagsEnum.study.value,
        'description': 'The study API is a study meta API that is used to create and manage the study.'
        + 'As such, it is only available to admin users.',
    },
    {
        'name': ResourceTagsEnum.participant.value,
        'description': 'The user API is used to record study participant responses.',
    },
]
