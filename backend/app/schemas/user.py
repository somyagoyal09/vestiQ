from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfileUpdate(BaseModel):
    age_group: str | None = Field(default=None, max_length=20)
    gender: str | None = Field(default=None, max_length=30)
    clothing_preference: str = Field(default="both", max_length=30)
    preferred_styles: list[str] = Field(default_factory=list)
    preferred_occasions: list[str] = Field(default_factory=list)
    clothing_interests: list[str] = Field(default_factory=list)
    preferred_colors: list[str] = Field(default_factory=list)
    styling_approach: list[str] = Field(default_factory=list)
    preferred_traditional_categories: list[str] = Field(default_factory=list)


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    profile_completed: bool = False
    onboarding_completed: bool = False
    age_group: str | None = None
    gender: str | None = None
    clothing_preference: str = "both"
    preferred_styles: list[str] = Field(default_factory=list)
    preferred_occasions: list[str] = Field(default_factory=list)
    clothing_interests: list[str] = Field(default_factory=list)
    preferred_colors: list[str] = Field(default_factory=list)
    styling_approach: list[str] = Field(default_factory=list)
    preferred_traditional_categories: list[str] = Field(default_factory=list)
