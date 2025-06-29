import asyncio
import logging
import time
import uuid
import inspect

from app.services.grammar import GrammarCorrector
from app.services.paraphrase import Paraphraser
from app.services.translation import Translator
from app.services.tone_classification import ToneClassifier
from app.services.inclusive_language import InclusiveLanguageChecker
from app.services.voice_detection import VoiceDetector
from app.services.readability import ReadabilityScorer
from app.services.synonyms import SynonymSuggester
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if getattr(settings, "DEBUG", False) else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Initialize service instances
grammar = GrammarCorrector()
paraphraser = Paraphraser()
translator = Translator()
tone = ToneClassifier()
inclusive = InclusiveLanguageChecker()
voice_analyzer = VoiceDetector()
readability = ReadabilityScorer()
synonyms = SynonymSuggester()

# Create async task queue (optional: maxsize=100 to prevent overload)
task_queue = asyncio.Queue(maxsize=100)

# Task handler map
SERVICE_HANDLERS = {
    "grammar": lambda p: grammar.correct(p["text"]),
    "paraphrase": lambda p: paraphraser.paraphrase(p["text"]),
    "translate": lambda p: translator.translate(p["text"], p["target_lang"]),
    "tone": lambda p: tone.classify(p["text"]),
    "inclusive": lambda p: inclusive.check(p["text"]),
    "voice": lambda p: voice_analyzer.classify(p["text"]),
    "readability": lambda p: readability.compute(p["text"]),
    "synonyms": lambda p: synonyms.suggest(p["text"]),  # ✅ This is async
}

async def worker(worker_id: int):
    logging.info(f"Worker-{worker_id} started")

    while True:
        task = await task_queue.get()
        future = task["future"]
        task_type = task["type"]
        payload = task["payload"]
        task_id = task["id"]

        start_time = time.perf_counter()
        logging.info(f"[Worker-{worker_id}] Processing Task-{task_id} | Type: {task_type} | Queue size: {task_queue.qsize()}")

        try:
            handler = SERVICE_HANDLERS.get(task_type)
            if not handler:
                raise ValueError(f"Unknown task type: {task_type}")

            result = handler(payload)
            if inspect.isawaitable(result):
                result = await result

            elapsed = time.perf_counter() - start_time
            logging.info(f"[Worker-{worker_id}] Finished Task-{task_id} in {elapsed:.2f}s")

            if not future.done():
                future.set_result(result)

        except Exception as e:
            logging.error(f"[Worker-{worker_id}] Error in Task-{task_id} ({task_type}): {e}")
            if not future.done():
                future.set_result({"error": str(e)})

        task_queue.task_done()

def start_workers(count: int = 2):
    for i in range(count):
        asyncio.create_task(worker(i))

async def enqueue_task(task_type: str, payload: dict, timeout: float = 10.0):
    future = asyncio.get_event_loop().create_future()
    task_id = str(uuid.uuid4())[:8]

    await task_queue.put({
        "future": future,
        "type": task_type,
        "payload": payload,
        "id": task_id
    })

    logging.info(f"[ENQUEUE] Task-{task_id} added to queue | Type: {task_type} | Queue size: {task_queue.qsize()}")

    try:
        return await asyncio.wait_for(future, timeout=timeout)
    except asyncio.TimeoutError:
        logging.warning(f"[ENQUEUE] Task-{task_id} timed out after {timeout}s")
        return {"error": f"Task {task_type} timed out after {timeout} seconds."}
