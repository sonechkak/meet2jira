from fastapi import APIRouter, Request

utils_router = APIRouter(
    prefix="/utils",
    responses={404: {"description": "Not found"}},
)

@utils_router.get('/list_endpoints/')
def list_endpoints(request: Request):
    url_list = [
        {'path': route.path, 'name': route.name}
        for route in request.app.routes
    ]
    return url_list
