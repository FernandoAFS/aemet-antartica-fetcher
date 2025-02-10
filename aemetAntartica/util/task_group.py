from asyncio import Task, TaskGroup
from collections.abc import Coroutine, Sequence


async def parallel_task[T](*coros: Coroutine[None, None, T]) -> Sequence[T]:
    "Simply run and wait all tasks in parallel"

    tasks: list[Task[T]] = []
    async with TaskGroup() as tg:
        for t in coros:
            task = tg.create_task(t)
            tasks.append(task)

    return [task.result() for task in tasks]
