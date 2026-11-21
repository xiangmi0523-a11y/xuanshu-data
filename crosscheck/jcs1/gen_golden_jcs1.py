#!/usr/bin/env python3
r"""
jcs-1 金标向量独立生成器（E2 审核清单 §6.2、§6.4(6)；DB-H-20）。

- 不导入、不调用引擎代码（D4 第 2 条）；只用 Python 标准库自写严格解析与规范化。
- 规则：键按 UTF-16 码元升序；不做 Unicode 规范化；拒绝重复键、孤立代理、NaN/Infinity、-0、
  非整数、超出 ±(2^53-1) 的整数；字符串只转义 " \ 与 U+0000～U+001F（\b \f \n \r \t 用短式，其余 \u00xx 小写）；
  输出 UTF-8，无多余空白；哈希为 sha256 小写十六进制。
- 集合数组：按向量声明的路径，以元素规范化文本（UTF-16 码元序）排序后再输出（GV-06）。
- GV-07～GV-13 的输入文本取自引擎端到端用例的对象（E2E-BZ-1、E2E-LY-1），此处以字面量写死，
  键序故意倒置并加缩进；不含任何夹具 ID（GV-13 只取不含夹具 ID 的条目）。

用法：python3 crosscheck/jcs1/gen_golden_jcs1.py [输出路径]   （缺省写 crosscheck/jcs1/golden_jcs1.json）
"""
import hashlib
import json
import os
import sys

MAX_SAFE = 2 ** 53 - 1


class Reject(Exception):
    pass


def _pairs(pairs):
    seen = set()
    for k, _ in pairs:
        if k in seen:
            raise Reject("duplicate_key")
        seen.add(k)
    return dict(pairs)


def _int(s):
    if s == "-0":
        raise Reject("negative_zero")
    v = int(s)
    if abs(v) > MAX_SAFE:
        raise Reject("unsafe_integer")
    return v


def _float(s):
    raise Reject("non_integer")


def _const(s):
    raise Reject("nan_or_infinity")


def _check_str(x):
    if isinstance(x, str):
        if any(0xD800 <= ord(ch) <= 0xDFFF for ch in x):
            raise Reject("lone_surrogate")
    elif isinstance(x, dict):
        for k, v in x.items():
            _check_str(k)
            _check_str(v)
    elif isinstance(x, list):
        for v in x:
            _check_str(v)


def parse(text):
    v = json.loads(text, object_pairs_hook=_pairs, parse_int=_int, parse_float=_float, parse_constant=_const)
    _check_str(v)
    return v


def _u16(s):
    return s.encode("utf-16-be")


SHORT = {0x08: "\\b", 0x09: "\\t", 0x0A: "\\n", 0x0C: "\\f", 0x0D: "\\r"}


def _str(s):
    out = ['"']
    for ch in s:
        c = ord(ch)
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif c < 0x20:
            out.append(SHORT.get(c, "\\u%04x" % c))
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def canon(v):
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return _str(v)
    if isinstance(v, list):
        return "[" + ",".join(canon(x) for x in v) + "]"
    if isinstance(v, dict):
        keys = sorted(v.keys(), key=_u16)
        return "{" + ",".join(_str(k) + ":" + canon(v[k]) for k in keys) + "}"
    raise Reject("unsupported_type")


def sort_set(v, path):
    """path 为键列表，指向一个集合数组；按元素规范化文本的 UTF-16 码元序排序"""
    if not path:
        return sorted(v, key=lambda x: _u16(canon(x)))
    v = dict(v)
    v[path[0]] = sort_set(v[path[0]], path[1:])
    return v


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---- 端到端对象（字面量，键序倒置）----
INPUT_BZ = '{\n  "tz_resolution": {\n    "offset_source": "契约 §11.1 内地夏令时区间（1990-04-15～09-16）",\n    "tz_table_version": "未记录",\n    "tzdata_version": "未记录",\n    "dst_flag": true,\n    "utc_offset_seconds": 32400,\n    "tz_id": "Asia/Shanghai"\n  },\n  "normalizer_version": "e2-norm-1",\n  "normalized_payload": {\n    "utc8_civil": "1990-06-15T13:30",\n    "utc_instant": "1990-06-15T05:30:00.000Z",\n    "v": 1\n  },\n  "raw_payload": {\n    "place_name": "北京",\n    "latitude": "39.900000",\n    "longitude": "116.400000",\n    "dst_included": true,\n    "tz_id": "Asia/Shanghai",\n    "gender": "UNKNOWN",\n    "time_precision": "MINUTE",\n    "civil_datetime": "1990-06-15T14:30",\n    "v": 1\n  },\n  "domain": "BAZI",\n  "v": 1\n}'
INPUT_LY = '{\n  "tz_resolution": {\n    "offset_source": "契约 §11.1 境内 UTC+8",\n    "tz_table_version": "未记录",\n    "tzdata_version": "未记录",\n    "dst_flag": false,\n    "utc_offset_seconds": 28800,\n    "tz_id": "Asia/Shanghai"\n  },\n  "normalizer_version": "e2-norm-1",\n  "normalized_payload": {\n    "utc8_civil": "2026-11-21T12:00",\n    "utc_instant": "2026-11-21T04:00:00.000Z",\n    "v": 1\n  },\n  "raw_payload": {\n    "yao": [\n      7,\n      8,\n      9,\n      6,\n      7,\n      8\n    ],\n    "method": "coins",\n    "tz_id": "Asia/Shanghai",\n    "cast_datetime": "2026-11-21T12:00",\n    "v": 1\n  },\n  "domain": "LIUYAO",\n  "v": 1\n}'
CONFIG_BZ = '{\n  "params": [\n    {\n      "apply_mode": "applied",\n      "value_source": "version_locked",\n      "value": "ye_zi_b",\n      "param_id": "CFG-01"\n    },\n    {\n      "apply_mode": "applied",\n      "value_source": "follows_param",\n      "value": "clock",\n      "param_id": "CFG-01T"\n    },\n    {\n      "apply_mode": "applied",\n      "value_source": "user_selected",\n      "value": "false",\n      "param_id": "CFG-02"\n    },\n    {\n      "apply_mode": "applied",\n      "value_source": "approved_default",\n      "value": "lichun",\n      "param_id": "CFG-03"\n    },\n    {\n      "apply_mode": "stored_only",\n      "value_source": "user_selected",\n      "value": "yh_yuelu",\n      "param_id": "CFG-04"\n    },\n    {\n      "apply_mode": "stored_only",\n      "value_source": "approved_default",\n      "value": "jieqi_day_1",\n      "param_id": "CFG-04C"\n    },\n    {\n      "apply_mode": "applied",\n      "value_source": "approved_default",\n      "value": "yuan_hai_static",\n      "param_id": "CFG-05"\n    },\n    {\n      "apply_mode": "applied",\n      "value_source": "approved_default",\n      "value": "wu",\n      "param_id": "CFG-05S"\n    },\n    {\n      "apply_mode": "applied",\n      "value_source": "approved_default",\n      "value": "none",\n      "param_id": "CFG-05W"\n    },\n    {\n      "apply_mode": "applied",\n      "value_source": "approved_default",\n      "value": "iana",\n      "param_id": "CFG-14"\n    },\n    {\n      "apply_mode": "applied",\n      "value_source": "approved_default",\n      "value": "iana",\n      "param_id": "CFG-15"\n    }\n  ],\n  "registry_version": "contract-v1.0-P-8",\n  "module": "BAZI",\n  "v": 1\n}'
CONFIG_LY = '{\n  "params": [],\n  "registry_version": "contract-v1.0-P-8",\n  "module": "LIUYAO",\n  "v": 1\n}'
RESULT_BZ = '{\n  "year_pillar": {\n    "value": "庚午",\n    "ambiguous": false\n  },\n  "v": 1,\n  "shishen": {\n    "year": {\n      "stem": "劫财",\n      "hidden": [\n        "七杀",\n        "偏印"\n      ]\n    },\n    "month": {\n      "stem": "伤官",\n      "hidden": [\n        "七杀",\n        "偏印"\n      ]\n    },\n    "hour": {\n      "stem": "偏财",\n      "hidden": [\n        "偏印",\n        "七杀",\n        "偏财"\n      ]\n    },\n    "day": {\n      "stem": "日主",\n      "hidden": [\n        "伤官",\n        "正财"\n      ]\n    }\n  },\n  "result_scope": [\n    "canggan",\n    "changsheng",\n    "luck_cycle",\n    "pillars",\n    "shishen"\n  ],\n  "requires_user_confirmation": false,\n  "notices": [],\n  "month_pillar": {\n    "value": "壬午",\n    "ambiguous": false\n  },\n  "luck_cycle": {\n    "value": null,\n    "status": "DEGRADED_LUCK_OMITTED",\n    "reason": "MISSING_GENDER"\n  },\n  "hour_pillar": {\n    "value": "乙未",\n    "ambiguous": false\n  },\n  "day_pillar": {\n    "value": "辛亥",\n    "ambiguous": false\n  },\n  "changsheng": {\n    "year": "病",\n    "month": "病",\n    "layer": "术数传承层",\n    "hour": "衰",\n    "day": "沐浴"\n  },\n  "canggan": {\n    "year": [\n      "丁",\n      "己"\n    ],\n    "month": [\n      "丁",\n      "己"\n    ],\n    "layer": "现代整理层",\n    "hour": [\n      "己",\n      "丁",\n      "乙"\n    ],\n    "day": [\n      "壬",\n      "甲"\n    ]\n  }\n}'
RESULT_LY = '{\n  "xunkong_branches": [\n    "辰",\n    "巳"\n  ],\n  "v": 1,\n  "result_scope": [\n    "bagong",\n    "bian",\n    "liuqin",\n    "liushen",\n    "najia",\n    "shiying",\n    "xunkong"\n  ],\n  "notices": [],\n  "day_ganzhi": "己亥",\n  "bian": {\n    "name": "泽雷随",\n    "lines": [\n      {\n        "yang": true,\n        "najia": "庚子",\n        "liuqin": "兄弟"\n      },\n      {\n        "yang": false,\n        "najia": "庚寅",\n        "liuqin": "子孙"\n      },\n      {\n        "yang": false,\n        "najia": "庚辰",\n        "liuqin": "官鬼"\n      },\n      {\n        "yang": true,\n        "najia": "丁亥",\n        "liuqin": "兄弟"\n      },\n      {\n        "yang": true,\n        "najia": "丁酉",\n        "liuqin": "父母"\n      },\n      {\n        "yang": false,\n        "najia": "丁未",\n        "liuqin": "官鬼"\n      }\n    ]\n  },\n  "ben": {\n    "ying": 6,\n    "shi": 3,\n    "position": "三世",\n    "palace": "坎",\n    "name": "水火既济",\n    "lines": [\n      {\n        "yao": 7,\n        "xunkong": false,\n        "najia": "己卯",\n        "liushen": "螣蛇",\n        "liuqin": "子孙"\n      },\n      {\n        "yao": 8,\n        "xunkong": false,\n        "najia": "己丑",\n        "liushen": "白虎",\n        "liuqin": "官鬼"\n      },\n      {\n        "yao": 9,\n        "xunkong": false,\n        "najia": "己亥",\n        "liushen": "玄武",\n        "liuqin": "兄弟"\n      },\n      {\n        "yao": 6,\n        "xunkong": false,\n        "najia": "戊申",\n        "liushen": "青龙",\n        "liuqin": "父母"\n      },\n      {\n        "yao": 7,\n        "xunkong": false,\n        "najia": "戊戌",\n        "liushen": "朱雀",\n        "liuqin": "官鬼"\n      },\n      {\n        "yao": 8,\n        "xunkong": false,\n        "najia": "戊子",\n        "liushen": "勾陈",\n        "liuqin": "兄弟"\n      }\n    ]\n  }\n}'
RESOLVED = '[\n  {\n    "value": "小暑@1990-07-07T09:00:29.000Z",\n    "key": "jie",\n    "item_kind": "jieqi_next"\n  },\n  {\n    "value": "芒种@1990-06-05T22:46:18.000Z",\n    "key": "jie",\n    "item_kind": "jieqi_prev"\n  },\n  {\n    "content_hash": "374922ef04e105f61fc7fd5e16966b6ae4584d39bf1f1abe39d0b38dc0fc3d89",\n    "version": "B4-22",\n    "key": "day_pillar",\n    "item_kind": "table_version"\n  },\n  {\n    "content_hash": "69a3215524381f96b212bc682416a3da47d9de4f286fa4ef14ce9ed03ee616e4",\n    "version": "B4-22",\n    "key": "jieqi",\n    "item_kind": "table_version"\n  }\n]'

VECTORS = [
    ("GV-01", "键序：ASCII、CJK、补充平面键混排（UTF-16 码元序：补充平面键排在 U+E000 以上键之前）",
     r'{"z": 1, "a": 2, "中": 3, "𠀀": 4, "ａ": 5, "A": 6, "é": 7, "aa": 8, "": 9}', []),
    ("GV-02", "Unicode：预组合与分解形式、CJK 兼容字均原样保留，不做规范化",
     r'{"precomposed": "é", "decomposed": "é", "compat": "﨑", "é": "key-precomposed", "é": "key-decomposed"}', []),
    ("GV-03", "转义：引号、反斜杠、控制字符；DEL、U+2028、U+2029、/ 不转义",
     r'{"s": "q\" b\\ \u0000\u0001\b\t\n\u000b\f\r\u001f \u007f    /"}', []),
    ("GV-04", "数值：安全整数边界与零；小数一律以定标十进制字符串表示 dec(1/3/6)",
     r'{"max": 9007199254740991, "min": -9007199254740991, "zero": 0, "dec1": "4.5", "dec3": "0.125", "dec6": "116.400000"}', []),
    ("GV-05", "null 与省略：契约明定为 null 的字段写 null；不适用的字段省略（省略不等于写 null）",
     r'{"luck_cycle": {"value": null, "status": "DEGRADED_LUCK_OMITTED", "reason": "MISSING_GENDER"}, "a": null}', []),
    ("GV-06", "有序与集合数组：ordered 保持原序；set 按元素规范化文本升序",
     r'{"ordered": [3, 1, 2], "set": ["丙", "乙", "甲", "10", "9"]}', [["set"]]),
    ("GV-07", "E2E-BZ-1 完整 input 对象（input_hash）", INPUT_BZ, []),
    ("GV-08", "E2E-LY-1 完整 input 对象（input_hash）", INPUT_LY, []),
    ("GV-09", "E2E-BZ-1 config 对象（config_hash；params 按 param_id 升序，含 Q-12 apply_mode）", CONFIG_BZ, []),
    ("GV-10", "E2E-LY-1 config 对象（空参数集写 []，config_hash）", CONFIG_LY, []),
    ("GV-11", "八字 result_payload 样例（result_hash）", RESULT_BZ, []),
    ("GV-12", "六爻 result_payload 样例（含变卦，result_hash）", RESULT_LY, []),
    ("GV-13", "resolved_context 样例（按 item_kind、key 升序的数组，data_fingerprint）", RESOLVED, []),
]

REJECTS = [
    ("duplicate_key", r'{"a": 1, "a": 2}'),
    ("duplicate_key", r'{"x": {"k": 1, "k": 1}}'),
    ("lone_surrogate", r'{"a": "\ud800"}'),
    ("lone_surrogate", r'{"\udc00": 1}'),
    ("nan_or_infinity", r'{"a": NaN}'),
    ("nan_or_infinity", r'{"a": Infinity}'),
    ("negative_zero", r'{"a": -0}'),
    ("unsafe_integer", r'{"a": 9007199254740992}'),
    ("unsafe_integer", r'{"a": -9007199254740992}'),
    ("non_integer", r'{"a": 1.5}'),
    ("non_integer", r'{"a": 1e2}'),
    ("non_integer", r'{"a": 1.0}'),
]


def build():
    out = {"version": "jcs-1", "spec": "E2 审核清单 §6.2、§6.4", "independent": "数据仓库独立实现生成，不调用引擎代码", "vectors": []}
    for vid, desc, text, sets in VECTORS:
        v = parse(text)
        for path in sets:
            v = sort_set(v, path)
        c = canon(v)
        out["vectors"].append({"id": vid, "desc": desc, "input": text, "set_paths": sets, "canonical": c, "sha256": sha(c)})
    rej = []
    for reason, text in REJECTS:
        try:
            parse(text)
        except Reject as e:
            if str(e) != reason:
                raise SystemExit(f"拒绝原因不符：{text} → {e}，应为 {reason}")
            rej.append({"input": text, "reason": reason})
            continue
        raise SystemExit(f"应拒绝却通过：{text}")
    out["vectors"].append({"id": "GV-14", "desc": "拒绝集：重复键、孤立代理、NaN/Infinity、-0、超界整数、非整数", "rejects": rej})
    return json.dumps(out, ensure_ascii=False, indent=1) + "\n"


if __name__ == "__main__":
    dst = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden_jcs1.json")
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write(build())
