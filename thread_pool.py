#!/usr/bin/env python3
"""Thread pool executor. Zero dependencies."""
import threading, queue, sys, time

class ThreadPool:
    def __init__(self, num_workers=4):
        self.tasks = queue.Queue()
        self.results = {}
        self._lock = threading.Lock()
        self._counter = 0
        self.workers = []
        for _ in range(num_workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self.workers.append(t)

    def _worker(self):
        while True:
            task_id, fn, args, kwargs = self.tasks.get()
            if fn is None: break
            try:
                result = fn(*args, **kwargs)
                with self._lock:
                    self.results[task_id] = ("ok", result)
            except Exception as e:
                with self._lock:
                    self.results[task_id] = ("error", e)
            self.tasks.task_done()

    def submit(self, fn, *args, **kwargs):
        with self._lock:
            self._counter += 1
            task_id = self._counter
        self.tasks.put((task_id, fn, args, kwargs))
        return Future(self, task_id)

    def map(self, fn, iterable):
        futures = [self.submit(fn, item) for item in iterable]
        return [f.result() for f in futures]

    def shutdown(self, wait=True):
        for _ in self.workers:
            self.tasks.put((None, None, None, None))
        if wait:
            for t in self.workers: t.join()

class Future:
    def __init__(self, pool, task_id):
        self._pool = pool
        self._id = task_id

    def result(self, timeout=None):
        start = time.time()
        while True:
            with self._pool._lock:
                if self._id in self._pool.results:
                    status, val = self._pool.results.pop(self._id)
                    if status == "error": raise val
                    return val
            if timeout and time.time() - start > timeout:
                raise TimeoutError()
            time.sleep(0.001)

    def done(self):
        with self._pool._lock:
            return self._id in self._pool.results

if __name__ == "__main__":
    pool = ThreadPool(4)
    results = pool.map(lambda x: x*x, range(10))
    print(f"Squares: {results}")
    pool.shutdown()
