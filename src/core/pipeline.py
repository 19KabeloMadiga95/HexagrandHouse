from dataclasses import dataclass, field
from typing import Callable, Any
import time

from src.core.logging import (
    pipeline_banner,
    pipeline_complete,
    success,
    warning,
    error,
)


@dataclass
class PipelineStep:
    name: str
    function: Callable
    required: bool = True


@dataclass
class PipelineResult:
    step_name: str
    status: str
    duration_seconds: float
    error_message: str = ""


@dataclass
class BasePipeline:
    name: str
    steps: list[PipelineStep] = field(default_factory=list)
    results: list[PipelineResult] = field(default_factory=list)

    def add_step(self, name: str, function: Callable, required: bool = True):
        self.steps.append(
            PipelineStep(
                name=name,
                function=function,
                required=required,
            )
        )

    def run_step(self, step: PipelineStep):
        start = time.perf_counter()

        try:
            step.function()

            duration = time.perf_counter() - start

            self.results.append(
                PipelineResult(
                    step_name=step.name,
                    status="Success",
                    duration_seconds=duration,
                )
            )

            success(f"{step.name} completed in {duration:.2f}s")

        except Exception as exc:
            duration = time.perf_counter() - start

            self.results.append(
                PipelineResult(
                    step_name=step.name,
                    status="Failed",
                    duration_seconds=duration,
                    error_message=str(exc),
                )
            )

            if step.required:
                error(f"{step.name} failed: {exc}")
                raise

            warning(f"{step.name} failed but was optional: {exc}")

    def run(self):
        pipeline_banner(self.name)

        self.results = []

        for step in self.steps:
            self.run_step(step)

        self.print_summary()

        pipeline_complete(self.name)

        return self.results

    def print_summary(self):
        print("")
        print("======================================")
        print(f"{self.name.upper()} SUMMARY")
        print("======================================")

        for result in self.results:
            print(
                f"{result.step_name} | "
                f"{result.status} | "
                f"{result.duration_seconds:.2f}s"
            )

            if result.error_message:
                print(f"  Error: {result.error_message}")

        print("======================================")