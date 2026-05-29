from typing import Literal

from .models import DnsServerRecord


class DnsServerRepository:
    def __init__(self, collection: DnsServerRecord):
        self.collection: DnsServerRecord = collection

    async def find_all(
        self,
        limit: int | None = None,
        offset: int | None = None,
        order_by: Literal["reputation", "reliability", "location"] | None = None,
        order_desc: bool = True,
    ) -> list[DnsServerRecord]:
        query = self.collection.find()
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.skip(offset)
        if order_by is not None:
            query = query.sort((order_by, -1 if order_desc else 1))
        return await query.to_list(length=None)

    async def save(self, record: DnsServerRecord) -> None:
        await self.collection.insert_one(record.model_dump())

    async def find_by_id(self, record_id: str) -> DnsServerRecord | None:
        return await self.collection.find_one({"_id": record_id})

    async def find_nearby(
        self,
        lat: float,
        lon: float,
        radius_km: int,
        order_by_reputation: bool = False,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[DnsServerRecord]:
        """
        Find DNS servers within a specified radius (in kilometers) of a given latitude and longitude.

        Args:
            lat (float): Latitude of the center point.
            lon (float): Longitude of the center point.
            radius_km (int): Radius in kilometers to search for nearby DNS servers.
            order_by_reputation (bool): Whether to order results by reputation (descending).
            limit (int | None): Maximum number of records to return.
            offset (int | None): Number of records to skip for pagination.
        Returns:
            list[DnsServerRecord]: A list of DNS server records that are within the specified radius.
        """
        try:
            # Convert radius from kilometers to meters for MongoDB geospatial query
            radius_meters = radius_km * 1000

            # Perform geospatial query using MongoDB's $near operator
            nearby_servers = await self.collection.find(
                {
                    "location": {
                        "$near": {
                            "$geometry": {
                                "type": "Point",
                                "coordinates": [lon, lat],
                            },
                            "$maxDistance": radius_meters,
                        }
                    }
                }
            ).to_list(length=None)

            if order_by_reputation:
                nearby_servers.sort(key=lambda x: x.reliability or 0, reverse=True)

            # Apply limit and offset for pagination
            if limit is not None:
                nearby_servers = nearby_servers[:limit]
            if offset is not None:
                nearby_servers = nearby_servers[offset:]

            return nearby_servers
        except Exception as e:
            print(f"Error occurred while finding nearby DNS servers: {e}")
            return []
