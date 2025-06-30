import logging
from typing import Any, Optional

from fast_depends import Depends as FastDepends
from fast_depends import inject
from fastapi import FastAPI, HTTPException
from opentelemetry import _logs
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from pydantic import BaseModel

resource = Resource.create(attributes={
    "service.name": "small-fastapi-template",
    "environment": "dev"
})

logger_provider = LoggerProvider(resource=resource)
_logs.set_logger_provider(logger_provider)

otlp_exporter = OTLPLogExporter(
    endpoint="http://localhost:4317",
    insecure=True
)

logger_provider.add_log_record_processor(
    BatchLogRecordProcessor(otlp_exporter)
)

handler = LoggingHandler(logger_provider=logger_provider)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

app = FastAPI()

class Item(BaseModel):
    id: int
    name: str


class ItemRepository:
    def __init__(self):
        self._items = [
            Item(id=1, name="First Item"),
            Item(id=2, name="Second Item")
        ]
    
    def get_all_items(self) -> list[Item]:
        return self._items
    
    def get_item_by_id(self, item_id: int) -> Optional[Item]:
        return next((item for item in self._items if item.id == item_id), None)


class ItemService:
    def __init__(self, repository: ItemRepository):
        self._repo = repository
    
    def get_items(self) -> list[Item]:
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


@app.get("/items", response_model=list[Item])
async def get_items() -> Any:
    logger.debug("items receiving...")
    service = get_item_service()
    logger.info("items received")
    return service.get_items()

@app.get("/items/{item_id}", response_model=Item)
async def get_item(
    item_id: int,
):
    logger.debug("item %s receiving...", item_id)
    service = get_item_service()
    logger.info("item received")
    return service.get_item(item_id)

@app.get("/process-message")
async def process_message(
    message: str = "Hello",
) -> dict:
    logger.debug("Start processing...")
    processor = MessageProcessor()
    logger.info("Processed")
    return {"msg": processor.process_with_items(message)}


def timestamp_log_config(uvicorn_log_config):
    datefmt = '%Y-%m-%d %H:%M:%S'
    if 'formatters' in uvicorn_log_config:
        uvicorn_log_config['formatters']['default']['fmt'] = '%(levelprefix)s [%(asctime)s] %(message)s'
        uvicorn_log_config['formatters']['default']['datefmt'] = datefmt
    return uvicorn_log_config

if __name__ == "__main__":
    import uvicorn
    from uvicorn.config import LOGGING_CONFIG
    config = timestamp_log_config(LOGGING_CONFIG.copy())
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=config)