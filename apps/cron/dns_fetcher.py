import httpx


async def get_dns_servers_csv() -> str:
    """Fetch the list of DNS servers from public API and return as CSV string."""
    URL = "https://public-dns.info/nameservers.csv"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(URL, timeout=10)
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as e:
        print(f"Failed to fetch DNS servers: {e}")
        raise RuntimeError("Could not fetch DNS servers") from e


async def parse_csv_to_dicts(csv_data: str) -> list[dict]:
    """Parse CSV string into a list of dictionaries."""
    lines = csv_data.strip().splitlines()
    headers = lines[0].split(",")
    return [dict(zip(headers, line.split(","))) for line in lines[1:]]


async def main():
    csv_data = await get_dns_servers_csv()
    dns_servers = await parse_csv_to_dicts(csv_data)
    print(
        f"Fetched {len(dns_servers)} DNS servers"
    )
    # Here you would typically save the dns_servers to your database


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
