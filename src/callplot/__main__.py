"""``python -m callplot``: the same result as the installed command.

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

DESIGN-PYTHON.md section 3.1 rule 3: ``python -m callplot ARGS`` must give the
same result as ``callplot ARGS``, so this only calls ``cli.main()`` and passes
its exit code on.  It holds no argument handling of its own, which is why the
CLI goldens cover it through ``cli.py``.
"""

import sys

from callplot.cli import main

if __name__ == "__main__":
    sys.exit(main())
