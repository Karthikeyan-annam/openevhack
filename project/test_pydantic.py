from pydantic import BaseModel

class Test(BaseModel):
    name: str
    num: int

t = Test(name='test', num=5)
print("Object:", t)
print("Dict:", t.dict())
print("num:", t.dict()['num'])