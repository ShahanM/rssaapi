import uuid
from datetime import datetime, timezone
from typing import Dict, List

from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session


class StudyResponseRepository:
	def __init__(self, db: Session):
		self.db = db


# def get_responses(
# 	db: Session, participant: StudyParticipant, construct_id: uuid.UUID, item_ids: List[uuid.UUID]
# ) -> Dict[uuid.UUID, ParticipantResponse]:
# 	if not item_ids:
# 		return {}

# 	reponses = (
# 		db.query(ParticipantSurveyResponse)
# 		.where(
# 			and_(
# 				ParticipantSurveyResponse.participant_id == participant.id,
# 				ParticipantSurveyResponse.construct_id == construct_id,
# 				ParticipantSurveyResponse.item_id.in_(item_ids),
# 			)
# 		)
# 		.all()
# 	)

# 	if not reponses:
# 		return {}

# 	return {res.item_id: res for res in reponses}


# def get_response(
# 	db: Session, participant: StudyParticipant, construct_id: uuid.UUID, item_id: uuid.UUID
# ) -> ParticipantResponse:
# 	if not item_id:
# 		return None

# 	response = (
# 		db.query(ParticipantSurveyResponse)
# 		.where(
# 			and_(
# 				ParticipantSurveyResponse.participant_id == participant.id,
# 				ParticipantSurveyResponse.construct_id == construct_id,
# 				ParticipantSurveyResponse.item_id == item_id,
# 			)
# 		)
# 		.first()
# 	)

# 	return response


# def create_survey_response(db: Session, participant_id: uuid.UUID, response: SurveyResponse) -> bool:
# 	participant = db.query(StudyParticipant).where(StudyParticipant.id == participant_id).first()
# 	if not participant:
# 		raise HTTPException(status_code=404, detail='Participant not found')

# 	pcontent = db.query(PageContent).where(PageContent.page_id == response.page_id).first()
# 	res = get_responses(
# 		db, participant, pcontent.content_id, [res_item.item_id for res_item in response.responses if res_item.item_id]
# 	)

# 	if res:
# 		for res_item in response.responses:
# 			if res_item.item_id in res:
# 				if res[res_item.item_id].response != res_item.response:
# 					res[res_item.item_id].response = res_item.response
# 					res[res_item.item_id].date_modified = datetime.now(timezone.utc)
# 					db.add(res[res_item.item_id])
# 		db.commit()
# 		return True

# 	presponses = []
# 	for res_item in response.responses:
# 		presponse = ParticipantSurveyResponse(
# 			participant_id=participant.id,
# 			construct_id=pcontent.content_id,
# 			response=res_item.response,
# 			item_id=res_item.item_id,
# 		)

# 		presponses.append(presponse)

# 	db.add_all(presponses)
# 	db.flush()
# 	db.commit()

# 	if all(True for res in presponses if res.id):
# 		return True

# 	return False


# def create_text_response(db: Session, participant_id: uuid.UUID, response: TextResponse) -> bool:
# 	participant = db.query(StudyParticipant).where(StudyParticipant.id == participant_id).first()
# 	if not participant:
# 		raise HTTPException(status_code=404, detail='Participant not found')

# 	res = get_response(db, participant, response.construct_id, response.item_id)

# 	if res:
# 		if res.response != response.response:
# 			res.response = response.response
# 			res.date_modified = datetime.now(timezone.utc)
# 			db.add(res)
# 			db.commit()
# 			return True
# 		return False

# 	presponse = ParticipantResponse(
# 		participant_id=participant.id,
# 		construct_id=response.construct_id,
# 		response=response.response,
# 		item_id=response.item_id,
# 	)

# 	db.add(presponse)
# 	db.commit()
# 	db.refresh(presponse)

# 	if presponse.id:
# 		return True

# 	return False


# def batch_create_text_responses(db: Session, participant_id: uuid.UUID, responses: List[TextResponse]) -> bool:
# 	participant = db.query(StudyParticipant).where(StudyParticipant.id == participant_id).first()
# 	if not participant:
# 		raise HTTPException(status_code=404, detail='Participant not found')

# 	presponses = []
# 	for response in responses:
# 		# TODO: This can be its own function and reused in create_text_response
# 		presponse = ParticipantResponse(
# 			participant_id=participant.id, step_id=participant.current_step, response=response.response
# 		)

# 		presponses.append(presponse)

# 	db.add_all(presponses)
# 	db.flush()
# 	db.commit()

# 	if all([True for res in presponses if res.id]):
# 		return True

# 	return False
