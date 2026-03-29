#!/usr/bin/env python3
"""Simple thread pool implementation."""
import threading, queue, time

class ThreadPool:
    def __init__(self, num_workers: int = 4):
        self.tasks = queue.Queue()
        self.results = {}
        self._lock = threading.Lock()
        self._task_id = 0
        self.workers = []
        self._stop = False
        for _ in range(num_workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self.workers.append(t)

    def _worker(self):
        while not self._stop:
            try:
                tid, fn, args, kwargs = self.tasks.get(timeout=0.1)
                try:
                    result = fn(*args, **kwargs)
                    with self._lock:
                        self.results[tid] = ("ok", result)
                except Exception as e:
                    with self._lock:
                        self.results[tid] = ("error", e)
                self.tasks.task_done()
            except queue.Empty:
                continue

    def submit(self, fn, *args, **kwargs) -> int:
        with self._lock:
            self._task_id += 1
            tid = self._task_id
        self.tasks.put((tid, fn, args, kwargs))
        return tid

    def get_result(self, tid: int, timeout: float = 5.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                if tid in self.results:
                    return self.results[tid]
            time.sleep(0.01)
        return ("timeout", None)

    def wait_all(self):
        self.tasks.join()

    def shutdown(self):
        self._stop = True
        for t in self.workers:
            t.join(timeout=1)

def test():
    pool = ThreadPool(2)
    ids = []
    for i in range(10):
        tid = pool.submit(lambda x: x * x, i)
        ids.append((tid, i))
    pool.wait_all()
    for tid, i in ids:
        status, val = pool.get_result(tid)
        assert status == "ok" and val == i * i, f"{i}: {status} {val}"
    # Error handling
    tid2 = pool.submit(lambda: 1/0)
    pool.wait_all()
    status2, _ = pool.get_result(tid2)
    assert status2 == "error"
    pool.shutdown()
    print("  thread_pool: ALL TESTS PASSED")

if __name__ == "__main__":
    test()
