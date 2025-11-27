from fastapi import FastAPI

app = FastAPI()

# pass new parameter in http request, there are 4 ways.
# First way: parameter path
# @app.get("/hello/{name}")
# def greet(name):
#     return f"Hello {name}"

# pass new parameter in http request, there are 4 ways.
# Second way: query parameter
@app.get("/hello")
def greet(name):
    return f"Hello {name}"