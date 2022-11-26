#!/usr/bin/env python3

import multiprocessing
from parquet_viewer.__main__ import main

if __name__ == "__main__":
    multiprocessing.freeze_support()  # Required for exe
    main()
