from enum import Enum

class TagsMetadataEnum(Enum):
	movie = 'Movie'
	ers = 'Movie (ERS)'
	study = 'Study'
	participant = 'participant'
	pref_comm = 'preference community'
	pref_viz = 'preference visualization'
	meta = 'Meta'



tags_metadata = [
	{
		'name': TagsMetadataEnum.movie.value,
		'description': 'This is the movie dataset adapated from the MovieLens dataset of IMDB movies.',
		'externalDocs': {
			'description': 'Movielens Dataset can be found at the MovieLens website.',
			'url': 'https://grouplens.org/datasets/movielens/',
		}
	},
	{
		'name': TagsMetadataEnum.ers.value,
		'description': 'This is the movie dataset with emotional valence ratings from the ERS dataset.'
	},
	{
		'name': TagsMetadataEnum.study.value,
		'description': 'The study API is a study meta API that is used to create and manage the study.' \
			+ 'As such, it is only available to admin users.'
	},
	{
		'name': TagsMetadataEnum.participant.value,
		'description': 'The user API is used to record study participant responses.'
	},
	{
		'name': TagsMetadataEnum.pref_comm.value,
		'description': 'These are the APIs used to create and manage the preference communities.'
	},
	{
		'name': TagsMetadataEnum.pref_viz.value,
		'description': 'These are the APIs used to create and manage the preference visualizations.'
	},
	{
		'name': TagsMetadataEnum.meta.value,
		'description': 'These are the metadata APIs that are used to create and manage the metadata for the study.'
	}
]

class AppMetadata:
	title = 'RSSA Project API'
	summary = 'API for all the RSSA projects, experiments, and alternate movie databases.'
	description = '''
		This API is a FastAPI based API that is used to manage the RSSA project. 
		The API is used to manage the study, the participants, the movies, 
		the preference communities, and the preference visualizations. 
		The API is also used to manage the metadata for the study.
	'''