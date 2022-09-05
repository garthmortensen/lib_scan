# -*- coding: utf-8 -*-
"""
Created on Sun Aug 14 12:19:33 2022

@author: garth
"""


from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy import inspect
from sqlalchemy import Table, Column, Integer, String, DateTime
from sqlalchemy import select, insert, update, delete
from sqlalchemy import func  # executes on db hardware
import numpy  # for testing
import pandas  # for testing
import tensorflow  # for testing
import keras  # for testing
import libssh2  # conda only
import zope  # conda only
import fastjsonschema  # pip only
import msgpack  # pip only


def setup_db(in_memory: bool=True):
    """CREATE DATABASE function.
        Input: Set boolean to determine if db should be in_memory (default),
        or sqlite.
        Output: engine, metadata
    """

    if in_memory:
        engine = create_engine('sqlite:///:memory:')  # better for git, dev
    else:
        engine = create_engine('sqlite:///db.sqlite')  # approach 1 //// for abs path
    
    # Create a metadata object
    metadata = MetaData()

    return engine, metadata


def setup_tables(engine, metadata):
    """CREATE TABLE function.
        Input: Provide engine and metadata
        Output: Returns engine, metadata and table
    """

    rolls_t = Table('rolls_t', metadata,
                   # pk autoincrement so you can skip assigning pk value in insert
                   Column('id', 
                          Integer(), 
                          primary_key=True, 
                          autoincrement=True),
                   Column('timestamp_created', 
                          DateTime(timezone=True),
                          # leave timestamp to db to calc, else latency issues
                          server_default=func.now(),
                          # anytime row updates, inserts new timestamp
                          onupdate=func.now()
                          ),
                   Column('reason', 
                          String(60),
                          nullable=False),
                   Column('sides', 
                          Integer(), 
                          nullable=True),
                   Column('roll_value', 
                          Integer(), 
                          nullable=False),
                   )

    chars_t = Table('chars_t', metadata,
                   # pk autoincrement so you can skip assigning pk value in insert
                   Column('id',
                          Integer(), 
                          primary_key=True, 
                          autoincrement=True),
                   Column('timestamp_created', 
                          DateTime(timezone=True),
                          server_default=func.now(),
                          onupdate=func.now()
                          ),
                   Column('char_name', 
                          String(60),
                          nullable=True),
                   Column('char_race', 
                          String(60),
                          nullable=True),
                   Column('char_class', 
                          String(60),
                          nullable=True),
                   Column('char_alignment', 
                          String(60),
                          nullable=True),
                   Column('strength', 
                          Integer(), 
                          nullable=True),
                   Column('dexterity', 
                          Integer(), 
                          nullable=True),
                   Column('constitution', 
                          Integer(), 
                          nullable=True),
                   Column('intelligence', 
                          Integer(), 
                          nullable=True),
                   Column('wisdom', 
                          Integer(), 
                          nullable=True),
                   Column('charisma', 
                          Integer(), 
                          nullable=True),
                   )

    # Create the table in the database
    metadata.create_all(engine)  # method 1
    # rolls_t.create(engine)  # method 2
    
    insp = inspect(engine)
    print(insp.get_table_names())

    return engine, metadata, rolls_t, chars_t


def insert_rows(engine, tablename, data):
    """INSERT INTO function. 
        Input: engine, tablename, data
        Output: None
    """

    insert_statement = insert(tablename)
    engine.execute(insert_statement, data)


def update_rows(engine, tablename, data):
    """UPDATE function. 
        Input: engine, tablename
        Output: None
    """
    
    roll_value = '99'
    data = roll_value
    update_statement = update(tablename).values(data)
    update_statement = update_statement.where(tablename.columns.id == 1)
    engine.execute(update_statement)


def select_rows(engine, tablename):
    """SELECT function. 
        Input: engine, tablename
        Output: None
    """

    select_statement = select([tablename])
    results = engine.execute(select_statement).fetchmany(size=100)
    print(select_statement)
    print(results)


def count_rows(engine, tablename) -> int:
    """SELECT count(*) function.
        Input: engine, tablename
        Output: row_count int
    """

    count_statement = func.count(tablename.columns.id)
    row_count = engine.execute(count_statement).scalar()
    print(row_count)

    return row_count


def delete_rows_all(engine, tablename):
    """DELETE FROM function.
        Input: engine, tablename
        Output: None
    """

    delete_statement = delete(tablename)
    print(delete_statement)
    # results = engine.execute(delete_statement)
    print(engine.execute(select([tablename])).fetchall())



# engine, metadata = setup_db()

# engine, metadata, rolls_t, chars_t = setup_tables(engine, metadata)

# insert_rows(engine, rolls_t, data)

# update_rows(engine, rolls_t)

# select_rows(engine, rolls_t)

# row_count = count_rows(engine, rolls_t)

# delete_rows_all(engine, rolls_t)




    
