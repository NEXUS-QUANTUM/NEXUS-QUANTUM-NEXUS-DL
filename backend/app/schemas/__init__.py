# ==========================================================================
#  NexusDL 2.0 - Package Schémas
#  Fichier : backend/app/schemas/__init__.py
# ==========================================================================

"""
Package contenant tous les schémas Pydantic de NexusDL.

Ces schémas sont utilisés pour la validation des données, la sérialisation
et la désérialisation dans les endpoints API.
"""

# Schémas Job
from app.schemas.job import (
    JobBase,
    JobCreate,
    JobUpdate,
    JobResponse,
    JobListResponse,
    JobStatusUpdate,
    JobCancelRequest,
    JobRetryRequest,
    JobFilters,
)

# Schémas Library
from app.schemas.library import (
    LibraryMetadata,
    LibraryItemBase,
    LibraryItemCreate,
    LibraryItemUpdate,
    LibraryItemResponse,
    LibraryListResponse,
    LibraryStats,
    LibrarySearchFilters,
    LibraryActionResponse,
)

# Schémas Provider
from app.schemas.provider import (
    ProviderInfo,
    ProviderListResponse,
    ChapterInfo,
    SeriesInfo,
    SearchResult,
    SearchResponse,
    AnalysisResult,
    ProviderConfig,
    ProviderConfigUpdate,
    ProviderErrorResponse,
)

# Schémas System
from app.schemas.system import (
    SystemInfo,
    SystemMetrics,
    DatabaseStatus,
    ResourceLimit,
    EnvironmentVariable,
    EnvironmentInfo,
    LogLevelUpdate,
    LogLevelResponse,
    LogEntry,
    LogListResponse,
    SystemHealthCheck,
    SystemOperationResponse,
    CacheClearResponse,
)

# Schémas User
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserStatusUpdate,
    UserRoleUpdate,
    UserLogin,
    UserLoginResponse,
    TokenRefresh,
    TokenResponse,
    PasswordChange,
    PasswordResetRequest,
    PasswordResetConfirm,
    UserResponse,
    UserWithPreferences,
    UserListResponse,
    SessionResponse,
    SessionListResponse,
    UserSearchFilters,
    AdminUserCreate,
    AdminUserUpdate,
)

# ==========================================================================
#  Exports
# ==========================================================================

__all__ = [
    # Job
    "JobBase",
    "JobCreate",
    "JobUpdate",
    "JobResponse",
    "JobListResponse",
    "JobStatusUpdate",
    "JobCancelRequest",
    "JobRetryRequest",
    "JobFilters",

    # Library
    "LibraryMetadata",
    "LibraryItemBase",
    "LibraryItemCreate",
    "LibraryItemUpdate",
    "LibraryItemResponse",
    "LibraryListResponse",
    "LibraryStats",
    "LibrarySearchFilters",
    "LibraryActionResponse",

    # Provider
    "ProviderInfo",
    "ProviderListResponse",
    "ChapterInfo",
    "SeriesInfo",
    "SearchResult",
    "SearchResponse",
    "AnalysisResult",
    "ProviderConfig",
    "ProviderConfigUpdate",
    "ProviderErrorResponse",

    # System
    "SystemInfo",
    "SystemMetrics",
    "DatabaseStatus",
    "ResourceLimit",
    "EnvironmentVariable",
    "EnvironmentInfo",
    "LogLevelUpdate",
    "LogLevelResponse",
    "LogEntry",
    "LogListResponse",
    "SystemHealthCheck",
    "SystemOperationResponse",
    "CacheClearResponse",

    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserStatusUpdate",
    "UserRoleUpdate",
    "UserLogin",
    "UserLoginResponse",
    "TokenRefresh",
    "TokenResponse",
    "PasswordChange",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "UserResponse",
    "UserWithPreferences",
    "UserListResponse",
    "SessionResponse",
    "SessionListResponse",
    "UserSearchFilters",
    "AdminUserCreate",
    "AdminUserUpdate",
]
