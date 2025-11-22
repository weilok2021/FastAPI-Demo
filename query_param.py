from fastapi import FastAPI
app = FastAPI()

"""When a query parameter is not required, set it to None by default"""
@app.get("/home/")
async def index(query1: str | None = None, query2: int = "178"):
    if query1 and query2:
        return {"message": "Explore query parameter in FastAPI",
                "name": query1,
                "height": query2,
                }
    else:
        return {"message": "Either query1 or query 2 is empty"}
    

"""When a query parameter is required, just do not declare any default value"""
@app.get("/search/")
async def search(required_q: str):
    return {"message": "Query Parameter is require for this endpoint!",
            "query_require": required_q,
            }