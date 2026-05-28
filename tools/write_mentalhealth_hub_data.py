#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""メンタルヘルスII種 知識ハブ CSV 統合出力（S30 + S31 + S32 + S33 + S34 + S35-S44）."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.hub_merge_data import merge_rows, write_hub_csvs  # noqa: E402
from tools.write_mentalhealth_hub_premium_faqs import apply_all as apply_premium_faqs  # noqa: E402
from tools.write_mentalhealth_hub_s30 import DATA, HEADER_COMPARE, HEADER_MISTAKES, HEADER_NUMBERS  # noqa: E402
from tools.write_mentalhealth_hub_s30_content import COMPARISONS as C30, MISTAKES as M30, NUMBERS as N30  # noqa: E402
from tools.write_mentalhealth_hub_s31_content import (  # noqa: E402
    COMPARISONS_ADD as C31,
    MISTAKES_ADD as M31,
    NUMBERS_ADD as N31,
)
from tools.write_mentalhealth_hub_s32_content import (  # noqa: E402
    COMPARISONS_ADD as C32,
    MISTAKES_ADD as M32,
    NUMBERS_ADD as N32,
)
from tools.write_mentalhealth_hub_s33_content import (  # noqa: E402
    COMPARISONS_ADD as C33,
    MISTAKES_ADD as M33,
    NUMBERS_ADD as N33,
)
from tools.write_mentalhealth_hub_s34_content import (  # noqa: E402
    COMPARISONS_ADD as C34,
    MISTAKES_ADD as M34,
    NUMBERS_ADD as N34,
)
from tools.write_mentalhealth_hub_s35_content import (  # noqa: E402
    COMPARISONS_ADD as C35,
    MISTAKES_ADD as M35,
    NUMBERS_ADD as N35,
)
from tools.write_mentalhealth_hub_s36_content import (  # noqa: E402
    COMPARISONS_ADD as C36,
    MISTAKES_ADD as M36,
    NUMBERS_ADD as N36,
)
from tools.write_mentalhealth_hub_s37_content import (  # noqa: E402
    COMPARISONS_ADD as C37,
    MISTAKES_ADD as M37,
    NUMBERS_ADD as N37,
)
from tools.write_mentalhealth_hub_s38_content import (  # noqa: E402
    COMPARISONS_ADD as C38,
    MISTAKES_ADD as M38,
    NUMBERS_ADD as N38,
)
from tools.write_mentalhealth_hub_s39_content import (  # noqa: E402
    COMPARISONS_ADD as C39,
    MISTAKES_ADD as M39,
    NUMBERS_ADD as N39,
)
from tools.write_mentalhealth_hub_s44_content import (  # noqa: E402
    COMPARISONS_ADD as C44,
    MISTAKES_ADD as M44,
    NUMBERS_ADD as N44,
)
from tools.write_mentalhealth_hub_s43_content import (  # noqa: E402
    COMPARISONS_ADD as C43,
    MISTAKES_ADD as M43,
    NUMBERS_ADD as N43,
)
from tools.write_mentalhealth_hub_s42_content import (  # noqa: E402
    COMPARISONS_ADD as C42,
    MISTAKES_ADD as M42,
    NUMBERS_ADD as N42,
)
from tools.write_mentalhealth_hub_s41_content import (  # noqa: E402
    COMPARISONS_ADD as C41,
    MISTAKES_ADD as M41,
    NUMBERS_ADD as N41,
)
from tools.write_mentalhealth_hub_s40_content import (  # noqa: E402
    COMPARISONS_ADD as C40,
    MISTAKES_ADD as M40,
    NUMBERS_ADD as N40,
)


def main() -> None:
    write_hub_csvs(
        DATA,
        header_compare=HEADER_COMPARE,
        header_numbers=HEADER_NUMBERS,
        header_mistakes=HEADER_MISTAKES,
        comparisons=merge_rows(C30, C31, C32, C33, C34, C35, C36, C37, C38, C39, C40, C41, C42, C43, C44),
        numbers=merge_rows(N30, N31, N32, N33, N34, N35, N36, N37, N38, N39, N40, N41, N42, N43, N44),
        mistakes=merge_rows(M30, M31, M32, M33, M34, M35, M36, M37, M38, M39, M40, M41, M42, M43, M44),
        apply_premium=apply_premium_faqs,
    )


if __name__ == "__main__":
    main()
