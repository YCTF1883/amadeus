import unittest
from unittest.mock import patch

from backend.app.agent import graph
from backend.app.speech import stt


class _FakeConnection:
    def __init__(self):
        self.closed = False

    async def close(self):
        self.closed = True


class _FakeMemory:
    def __init__(self):
        self.conn = _FakeConnection()


class _FakePipe:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class _FakeWorker:
    def __init__(self, running=True, timeout=False):
        self.running = running
        self.timeout = timeout
        self.terminated = False
        self.killed = False
        self.stdin = _FakePipe()
        self.stdout = _FakePipe()

    def poll(self):
        return None if self.running else 0

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        if self.timeout and not self.killed:
            raise stt.subprocess.TimeoutExpired("fake-worker", timeout)
        self.running = False
        return 0

    def kill(self):
        self.killed = True


class AgentShutdownTests(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        graph._agent_instance = None

    async def test_close_releases_sqlite_and_resets_agent_state(self):
        agent = graph.AmadeusAgent.__new__(graph.AmadeusAgent)
        agent.memory = _FakeMemory()
        agent.graph = object()
        connection = agent.memory.conn

        await agent.close()

        self.assertTrue(connection.closed)
        self.assertIsNone(agent.memory)
        self.assertIsNone(agent.graph)

    async def test_close_agent_does_not_create_a_new_singleton(self):
        graph._agent_instance = None

        with patch.object(graph, "AmadeusAgent") as constructor:
            await graph.close_agent()

        constructor.assert_not_called()


class SpeechWorkerShutdownTests(unittest.TestCase):
    def tearDown(self):
        stt._worker = None

    def test_stop_worker_terminates_process_and_closes_pipes(self):
        worker = _FakeWorker()
        stt._worker = worker

        stt.stop_worker()

        self.assertTrue(worker.terminated)
        self.assertTrue(worker.stdin.closed)
        self.assertTrue(worker.stdout.closed)
        self.assertIsNone(stt._worker)

    def test_stop_worker_kills_process_after_timeout(self):
        worker = _FakeWorker(timeout=True)
        stt._worker = worker

        stt.stop_worker(timeout=0.01)

        self.assertTrue(worker.terminated)
        self.assertTrue(worker.killed)
        self.assertIsNone(stt._worker)


if __name__ == "__main__":
    unittest.main()
