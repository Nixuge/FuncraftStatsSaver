from sqlite3 import Connection, Cursor
import sqlite3
from threading import Thread
from time import sleep

class DbQueue(Thread):
    # should be thread safe as lists are thread safe
    #TODO: use queue (https://www.geeksforgeeks.org/queue-in-python/ ?)
    instructions: list[tuple[str, list | tuple | None]] #0 = query, 1 = data
    important_instructions: list[str]
    connection: Connection
    cursor: Cursor
    should_stop: bool = False

    def __init__(self, db_file: str) -> None:
        super().__init__(None, None, "DbQueueThread") #see thread init (unneeded basically)
        self.instructions = []
        self.important_instructions = []
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
    
    def add_important_instruction(self, full_query: str):
        self.important_instructions.append(full_query)
        if "~" in full_query:
            print(full_query)

    def add_instuction(self, query: str, data: list | tuple | None):
        self.instructions.append((query, data))

    # Note for both _process_important_instructions() & _process_normal_instruction():
    # "for" loops seem to skip some instructions 
    # (for some reason? See the git blame for how it was done before)
    # So switched over to "while"s
    def _process_important_instructions(self) -> None:
        while len(self.important_instructions) > 0:
            self.cursor.execute(self.important_instructions.pop(0))
            
        self.connection.commit()
        # self.connection.serialize()

    def _process_normal_instruction(self) -> None:
        # count = 0
        try:
            while len(self.instructions) > 0:
                instruction = self.instructions.pop(0)
                # count += 1
                if instruction[1] != None: # if data present
                    self.cursor.execute(instruction[0], instruction[1])
                else:
                    self.cursor.execute(instruction[0])
        except sqlite3.IntegrityError as e:
            # if not "UNIQUE contraint failed: " in str(e):
            print(f"INTEGRITYERROR HAPPENED: {e}")
                    
        # print(f"Added {count} values")

        self.connection.commit()
        # self.connection.serialize()


    def run(self) -> None:
        while True:
            if self.should_stop:
                break

            sleep(.2)

            # perform create table queries BEFORE insert queries
            if len(self.important_instructions) > 0:
                self._process_important_instructions()
            
            # then perform normal (insert) queries
            if len(self.instructions) > 0:
                self._process_normal_instruction()
