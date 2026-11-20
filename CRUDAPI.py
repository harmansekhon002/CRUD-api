from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm  # CHANGED
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from fastapi import Query
import os

app = FastAPI()

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

SECRET_KEY = os.environ.get("SECRET_KEY","dev-only-key")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ---------- fake databases ----------
orders = [
    {"id": 1, "item": "Laptop", "price": 55000, "owner_id": 1},
    {"id": 2, "item": "Phone", "price": 20000, "owner_id": 2},
]
users = []


# ---------- models ----------
class OrderIn(BaseModel):
    item: str
    price: int


class UserIn(BaseModel):
    username: str
    password: str


# ---------- token helpers ----------
def create_token(user_id: int):
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def get_current_user_id(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return int(payload["sub"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ---------- auth routes ----------
@app.post("/register", status_code=201)
def register(user: UserIn):
    for u in users:
        if u["username"] == user.username:
            raise HTTPException(status_code=409, detail="Username taken")

    hashed = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
    new_user = {
        "id": len(users) + 1,
        "username": user.username,
        "password_hash": hashed,
    }
    users.append(new_user)
    return {"id": new_user["id"], "username": new_user["username"]}


@app.post("/login")
@limiter.limit("5/minutes")
def login(form: OAuth2PasswordRequestForm = Depends()):  # CHANGED
    for u in users:
        if u["username"] == form.username:  # CHANGED
            if bcrypt.checkpw(form.password.encode(), u["password_hash"]):  # CHANGED
                return {"access_token": create_token(u["id"]), "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid username or password")


# ---------- order routes ----------
@app.get("/")
def hello():
    return {"message": "hello"}


@app.get("/orders")
def list_orders(
    page: int = Query(1,ge=1), limit: int = Query(10,ge=1,le=100), user_id: int = Depends(get_current_user_id)
):
    mine = [o for o in orders if o["owner_id"] == user_id]
    start = (page - 1) * limit
    return mine[start : start + limit]


@app.get("/orders/{order_id}")
def get_order(order_id: int, user_id: int = Depends(get_current_user_id)):
    for order in orders:
        if order["id"] == order_id:
            if order["owner_id"] == user_id:
                return order
            raise HTTPException(status_code=408, detail="this order is not yours")
    raise HTTPException(status_code=404, detail="Order not found")


@app.post("/orders", status_code=201)
def create_order(order: OrderIn, user_id: int = Depends(get_current_user_id)):
    new_id = len(orders) + 1
    new_order = {
        "id": new_id,
        "item": order.item,
        "price": order.price,
        "owner id": user_id,
    }
    orders.append(new_order)
    return new_order


@app.put("/orders/{order_id}")
def update_order(
    order_id: int, order: OrderIn, user_id: int = Depends(get_current_user_id)
):
    for existing in orders:
        if existing["id"] == order_id:
            if existing["owner_id"] != user_id:
                raise HTTPException(status_code=403, detail="Not your order")
            existing["item"] = order.item
            existing["price"] = order.price
            return existing
    raise HTTPException(status_code=404, detail="Order not found")


@app.delete("/orders/{order_id}", status_code=204)
def delete_order(order_id: int, user_id: int = Depends(get_current_user_id)):
    for order in orders:
        if order["id"] == order_id:
            if order["owner_id"] != user_id:
                raise HTTPException(status_code=403, detail="Not your order")
            orders.remove(order)
            return
    raise HTTPException(status_code=404, detail="Order not found")
