from thread_pool import ThreadPool
pool = ThreadPool(2)
results = pool.map(lambda x: x**2, range(5))
assert results == [0, 1, 4, 9, 16]
f = pool.submit(lambda: 42)
assert f.result(timeout=2) == 42
pool.shutdown()
print("Thread pool tests passed")