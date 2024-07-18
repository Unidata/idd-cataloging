#!/home/ldm/.conda/envs/iddcat/bin/python

import asyncio
import subprocess
import traceback
from datetime import datetime as dt
from sqlalchemy import create_engine, Table, Column, BigInteger, Integer, String, MetaData, DateTime
from sqlalchemy.orm import sessionmaker

NOTIFYME = "/home/ldm/bin/notifyme"
R_HOST = "idd.unidata.ucar.edu"
FEED = "ANY"


async def read_stream(stream):

    # create a SQLAlchemy engine object that connects to your PostgreSQL database
    engine = create_engine('postgresql://username:password@localhost/iddcat')

    metadata = MetaData()
    table_name = 'products'
    table = Table(table_name, metadata,
                  Column('id', BigInteger, primary_key=True, autoincrement=True),
                  Column('product', String),
                  Column('feedtype', String),
                  Column('datasize', Integer),
                  Column('insertion_dt', DateTime),
                  Column('origin', String),
                  Column('relay', String))

    # create the table in the database if it does not exist
    table.create(engine, checkfirst=True)

    Session = sessionmaker(bind=engine)
    session = Session()

    print("Starting...")

    while True:
        line = await stream.readline()
        if not line:
            break
        if "notifyme.c:notifymeprog_6" in line.decode():
            parsed = parse_line(line.decode().rstrip())
            # print(parsed)
            record = table.insert().values(
                product=parsed[0],
                feedtype=parsed[1],
                datasize=parsed[2],
                insertion_dt=parsed[3],
                origin=parsed[4],
                relay=parsed[5]
            )
            session.execute(record)
            session.commit()


async def run_command(command):
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    await read_stream(process.stdout)
    await process.wait()


async def main():
    cmd = f"{NOTIFYME} -v -h {R_HOST} -f {FEED} -O"
    print(cmd)
    await asyncio.gather(
        run_command(cmd)
    )


def parse_line(line):
    bits = line.strip("\n").split(maxsplit=8)
    datasize = bits[4]
    inserted = bits[5]
    insert_dt = dt.strptime(inserted, "%Y%m%d%H%M%S.%f")
    feedtype = bits[6]
    goodstuff = bits[-1]
    product_id, path = goodstuff.rsplit(maxsplit=1)
    node_origin, node_relay = path.split("_v_")
    return(product_id, feedtype, datasize, insert_dt, node_origin, node_relay)


if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except Exception:
            traceback.print_exc()
