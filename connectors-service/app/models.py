from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict
from uuid import UUID


class MySQLCredentials(BaseModel):
    host: str
    port: int
    databaseName: str
    username: str
    password: str


class PostgreSQLCredentials(BaseModel):
    host: str
    port: int
    databaseName: str
    username: str
    password: str


class ModelInventoryModel(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    client_id: str
    model_name: str
    provider_name: str = None
    weights_location: str = None
    bias_notes: str = None
    description: str = None
    industry_use_case: str = None
    data_store_types: str = None
    compliance_requirements: str = None


class AddSDEModel(BaseModel):
    name: str
    data_type: str
    sensitivity: str
    regex: str
    classification: str
    selected_industry: str
