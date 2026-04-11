from .models import DnsServerRecord


class DnsServerRepository:
    def __init__(self, collection: DnsServerRecord):
        self.collection: DnsServerRecord = collection

    async def find_all(self) -> list[DnsServerRecord]:
        return await self.collection.find().to_list(length=None)

    async def save(self, record: DnsServerRecord) -> None:
        await self.collection.insert_one(record.model_dump())

    async def find_by_id(self, record_id: str) -> DnsServerRecord | None:
        return await self.collection.find_one({"_id": record_id})
