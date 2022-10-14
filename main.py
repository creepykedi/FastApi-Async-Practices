import fastapi
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import endpoints

app = fastapi.FastAPI()
app.include_router(endpoints.read_router)
#cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def greet():
    return 'Hello async world'


if __name__ == '__main__':
    uvicorn.run('main:app', host="localhost", port=8001, reload=True)
