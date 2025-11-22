""" 
Explored the concept of request annotation, type annotation, and type union.
Also Enum can be used if we want path parameters to be predefined.
"""

from fastapi import FastAPI
from enum import Enum

class SpecialID(int, Enum):
    num1 = 1
    num2 = 2
    num3 = 3

app = FastAPI()


@app.get("/users/me")
async def read_user_me():
    return {"user_id": "the current user"}


@app.get("/users/{user_id}")
async def root(user_id: SpecialID | int):
    if user_id in [SpecialID.num1, SpecialID.num2, SpecialID.num3]:
        return {"message": "You Special!",
                "user_id": user_id,
                }
    else:
        return {"message": "You are not Special!",
        "user_id": user_id,
        }