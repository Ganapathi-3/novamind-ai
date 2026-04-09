
from typing import List
from fastapi import HTTPException, status

ROLE_PERMISSIONS = {
    "admin":    ["public", "engineering", "hr", "finance", "legal", "executive", "general"],
    "hr":       ["public", "hr", "general"],
    "employee": ["public", "engineering", "general"],
    "intern":   ["public"]
}

def get_allowed_departments(role: str) -> List[str]:
    role = role.lower().strip()
    if role not in ROLE_PERMISSIONS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Unknown role: '{role}'")
    return ROLE_PERMISSIONS[role]

def can_access_department(role: str, department: str) -> bool:
    return department.lower() in get_allowed_departments(role)

def build_chroma_filter(role: str) -> dict:
    allowed = get_allowed_departments(role)
    if len(allowed) == 1:
        return {"department": allowed[0]}
    return {"department": {"$in": allowed}}

def get_role_summary() -> dict:
    return ROLE_PERMISSIONS
