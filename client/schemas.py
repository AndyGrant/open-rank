from pydantic import BaseModel, Field
from typing import Optional

# ============================================================================
# Request Schemas
# ============================================================================

class ConnectRequest(BaseModel):
    username  : str
    password  : str
    hardware  : dict
    worker_id : Optional[int] = None
    secret    : Optional[str] = None

class PullImageRequest(BaseModel):
    worker_id : int
    secret    : str
    engine_id : int

class PullBookRequest(BaseModel):
    worker_id      : int
    secret         : str
    rating_list_id : int

# ============================================================================
# Response Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    error: str

class WarningResponse(BaseModel):
    warning: str

class ConnectResponse(BaseModel):
    secret    : str
    worker_id : int

class WorkloadConfig(BaseModel):
    games        : int
    pairing_id   : int
    thread_count : int
    hashsize     : int
    base_time    : int
    increment    : int

class BookInfo(BaseModel):
    rating_list_id : int
    name           : str
    sha256         : str

class EngineInfo(BaseModel):
    image     : str
    nps       : int
    engine_id : int
    sha256    : str

class WorkloadResponse(BaseModel):
    config   : WorkloadConfig
    book     : BookInfo
    engine_a : EngineInfo
    engine_b : EngineInfo
