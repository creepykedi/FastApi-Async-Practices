import os
from fastapi import APIRouter, BackgroundTasks
import asyncio
import time
from fastapi import File, UploadFile
import aiofiles
import httpx

read_router = APIRouter()
url_list = ['https://reddit.com', 'https://google.com', 'https://ru.wikipedia.org/',
            'https://www.youtube.com/', 'https://www.facebook.com/', 'https://www.instagram.com/',
            'https://www.twitch.tv/', 'https://www.yahoo.com/', 'https://www.amazon.com/']


async def run_in_process(fn, *args):
    """Run a function in a separate process"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, fn, *args)


#   CPU calculations
async def calculate_data_for_file(file) -> int:
    """A blocking CPU-bound function"""
    print('calculating with async')
    name = file.filename
    name_len = len(name)
    time.sleep(8)
    return name_len


def calculate_data_for_file_sync(file) -> int:
    print('calculating in sync')
    name = file.filename
    name_len = len(name)
    time.sleep(6)
    return name_len


#   Requests
async def send_request_through_httpx() -> float:
    """Non-blocking IO-bound function - sending network requests"""
    st = time.time()
    #await asyncio.sleep(5)
    async with httpx.AsyncClient() as client:
        tasks = []
        for url in url_list:
            tasks.append(client.get(url))
        responses = await asyncio.gather(*tasks)
        for r in responses:
            print(r.status_code)

    fin = time.time() - st
    return fin


async def send_request_through_requests_sync() -> float:
    """Blocking IO-bound function - sending network requests"""
    st = time.time()
    for url in url_list:
        r = httpx.get(url)  # same as requests.get(url)
        print(r.status_code)
    fin = time.time() - st
    return fin


#   File reading
def read_file_data_sync(file: UploadFile = File(...)) -> str:
    """Blocking IO-bound function - reading file"""
    print('reading file in sync')
    os.chdir('D:\\')
    with open(file.filename, 'r'):
        file.read()
        return 'done'


async def read_file_data(file: UploadFile = File(...)) -> str:
    """Non-blocking IO-bound function - reading file"""
    print('reading file async')
   # await asyncio.sleep(1)
    os.chdir('D:\\')
    async with aiofiles.open(file.filename, mode='r'):
        await file.read()
        return 'done'


@read_router.post("/read_file+process_block", tags=['Read files'],
                  description='Reads a file async '
                              'and runs CPU-bound task',
                  status_code=200)
# will block main thread
async def read_file_and_calculate(file: UploadFile = File(...)):
    st = time.time()
    contents, calc = await asyncio.gather(read_file_data(file),
                                          calculate_data_for_file(file))
    time_taken = time.time() - st
    return {'filename': file.filename, 'contents': contents,
            'calculation': calc, 'took': time_taken}


@read_router.post("/read_file+process_block_sync", tags=['Read files'],
                  description='Reads a file async then sync cpu-bound task',
                  status_code=200)
# will block main thread as well
def read_file_and_calculate_sync(file: UploadFile = File(...)):
    st = time.time()
    contents = read_file_data_sync(file)
    calc = calculate_data_for_file_sync(file)
    time_taken = time.time() - st
    return {'filename': file.filename, 'contents': contents,
            'calculation': calc, 'took': time_taken}


@read_router.post("/read_file+process_in_background", tags=['Read files'],
                  description='Reads a file async'
                              'then run cpu-bound task in background',
                  status_code=200)
# will not block main thread, won't return cpu calculation, but will return immediately after file read
async def read_file_and_calculate_sync(background_tasks: BackgroundTasks,
                                       file: UploadFile = File(...)):
    st = time.time()
    contents = await read_file_data(file)
    background_tasks.add_task(calculate_data_for_file_sync, file)
    time_taken = time.time() - st
    return {'filename': file.filename, 'contents': contents,
            'took': time_taken}


@read_router.post("/read_file+separate_process", tags=['Read files'],
                  description='Reads a file async '
                              'then run cpu-bound task in a separate process',
                  status_code=200)
async def read_file_and_calculate_sync(file: UploadFile = File(...)):
    # won't block main thread, will return after calculation is done
    st = time.time()
    tasks = [read_file_data(file), run_in_process(calculate_data_for_file_sync, file)]
    contents = await asyncio.gather(*tasks)
    time_taken = time.time() - st
    return {'filename': file.filename, 'contents': contents,
            'took': time_taken}


@read_router.post("/read_file+requests_no_block", tags=['Read files'],
                  description='Reads a file async and sends '
                              'non-blocking request',
                  status_code=200)
# will not block main thread - all async
async def read_file_and_send_requests_httpx(file: UploadFile = File(...)):
    st = time.time()
    contents, requests = await asyncio.gather(read_file_data(file),
                                              send_request_through_httpx())
    time_taken = time.time() - st
    return {'filename': file.filename, 'contents': contents,
            'requests': requests, 'took': time_taken}


@read_router.post("/read_file+requests_sync", tags=['Read files'],
                  description='Reads a file async and uses '
                              'regular sync library to request data',)
# will block main thread bc of sync requests
async def read_file_and_send_requests_httpx_sync(file: UploadFile = File(...)):
    st = time.time()
    contents, requests = await asyncio.gather(read_file_data(file),
                                              send_request_through_requests_sync())
    time_taken = time.time() - st
    return {'filename': file.filename, 'contents': contents,
            'requests': requests, 'took': time_taken}


@read_router.post("/read_file_sync", tags=['Read files'],
                  description='Reads a file sync and calculates data',
                  status_code=200)
# goes to thread
def read_file_sync(file: UploadFile = File(...)):
    start = time.time()
    contents = read_file_data_sync(file)
    #contents = await read_file_data(file)
    #calc = calculate_data_for_file_sync(file)
    time_taken = time.time() - start
    return {'filename': file.filename, 'contents': contents,
            'calculation': 1, 'took': time_taken}


@read_router.post("/read_file_pseudo_async", tags=['Read files'],
                  status_code=200)
# ?
async def read_file_pseudo_async(file: UploadFile = File(...)):
    start = time.time()
    contents = read_file_data_sync(file)
    #contents = await read_file_data(file)
    time_taken = time.time() - start
    return {'filename': file.filename, 'contents': contents,
            'calculation': 1, 'took': time_taken}