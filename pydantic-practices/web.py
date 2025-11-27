from model import Creature
from fastapi import FastAPI

app = FastAPI()

@app.get("/creatures")
def fetch_creatures() -> list[Creature]:
    from data import get_creatures
    return get_creatures()