from .main import _parse_args, _run_as_cli
import asyncio

if __name__ == "__main__":
    args = _parse_args()
    if args.raw_text is not None:
        _run_as_cli(args.raw_text)
    else:
        from .main import _run_as_actor
        asyncio.run(_run_as_actor())
