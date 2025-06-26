from concurrent.futures import ThreadPoolExecutor

# Shared executor for all CPU-bound tasks
executor = ThreadPoolExecutor(max_workers=4)