#!/usr/bin/env python3
"""thread_pool: Simple thread pool executor."""
import threading, queue, sys, time

class ThreadPool:
    def __init__(self, num_workers=4):
        self.tasks = queue.Queue()
        self.results = {}
        self._lock = threading.Lock()
        self._id = 0
        self.workers = []
        self._shutdown = False
        for _ in range(num_workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self.workers.append(t)

    def _worker(self):
        while not self._shutdown:
            try:
                task_id, fn, args, kwargs = self.tasks.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                result = fn(*args, **kwargs)
                with self._lock:
                    self.results[task_id] = ("ok", result)
            except Exception as e:
                with self._lock:
                    self.results[task_id] = ("err", e)
            self.tasks.task_done()

    def submit(self, fn, *args, **kwargs):
        with self._lock:
            self._id += 1
            task_id = self._id
        self.tasks.put((task_id, fn, args, kwargs))
        return task_id

    def get_result(self, task_id, timeout=5):
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                if task_id in self.results:
                    return self.results.pop(task_id)
            time.sleep(0.01)
        raise TimeoutError(f"Task {task_id} not completed")

    def shutdown(self, wait=True):
        if wait:
            self.tasks.join()
        self._shutdown = True

def test():
    pool = ThreadPool(2)
    def square(x): return x * x
    ids = [pool.submit(square, i) for i in range(10)]
    results = []
    for tid in ids:
        status, val = pool.get_result(tid)
        assert status == "ok"
        results.append(val)
    assert results == [i*i for i in range(10)]
    # Error handling
    def fail(): raise ValueError("boom")
    tid = pool.submit(fail)
    status, val = pool.get_result(tid)
    assert status == "err"
    assert "boom" in str(val)
    pool.shutdown()
    print("All tests passed!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test": test()
    else: print("Usage: thread_pool.py test")
