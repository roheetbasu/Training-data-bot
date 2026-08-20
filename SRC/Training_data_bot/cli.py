import argparse
import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from .bot import TrainingDataBot
from .core.models import ExportFormat, TaskType


def _task(value: str) -> TaskType:
    try:
        return TaskType(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Unknown task '{value}'. Choose: {', '.join(t.value for t in TaskType)}"
        ) from exc


async def run_process(source: str, task: TaskType, output: str, no_quality_filter: bool = False):
    async with TrainingDataBot({}) as bot:
        documents = await bot.load_documents(source)
        if not documents:
            raise RuntimeError("No documents were loaded.")
        dataset = await bot.process_documents(
            documents=documents,
            task_types=[task],
            quality_filter=not no_quality_filter,
        )
        report = await bot.evaluate_dataset(dataset)
        exported = await bot.export_dataset(dataset, output, ExportFormat.JSONL)

        print("\n=== Training Data Bot ===")
        print(f"Source documents : {len(documents)}")
        print(f"Task             : {task.value}")
        print(f"Examples kept    : {len(dataset.examples)}")
        print(f"Quality score    : {report.overall_score:.3f}")
        print(f"Quality passed   : {report.passed}")
        print(f"Exported to      : {exported}")
        if dataset.examples:
            ex = dataset.examples[0]
            print("\n--- First example ---")
            print("INPUT:")
            print(ex.input_text[:500])
            print("\nOUTPUT:")
            print(ex.output_text[:1000])
        return dataset


async def run_demo():
    with TemporaryDirectory(prefix="training_data_bot_demo_") as tmp:
        tmp_path = Path(tmp)
        source = tmp_path / "sample.txt"
        output = Path("outputs") / "demo_dataset.jsonl"
        source.write_text(
            "Machine learning systems learn patterns from examples. "
            "A training dataset contains input data and target outputs. "
            "High-quality datasets should be accurate, diverse, relevant, and clear. "
            "This example demonstrates how the Training Data Bot loads a document, "
            "splits it into chunks, generates training examples, evaluates quality, "
            "and exports the result as JSONL.",
            encoding="utf-8",
        )
        await run_process(str(source), TaskType.QA_GENERATION, str(output))


def build_parser():
    parser = argparse.ArgumentParser(
        prog="training-data-bot",
        description="Generate, evaluate, and export LLM training data.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="Run a complete offline demonstration.")
    demo.set_defaults(handler=lambda args: run_demo())

    process = sub.add_parser("process", help="Process a local file or directory.")
    process.add_argument("source", help="Path to a supported file or directory.")
    process.add_argument(
        "--task", type=_task, default=TaskType.QA_GENERATION,
        choices=list(TaskType), metavar="TASK",
        help="qa_generation, classification, or summarization",
    )
    process.add_argument(
        "--output", default="outputs/dataset.jsonl",
        help="Output JSONL path (default: outputs/dataset.jsonl)",
    )
    process.add_argument(
        "--no-quality-filter", action="store_true",
        help="Keep examples even when quality checks fail.",
    )
    process.set_defaults(
        handler=lambda args: run_process(
            args.source, args.task, args.output, args.no_quality_filter
        )
    )
    return parser


def main():
    args = build_parser().parse_args()
    asyncio.run(args.handler(args))


if __name__ == "__main__":
    main()
