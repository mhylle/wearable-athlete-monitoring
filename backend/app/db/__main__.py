"""Allow running seed as: python -m app.db"""

import asyncio

from app.db.seed import _main

asyncio.run(_main())
