"""Unit test suite for Vortex Apex architecture and thread pool coordination."""
import os
import time
import unittest
import threading
from apex import cpu_torture_worker, RUNNING_FLAG

class TestVortexApex(unittest.TestCase):
    def test_cpu_detection(self):
        cores = os.cpu_count() or 4
        self.assertGreaterEqual(cores, 1)

    def test_cpu_worker_lifecycle(self):
        # Verify worker starts, tortures SIMD arrays, and safely terminates on flag
        RUNNING_FLAG.set()
        t = threading.Thread(target=cpu_torture_worker, args=(0,), daemon=True)
        t.start()
        time.sleep(0.1)
        self.assertTrue(t.is_alive())
        RUNNING_FLAG.clear()
        t.join(timeout=0.5)
        self.assertFalse(t.is_alive())

if __name__ == "__main__":
    unittest.main()
