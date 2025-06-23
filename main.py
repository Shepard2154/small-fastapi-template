from fastapi import FastAPI, HTTPException
from fast_depends import inject, Depends as FastDepends
from pydantic import BaseModel
from typing import List, Optional, Any


class Item(BaseModel):
    id: int
    name: str


class ItemRepository:
    def __init__(self):
        self._items = [
            Item(id=1, name="First Item"),
            Item(id=2, name="Second Item")
        ]
    
    def get_all_items(self) -> List[Item]:
        return self._items
    
    def get_item_by_id(self, item_id: int) -> Optional[Item]:
        return next((item for item in self._items if item.id == item_id), None)


class ItemService:
    def __init__(self, repository: ItemRepository):
        self._repo = repository
    
    def get_items(self) -> List[Item]:
        return self._repo.get_all_items()
    
    def get_item(self, item_id: int) -> Item:
        item = self._repo.get_item_by_id(item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return item

def get_item_repository() -> ItemRepository:
    return ItemRepository()

@inject
def get_item_service(
    repo: ItemRepository = FastDepends(get_item_repository)
) -> ItemService:
    return ItemService(repo)


class MessageProcessor:
    @inject
    def __init__(self, item_service: ItemService = FastDepends(get_item_service)):
        self.item_service = item_service

    def process_with_items(self, message: str) -> str:
        items = self.item_service.get_items()
        item_names = ", ".join([item.name for item in items])
        return f"{message}. Available items: {item_names}"


app = FastAPI()

@app.get("/items", response_model=list[Item])
async def get_items() -> Any:
    service = get_item_service()
    return service.get_items()

@app.get("/items/{item_id}", response_model=Item)
async def get_item(
    item_id: int,
):
    service = get_item_service()
    return service.get_item(item_id)

@app.get("/process-message")
async def process_message(
    message: str = "Hello",
) -> dict:
    processor = MessageProcessor()
    return {"msg": processor.process_with_items(message)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)