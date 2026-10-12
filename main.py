from typing import Literal

from fastapi import FastAPI, Query, Response, status

from app.database import initialize_database
from app.models import (
    Claim,
    ClaimInput,
    ClaimReviewInput,
    ItemCloseInput,
    ItemReport,
    ItemReportInput,
    ItemReportUpdate,
    ItemStatusHistory,
    Person,
    PersonInput,
)

app = FastAPI(
    title="Campus Lost and Found Management API",
    description="Manage campus lost and found reports, claims, and item status history.",
    version="1.0.0",
)


@app.get("/", tags=["General"])
def home():
    return {"message": "Welcome to the Campus Lost and Found Management API. Visit /docs to try the API."}


@app.get("/people", response_model=list[Person], tags=["People"])
def get_people(role: Literal["student", "staff", "admin"] | None = None):
    return PersonInput.list_people(role=role)


@app.get("/people/{person_id}", response_model=Person, tags=["People"])
def get_person(person_id: int):
    return PersonInput.get_person(person_id=person_id)


@app.post("/people", response_model=Person, status_code=status.HTTP_201_CREATED, tags=["People"])
def create_person(person: PersonInput):
    return PersonInput.create_person(person_input=person)


@app.put("/people/{person_id}", response_model=Person, tags=["People"])
def update_person(person_id: int, person: PersonInput):
    return PersonInput.update_person(person_id=person_id, person_input=person)


@app.delete("/people/{person_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["People"])
def delete_person(person_id: int):
    PersonInput.delete_person(person_id=person_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/items", response_model=list[ItemReport], tags=["Item Reports"])
def get_items(
    report_type: Literal["lost", "found"] | None = None,
    status_filter: Literal["open", "under_review", "matched", "claimed", "closed"] | None = Query(default=None, alias="status"),
    category: str | None = None,
    location: str | None = None,
    search: str | None = None,
    reporter_id: int | None = Query(default=None, gt=0),
):
    return ItemReportInput.list_items(report_type, status_filter, category, location, search, reporter_id)


@app.get("/items/{item_id}", response_model=ItemReport, tags=["Item Reports"])
def get_item(item_id: int):
    return ItemReportInput.get_item(item_id=item_id)


@app.post("/items", response_model=ItemReport, status_code=status.HTTP_201_CREATED, tags=["Item Reports"])
def create_item(item: ItemReportInput):
    return ItemReportInput.create_item(item_input=item)


@app.put("/items/{item_id}", response_model=ItemReport, tags=["Item Reports"])
def update_item(item_id: int, item: ItemReportUpdate):
    return ItemReportInput.update_item(item_id=item_id, item_input=item)


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Item Reports"])
def delete_item(item_id: int):
    ItemReportInput.delete_item(item_id=item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/items/{item_id}/history", response_model=list[ItemStatusHistory], tags=["Item Reports"])
def get_item_history(item_id: int):
    return ItemReportInput.list_history(item_id=item_id)


@app.patch("/items/{item_id}/close", response_model=ItemReport, tags=["Item Reports"])
def close_item(item_id: int, request: ItemCloseInput):
    return ItemReportInput.close_item(item_id=item_id, close_input=request)


@app.get("/claims", response_model=list[Claim], tags=["Claims"])
def get_claims(
    status_filter: Literal["pending", "approved", "rejected"] | None = Query(default=None, alias="status"),
    item_id: int | None = Query(default=None, gt=0),
    claimant_id: int | None = Query(default=None, gt=0),
):
    return ClaimInput.list_claims(status_filter, item_id, claimant_id)


@app.get("/claims/{claim_id}", response_model=Claim, tags=["Claims"])
def get_claim(claim_id: int):
    return ClaimInput.get_claim(claim_id=claim_id)


@app.post("/claims", response_model=Claim, status_code=status.HTTP_201_CREATED, tags=["Claims"])
def create_claim(claim: ClaimInput):
    return ClaimInput.create_claim(claim_input=claim)


@app.patch("/claims/{claim_id}/review", response_model=Claim, tags=["Claims"])
def review_claim(claim_id: int, review: ClaimReviewInput):
    return ClaimInput.review_claim(claim_id=claim_id, review_input=review)


@app.delete("/claims/{claim_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Claims"])
def delete_claim(claim_id: int):
    ClaimInput.delete_claim(claim_id=claim_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


initialize_database()
