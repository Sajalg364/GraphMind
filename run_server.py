import sys
import os

if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
    sys.path.insert(0, os.getcwd())

    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
