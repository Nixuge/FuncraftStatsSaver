from asyncio import Task
import asyncio
from concurrent.futures import ProcessPoolExecutor
from threading import Thread
import time
from typing import Callable

def sec_to_min_hours(seconds):
    min, sec = divmod(seconds, 60)
    hour, min = divmod(min, 60)
    if hour > 0:
        return '%ds %dm %dh' % (sec, min, hour)
    else:
        return '%ds %dm' % (sec, min)

queue = asyncio.Queue()
p = ProcessPoolExecutor(max_workers=125)
loop = asyncio.get_event_loop()

class ThreadLimiter:
    tasks: list[Thread]
    remaining_elements: list
    done_tasks_count: int
    print_progress_str: str
    polling_sleep: float
    max_task_count: int
    function_for_task: Callable

    def __init__(self,
                 function_to_task, #Function to call
                 print_progress_str: str = "Downloaded/Remaining tasks: {downloaded!s}/{remaining!s}, Running tasks: {running_tasks!s} ({done_tasks!s}/{failed_tasks!s} main, {additional_tasks!s}/{additional_failed_tasks!s} additional, {skipped_tasks!s} skips) {running_time!s}     ",
                 max_task_count: int = 1,
                 polling_sleep: float = .2
                 ) -> None:
        self.done_tasks_count = 0
        self.failed_tasks_count = 0
        self.remaining_elements = []
        self.tasks = []
        self.skipped_tasks = 0
        self.done_tasks = 0
        self.additional_tasks = 0
        self.additional_failed_tasks = 0
        self.print_progress_str = print_progress_str
        self.function_for_task = function_to_task
        self.max_task_count = max_task_count
        self.polling_sleep = polling_sleep
        self.global_lock = False
        self.lock_fail = False
        self.start_time = time.time()


    # To be called & returned when an error occurs
    # eg:
    # try:
    #     ....
    # except:
    #     return fail(elem)
    #
    # Will automatically add back to the remaining list & return false
    # async def fail(self, element):
    #     while self.lock_fail:
    #         await asyncio.sleep(self.polling_sleep)
        
    #     self.lock_fail = True
    #     with open("failed.txt", "a") as failedfile:
    #         failedfile.write(str(element) + "\n")
    #     self.lock_fail = False

    #     self.failed_tasks_count += 1

    #     return False

    def fail_retry(self, element, text):
        while self.lock_fail:
            time.sleep(self.polling_sleep)
        
        self.lock_fail = True
        with open("failed.txt", "a") as failedfile:
            failedfile.write(text + "\n\n")
        self.lock_fail = False

        self.done_tasks_count -= 1
        self.failed_tasks_count += 1
        self.remaining_elements.insert(5, element)

        time.sleep(1)
        return False

    def grab_all(self):
        while True:
            for element in self.remaining_elements:
                if (len(self.tasks) > self.max_task_count):
                    break
                
                self.function_for_task(element)
                self.remaining_elements.remove(element)

            for task in self.tasks:
                if not task.is_alive():
                    self.tasks.remove(task)
                    self.done_tasks_count += 1

            print(self.print_progress_str.format(
                downloaded=self.done_tasks_count,
                remaining=len(self.remaining_elements),
                running_tasks=len(self.tasks),
                failed_tasks=self.failed_tasks_count,
                skipped_tasks=self.skipped_tasks,
                additional_tasks=self.additional_tasks,
                additional_failed_tasks=self.additional_failed_tasks,
                done_tasks=self.done_tasks,
                running_time=sec_to_min_hours(time.time() - self.start_time),
            ), end="\r")

            if len(self.tasks) == 0:
                break

            time.sleep(self.polling_sleep)
        
        print("\n== Done with batch ==")