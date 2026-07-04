import asyncio
import logging
import platform

import dns.asyncresolver
from beanie.odm.operators.update.general import Set

from dns_models import DnsServerRecord
from beanie import init_beanie


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

IS_WINDOWS = platform.system() == "Windows"
QUEUE_MAX_SIZE=1_000
TRUSTED_DOMAINS = ["google.com", "cloudflare.com", "aws.amazon.com", "facebook.com", "microsoft.com"]
MAX_WORKERS = 10  # Number of concurrent tasks for processing records

def update_reliablity_score(server: DnsServerRecord, no_of_fails:int, no_of_success:int) -> None:
    """Update the reliability score of a DNS server based on the success of a ping."""
    if no_of_success > 0:
        server.reliability = min(server.reliability + (no_of_success * 10), 100)
    if no_of_fails > 0:
        server.reliability = max(server.reliability - (no_of_fails * 20), 0)


records_queue = asyncio.Queue(QUEUE_MAX_SIZE)
db_update_queue = asyncio.Queue()

sem = asyncio.Semaphore(100)  

async def ping(ip: str, timeout: int = 1) -> bool:
    if IS_WINDOWS:
        cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), ip]
    else:
        cmd = ["ping", "-c", "1", "-W", str(timeout), ip]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )

    try:
        return await asyncio.wait_for(proc.wait(), timeout=timeout + 1) == 0
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return False
    except Exception as e:
        logger.error(f"Error pinging {ip}: {e}")
        return False

async def ping_with_semaphore(ip: str) -> tuple[str, bool]:
    async with sem:
        result = await ping(ip)
        return ip, result

async def ping_dns_ips(ips: list[str]) -> dict[str, bool]:
    """
    Ping the given list of IPs and return a dictionary with the results.
    """
    
    results = {}
    ping_tasks = [ping_with_semaphore(ip) for ip in ips]
    for ip, success in await asyncio.gather(*ping_tasks):
        results[ip] = success
    return results


async def trusted_domain_resolved(record: DnsServerRecord, domain:str) -> bool:
    """
    Get DNS records for Google domains using the given DNS server record.
    """
    resolver = dns.asyncresolver.Resolver()
    resolver.nameservers = record.ips
    resolver.lifetime = 5.0
    try:
        await resolver.resolve(domain, "A")
        return True
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        logger.warning(f"No A records found for {domain} using {record.name}")
        return False
    except dns.resolver.LifetimeTimeout:
        logger.warning(f"DNS query timed out for {domain} using {record.name}")
        return False
    except Exception as e:
        logger.error(f"Error querying DNS for {domain} using {record.name}: {e}")
        return False


async def fetch_and_enqueue_records():
    """
    Fetch DNS server records from the database and enqueue them for processing.
    """
    count = 0
    async for record in DnsServerRecord.find(
        DnsServerRecord.active == True, DnsServerRecord.reliability >= 0
    ):
        await records_queue.put(record)
        count += 1

    logger.info(f"Enqueued {count} DNS records for processing")

    for _ in range(MAX_WORKERS):
        await records_queue.put(None)  # Sentinel to signal workers to stop

    logger.debug(f"Sent {MAX_WORKERS} sentinels to stop workers")

async def process_record(record: DnsServerRecord):
    """
    Process a single DNS server record: ping it and update its reliability score.
    """
    # Create both coroutines (not awaited yet — they run concurrently below)
    ping_coro = ping_dns_ips(record.ips)
    dns_coros = [
        trusted_domain_resolved(record, domain) for domain in TRUSTED_DOMAINS
    ]

    # Run ping + all DNS resolution concurrently
    ping_results, *dns_results = await asyncio.gather(ping_coro, *dns_coros)

    no_of_fails = sum(1 for r in dns_results if not r)
    no_of_success = sum(1 for r in dns_results if r)

    update_reliablity_score(record, no_of_fails, no_of_success)
    new_ips = [ip for ip, success in ping_results.items() if success]
    record.ips = new_ips

    logger.debug(
        f"Record {record.identifier}: ping={len(new_ips)}/{len(ping_results)} "
        f"dns_ok={no_of_success}/{len(dns_results)} score={record.reliability}"
    )

    if len(new_ips) == 0:
        record.reliability = 0
        record.active = False  # Mark as inactive if no IPs are reachable
        logger.warning(f"Record {record.identifier} marked inactive: no reachable IPs")

    await db_update_queue.put(record)


async def bulk_update_records(records: list[DnsServerRecord]):
    """
    Bulk update DNS server records in the database.
    """
    if not records:
        return

    logger.debug(f"Bulk updating {len(records)} records")

    try:
        async with DnsServerRecord.bulk_writer(ordered=False) as writer:
            for record in records:
                await DnsServerRecord.find_one(
                    DnsServerRecord.identifier == record.identifier, bulk_writer=writer
                ).update(
                    Set(
                        {
                            "reliability": record.reliability,
                            "ips": record.ips,
                            "last_seen": record.last_seen,
                        }
                    ),
                    upsert=True,
                )
        logger.info(f"Successfully updated {len(records)} records in DB")
    except Exception as e:
        logger.error(f"Error bulk updating records: {e}")

async def reliablity_check_operation():
    worker_id = id(asyncio.current_task())
    logger.debug(f"Worker {worker_id} started")

    count = 0
    while True:
        record = await records_queue.get()
        if record is None:
            records_queue.task_done()
            logger.debug(f"Worker {worker_id} received sentinel, exiting after processing {count} records")
            break

        try:
            await process_record(record)
            count += 1
        except Exception as e:
            logger.error(f"Worker {worker_id} error processing {record.identifier}: {e}")
        finally:
            records_queue.task_done()

async def update_records_in_db():
    """
    Update DNS server records in the database based on the results of the ping and DNS resolution tests.
    """
    logger.debug("DB update task started")

    records = []
    total_flushed = 0

    while True:
        record = await db_update_queue.get()

        # Sentinel: None signals stop
        if record is None:
            if records:  # Flush any remaining batch
                await bulk_update_records(records)
                total_flushed += len(records)
            db_update_queue.task_done()
            logger.info(f"DB update task finished, total records flushed: {total_flushed}")
            break

        records.append(record)
        if len(records) >= 500:
            await bulk_update_records(records)
            total_flushed += len(records)
            logger.debug(f"Flushed batch of {len(records)} records, cumulative: {total_flushed}")
            records.clear()
        db_update_queue.task_done()

async def main():
    """
    Main function to run the ping and update reliability process.
    """
    logger.info("=== DNS Reliability Check Started ===")
    from .utils.db import connect_to_mongo, close_mongo, MONGODB_DB

    client = await connect_to_mongo()
    await init_beanie(database=client[MONGODB_DB], document_models=[DnsServerRecord])

    # Start the database update task
    db_update_task = None
    processing_tasks = []
    try:
        db_update_task = asyncio.create_task(update_records_in_db())
        logger.debug("DB update task created")

        # Start the record processing tasks
        processing_tasks = [asyncio.create_task(reliablity_check_operation()) for _ in range(MAX_WORKERS)]
        logger.info(f"Started {MAX_WORKERS} worker tasks")

        await fetch_and_enqueue_records()

        # Wait for all processing tasks to complete
        logger.debug("Waiting for all workers to finish...")
        await asyncio.gather(*processing_tasks)
        logger.info("All workers completed")

        # Signal database task to stop (sentinel)
        await db_update_queue.put(None)
        logger.debug("Sent stop signal to DB task")

        # Wait for the database update task to finish
        await db_update_task
        logger.info("=== DNS Reliability Check Completed ===")
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        for task in processing_tasks:
            task.cancel()
        if db_update_task:
            db_update_task.cancel()
        logger.debug("Cancelled all worker tasks")
    finally:
        await close_mongo()
        logger.debug("MongoDB connection closed")

if __name__ == "__main__":
    import os

    # Configure logging for dev environment
    log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("beanie").setLevel(logging.INFO)

    asyncio.run(main())
