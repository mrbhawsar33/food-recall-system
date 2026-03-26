from fastapi import FastAPI

# This creates the "app" object that AWS will run
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World! this is from the Food Recall API"}