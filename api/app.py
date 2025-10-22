from contextlib import asynccontextmanager
from fastapi import FastAPI, Body, Depends
from fastapi.middleware.cors import CORSMiddleware

from api.models import APIResponse, CodeRequest, CodeVerifyRequest, PasswordVerifyRequest
from api.depends import get_telegram_user_id


@asynccontextmanager
async def lifespan(app: FastAPI):
    import dotenv
    dotenv.load_dotenv()
    yield


app = FastAPI(debug=True, lifespan=lifespan)


origins = [
    "*",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.1.2:5173",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
def phones(telegram_user_id: int = Depends(get_telegram_user_id)):
    return []


@app.post('/code-request', response_model=APIResponse)
def code_request(telegram_user_id: int = Depends(get_telegram_user_id), code_request: CodeRequest = Body(...)):
    if code_request.phone_number == '+38099200100':
        return APIResponse(success=True, data={ 'phone_code_hash': 'abcdef123', 'timeout': 6000 })
    return APIResponse(success=False, error='Phone number invalid.')


@app.post('/code-verify', response_model=APIResponse)
def code_verify(telegram_user_id: int = Depends(get_telegram_user_id), code_verify_request: CodeVerifyRequest = Body(...)):
    if code_verify_request.code == '00000' and code_verify_request.phone_code_hash == 'abcdef123':
        return APIResponse(success=True, data={ 'need_password': True })
    return APIResponse(success=False, error='Invalid code.')


@app.post('/password-verify', response_model=APIResponse)
def password_verify(telegram_user_id: int = Depends(get_telegram_user_id), password_verify_request: CodeVerifyRequest = Body(...)):
    if password_verify_request.password == 'oralcumshot':
        return APIResponse(success=True)
    return APIResponse(success=False, error='Invalid password.')
