from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app import services


class PersonInput(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    contact_number: str | None = Field(default=None, max_length=30)
    role: Literal["student", "staff", "admin"] = "student"

    @field_validator("full_name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Full name cannot be blank")
        return value

    @staticmethod
    def list_people(role=None):
        return services.list_people(role)

    @staticmethod
    def get_person(person_id):
        return services.get_person(person_id)

    @staticmethod
    def create_person(person_input):
        return services.create_person(person_input.model_dump())

    @staticmethod
    def update_person(person_id, person_input):
        return services.update_person(person_id, person_input.model_dump())

    @staticmethod
    def delete_person(person_id):
        return services.delete_person(person_id)


class Person(PersonInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: str


class ItemReportInput(BaseModel):
    report_type: Literal["lost", "found"]
    item_name: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=60)
    description: str = Field(min_length=5, max_length=1500)
    color: str | None = Field(default=None, max_length=60)
    location: str = Field(min_length=2, max_length=160)
    event_date: date
    reporter_id: int = Field(gt=0)

    @field_validator("item_name", "category", "description", "location")
    @classmethod
    def trim_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value

    @staticmethod
    def list_items(report_type=None, status=None, category=None, location=None, search=None, reporter_id=None):
        return services.list_items(report_type, status, category, location, search, reporter_id)

    @staticmethod
    def get_item(item_id):
        return services.get_item(item_id)

    @staticmethod
    def create_item(item_input):
        return services.create_item(item_input.model_dump())

    @staticmethod
    def update_item(item_id, item_input):
        return services.update_item(item_id, item_input.model_dump())

    @staticmethod
    def delete_item(item_id):
        return services.delete_item(item_id)

    @staticmethod
    def list_history(item_id):
        return services.list_history(item_id)

    @staticmethod
    def close_item(item_id, close_input):
        return services.close_item(item_id, close_input.changed_by, close_input.note)


class ItemReportUpdate(BaseModel):
    item_name: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=60)
    description: str = Field(min_length=5, max_length=1500)
    color: str | None = Field(default=None, max_length=60)
    location: str = Field(min_length=2, max_length=160)
    event_date: date


class ItemReport(ItemReportInput):
    id: int
    status: Literal["open", "under_review", "matched", "claimed", "closed"]
    created_at: str
    updated_at: str


class ClaimInput(BaseModel):
    item_id: int = Field(gt=0)
    claimant_id: int = Field(gt=0)
    claim_details: str = Field(min_length=10, max_length=1500)

    @field_validator("claim_details")
    @classmethod
    def trim_details(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Claim details cannot be blank")
        return value

    @staticmethod
    def list_claims(status=None, item_id=None, claimant_id=None):
        return services.list_claims(status, item_id, claimant_id)

    @staticmethod
    def get_claim(claim_id):
        return services.get_claim(claim_id)

    @staticmethod
    def create_claim(claim_input):
        return services.create_claim(claim_input.model_dump())

    @staticmethod
    def review_claim(claim_id, review_input):
        return services.review_claim(claim_id, review_input.decision, review_input.reviewed_by, review_input.review_note)

    @staticmethod
    def delete_claim(claim_id):
        return services.delete_claim(claim_id)


class ClaimReviewInput(BaseModel):
    decision: Literal["approved", "rejected"]
    reviewed_by: int = Field(gt=0)
    review_note: str | None = Field(default=None, max_length=1000)


class Claim(ClaimInput):
    id: int
    status: Literal["pending", "approved", "rejected"]
    reviewed_by: int | None
    review_note: str | None
    created_at: str
    reviewed_at: str | None


class ItemCloseInput(BaseModel):
    changed_by: int = Field(gt=0)
    note: str | None = Field(default=None, max_length=1000)


class ItemStatusHistory(BaseModel):
    id: int
    item_id: int
    previous_status: str | None
    new_status: str
    changed_by: int
    note: str | None
    changed_at: str
