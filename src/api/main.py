from fastapi import FastAPI

app = FastAPI(title='Gaming Analytics Platform API')

@app.get('/')
def health_check():
    return {'status': 'ok'}
