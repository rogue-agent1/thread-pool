#!/usr/bin/env python3
"""thread_pool - Fixed-size thread pool with future-based results."""
import sys, threading, queue

class Future:
    def __init__(self):
        self._event = threading.Event()
        self._result = None
        self._error = None
    def set_result(self, val):
        self._result = val
        self._event.set()
    def set_error(self, err):
        self._error = err
        self._event.set()
    def result(self, timeout=None):
        self._event.wait(timeout)
        if self._error: raise self._error
        return self._result

class ThreadPool:
    def __init__(self, size=4):
        self._q = queue.Queue()
        self._workers = []
        for _ in range(size):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self._workers.append(t)
    def _worker(self):
        while True:
            item = self._q.get()
            if item is None: break
            func, args, kwargs, fut = item
            try: fut.set_result(func(*args, **kwargs))
            except Exception as e: fut.set_error(e)
    def submit(self, func, *args, **kwargs):
        fut = Future()
        self._q.put((func, args, kwargs, fut))
        return fut
    def shutdown(self):
        for _ in self._workers: self._q.put(None)
        for t in self._workers: t.join()

def test():
    pool = ThreadPool(2)
    futs = [pool.submit(lambda x: x*x, i) for i in range(10)]
    results = [f.result(timeout=5) for f in futs]
    assert results == [i*i for i in range(10)]
    f = pool.submit(lambda: (_ for _ in ()).throw(ValueError("boom")))
    try: f.result(timeout=5); assert False
    except ValueError: pass
    pool.shutdown()
    print("thread_pool: all tests passed")

if __name__ == "__main__":
    test() if "--test" in sys.argv else print("Usage: thread_pool.py --test")
