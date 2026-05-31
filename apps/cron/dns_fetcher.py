import sys
import pathlib
from dns_models import DnsServerRecord, GeoPoint
from datetime import datetime, timezone
from beanie.odm.operators.update.general import Set

import httpx

# If `apps` isn't importable (running from the `apps/cron` dir), add the
# repository root to `sys.path` so absolute imports like `apps.cron...` work.
try:
    import apps  # type: ignore
except Exception:
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))


async def get_dns_servers_csv() -> str:
    """Fetch the list of DNS servers from public API and return as CSV string."""
    URL = "https://public-dns.info/nameservers.csv"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(URL, timeout=60)
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as e:
        print(f"Failed to fetch DNS servers: {e}")
        raise RuntimeError("Could not fetch DNS servers") from e


async def parse_csv_to_dicts(csv_data: str) -> list[dict]:
    """Parse CSV string into a list of dictionaries.

        Returns a list of dicts where each dict represents a DNS server with keys
    matching the CSV headers.
        E.g.
            [
                {'ip_address': '2001:4860:4860::8888',
                'name': 'dns.google.',
                'as_number': '15169',
                'as_org': 'GOOGLE',
                'country_code': 'US',
                'city': '',
                'version': '',
                'error': '',
                'dnssec': 'true',
                'reliability': '1.00',
                'checked_at': '2023-08-17T22:01:10Z',
                'created_at': '2023-04-26T22:18:09Z'
                }, ....
            ]
    """

    lines = csv_data.strip().splitlines()
    headers = lines[0].split(",")
    return [dict(zip(headers, line.split(","))) for line in lines[1:]]


def safe_float(value: str) -> float:
    """Convert a string to float, returning 0 if conversion fails."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0


def is_datetime(s: str) -> bool:
    try:
        datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        return True
    except ValueError:
        return False


async def parse_to_db_model(
    server_list: list[dict], identifier: str
) -> DnsServerRecord | None:
    try:

        first_record = server_list[0]
        all_ips = list(
            {
                entry.get("ip_address")
                for entry in server_list
                if entry.get("ip_address")
            }
        )
        record = DnsServerRecord(
            name=first_record.get("name", "") or "",
            ips=all_ips,
            country=first_record.get("country_code") or None,
            city=first_record.get("city") or None,
            as_number=int(first_record.get("as_number") or 0),
            identifier=identifier,
            organization=first_record.get("as_org") or "",
            reliability=(
                safe_float(first_record.get("reliability")) * 100
                if first_record.get("reliability")
                else 0
            ),
            dnssec=(first_record.get("dnssec", "false").lower() == "true"),
            last_seen=(
                first_record.get("checked_at")
                if is_datetime(first_record.get("checked_at", ""))
                else datetime.now(timezone.utc)
            ),
        )

        return record
    except Exception as e:
        print(f"Error saving record {identifier}, {server_list}: {e}")


def build_batches(items, batch_size: int):
    """Yield batches of `batch_size` from any iterable `items`.

    This streams batches instead of building a full list in memory.
    """
    batch = []
    for item in items:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


async def _process_batch(batch):
    model_pairs: list[tuple[str, DnsServerRecord]] = []
    for identifier, server_list in batch:
        model = await parse_to_db_model(server_list, identifier)
        if model:
            model_pairs.append((identifier, model))
    if not model_pairs:
        return
    print(f"Processing batch of {len(model_pairs)} records", model_pairs[0][1])
    async with DnsServerRecord.bulk_writer(ordered=False) as writer:
        for identifier, model in model_pairs:
            await DnsServerRecord.find_one(
                DnsServerRecord.identifier == identifier, bulk_writer=writer
            ).upsert(
                Set(
                    {
                        **model.model_dump(
                            exclude={"id", "created_at"}, exclude_none=True
                        ),
                        "last_seen": datetime.now(timezone.utc),
                    }
                ),
                on_insert=model,
            )


async def save_to_mongodb(dns_servers: dict[str, list[dict]]) -> None:
    """Save the list of DNS servers to MongoDB using Beanie."""

    from beanie import init_beanie
    from apps.cron.utils.db import connect_to_mongo, close_mongo, MONGODB_DB

    client = await connect_to_mongo()
    await init_beanie(database=client[MONGODB_DB], document_models=[DnsServerRecord])

    batch_size = 2000
    # Stream batches from the dict items iterator so we don't allocate a large list
    batches = build_batches(dns_servers.items(), batch_size)
    for batch in batches:
        await _process_batch(batch)

    # For all records that were not last seen today, set active=False
    today = datetime.now(timezone.utc).date()
    await DnsServerRecord.update_many(
        DnsServerRecord.last_seen
        < datetime(today.year, today.month, today.day, tzinfo=timezone.utc),
        Set({"active": False}),
    )

    await close_mongo()


async def update_location():
    """Update location for all DNS servers that are missing it."""
    from beanie import init_beanie
    from apps.cron.utils.db import connect_to_mongo, close_mongo, MONGODB_DB
    from helper.location_helper import get_lat_long_from_city_country

    client = await connect_to_mongo()
    await init_beanie(database=client[MONGODB_DB], document_models=[DnsServerRecord])

    # Find all records missing location
    pairs = await DnsServerRecord.aggregate(
        [
            {
                "$group": {
                    "_id": {
                        "city": "$city",
                        "country": "$country",
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "city": "$_id.city",
                    "country": "$_id.country",
                }
            },
        ]
    ).to_list()
    print(
        f"Found {len(pairs)} unique city-country pairs to update location for",
        pairs[:5],
    )
    for pair in pairs:
        city = pair.get("city")
        country = pair.get("country")
        if not city and not country:
            continue
        location = await get_lat_long_from_city_country(city, country)
        if location:
            print(f"Updating location for {city}, {country} to {location}")
            geo_point = GeoPoint(coordinates=[location[1], location[0]])
            await DnsServerRecord.find(
                DnsServerRecord.city == city,
                DnsServerRecord.country == country,
            ).update(Set({"location": geo_point}))
    await close_mongo()


async def main():
    # csv_data = await get_dns_servers_csv()
    # dns_servers = await parse_csv_to_dicts(csv_data)

    # print(f"Fetched {len(dns_servers)} DNS servers", dns_servers[:0])
    # dns_map: dict[str, list[dict]] = {}
    # for server in dns_servers:
    #     asn = server.get("as_number")
    #     name = server.get("name")
    #     as_org = server.get("as_org")
    #     key = f"{asn} {name} {as_org}"
    #     if key in dns_map:
    #         dns_map[key].append(server)
    #     else:
    #         dns_map[key] = [server]

    # await save_to_mongodb(dns_map)

    # print(f"Parsed {len(dns_map)} DNS servers into map", list(dns_map.items())[:5])
    await update_location()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
