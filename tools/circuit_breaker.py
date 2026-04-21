import time
import functools
from datetime import datetime
from enum import Enum

class State(Enum):
    CLOSED = "CLOSED"        # funcionando normal
    OPEN = "OPEN"            # cortado — rechaza llamadas
    HALF_OPEN = "HALF_OPEN"  # probando recuperación

class CircuitBreaker:
    def __init__(self, name, failure_threshold=3, recovery_timeout=30, success_threshold=2):
        self.name = name
        self.failure_threshold = failure_threshold   # fallos para abrir
        self.recovery_timeout = recovery_timeout     # segundos antes de probar
        self.success_threshold = success_threshold   # éxitos para cerrar
        self.state = State.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.log = []

    def _record(self, event, detail=""):
        entry = {
            "ts": datetime.now().strftime("%H:%M:%S"),
            "state": self.state.value,
            "event": event,
            "detail": detail
        }
        self.log.append(entry)
        print(f"[CB:{self.name}] [{entry['ts']}] {self.state.value} — {event} {detail}")

    def call(self, func, *args, **kwargs):
        if self.state == State.OPEN:
            elapsed = time.time() - self.last_failure_time
            if elapsed >= self.recovery_timeout:
                self.state = State.HALF_OPEN
                self.success_count = 0
                self._record("HALF_OPEN", f"intentando recuperación tras {elapsed:.0f}s")
            else:
                self._record("REJECTED", f"circuito abierto, {self.recovery_timeout - elapsed:.0f}s para reintento")
                raise CircuitOpenError(f"Circuit breaker '{self.name}' OPEN — espera {self.recovery_timeout - elapsed:.0f}s")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(str(e))
            raise

    def _on_success(self):
        self.failure_count = 0
        if self.state == State.HALF_OPEN:
            self.success_count += 1
            self._record("SUCCESS", f"{self.success_count}/{self.success_threshold} éxitos para cerrar")
            if self.success_count >= self.success_threshold:
                self.state = State.CLOSED
                self._record("CLOSED", "circuito cerrado — sistema recuperado")
        else:
            self._record("SUCCESS")

    def _on_failure(self, error):
        self.failure_count += 1
        self.last_failure_time = time.time()
        self._record("FAILURE", f"{self.failure_count}/{self.failure_threshold} — {error[:60]}")
        if self.failure_count >= self.failure_threshold:
            self.state = State.OPEN
            self._record("OPEN", f"umbral alcanzado — circuito abierto")

    def status(self):
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self.failure_count,
            "threshold": self.failure_threshold,
            "last_failure": self.last_failure_time,
            "log": self.log[-10:]
        }

class CircuitOpenError(Exception):
    pass

# Instancia global para el LLM
llm_breaker = CircuitBreaker(
    name="HuggingFace-LLM",
    failure_threshold=3,
    recovery_timeout=30,
    success_threshold=2
)
