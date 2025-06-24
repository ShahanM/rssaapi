from enum import Enum


class TagsMetadataEnum(Enum):
	movie = 'Movie'
	study = 'Study'
	survey = 'Survey'
	response = 'Response'
	participant = 'Participant'
	feedback = 'feedback'
	rssa = 'Recommender System for Self Actualization'
	admin = 'Admin'


tags_metadata = [
	{
		'name': TagsMetadataEnum.movie.value,
		'description': 'This is the movie dataset adapated from the MovieLens dataset of IMDB movies.',
		'externalDocs': {
			'description': 'Movielens Dataset can be found at the MovieLens website.',
			'url': 'https://grouplens.org/datasets/movielens/',
		},
	},
	{
		'name': TagsMetadataEnum.study.value,
		'description': 'The study API is a study meta API that is used to create and manage the study.'
		+ 'As such, it is only available to admin users.',
	},
	{
		'name': TagsMetadataEnum.participant.value,
		'description': 'The user API is used to record study participant responses.',
	},
	{
		'name': TagsMetadataEnum.rssa.value,
		'description': 'The user API is used to record study participant responses.',
	},
	{
		'name': TagsMetadataEnum.admin.value,
		'description': 'The user API is used to record study participant responses.',
	},
]


class AppMetadata:
	title = 'RSSA Project API'
	summary = 'API for all the RSSA projects, experiments, and alternate movie databases.'
	description = """
		This API is a FastAPI based API that is used to manage the RSSA project. 
		The API is used to manage the study, the participants, the movies, 
		the preference communities, and the preference visualizations. 
		The API is also used to manage the metadata for the study.
	"""
