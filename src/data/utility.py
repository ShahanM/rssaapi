def sa_obj_to_dict(obj):
	from sqlalchemy import inspect

	return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}
