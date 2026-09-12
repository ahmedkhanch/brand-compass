"""Strict contracts for server-authorized report execution."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ReportJobBrandInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    name: str = Field(min_length=1)
    website_url: str
    industry: str
    competitor: str


class ReportJobExecutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    report_id: str = Field(min_length=1, max_length=255)


class ReportJobClaims(ReportJobExecutionRequest):
    user_id: str = Field(min_length=1, max_length=255)
    brand_input: ReportJobBrandInput


class ReportJobExecutionResponse(BaseModel):
    report_id: str
    status: Literal["complete", "failed"]


class ReportJobError(BaseModel):
    detail: str
