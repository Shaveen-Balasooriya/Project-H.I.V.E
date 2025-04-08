from fastapi import FastAPI
from app.routes.honeypot_routes import router as honeypot_router
import podman

app = FastAPI(
    title="Project H.I.V.E",
    description="Project H.I.V.E's api to connect to the server side."
)

app.include_router(honeypot_router)
@app.get("/")
async def root():
    return {'message': 'Welcome to Project H.I.V.E API!'}

@app.get("/health")
async def health():
    try:
        _url = 'unix:///tmp/podman.sock'
        with podman.PodmanClient(base_url=_url) as _client:
            # Check if the Podman client is reachable
            if _client.ping():
                return {
                    'status': 'ok',
                    'message': 'Podman client is reachable',
                    'version': _client.version()
                }
    except Exception as e:
        print(f'Error during health check: {str(e)}')
        return {
            'status': 'error',
            'message': str(e)
        }
