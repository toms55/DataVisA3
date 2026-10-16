import csv
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "2026-Spring-Ass3-V20.xlsx"
OUT = ROOT / "data" / "trade.csv"

SHEETS = {"Export-dataset": "Export", "Import-dataset": "Import"}


def clean_name(raw):
    text = raw.strip()
    if text.endswith(";"):
        text = text[:-1]
    return text.strip()


def split_header(raw):
    text = clean_name(raw)
    code, _, name = text.partition(" ")
    return code.strip(), name.strip()


def level_of(code):
    if code == "-1":
        return "total"
    return "main" if len(code) == 1 else "sub"


def read_sheet(worksheet, direction):
    rows = list(worksheet.iter_rows(values_only=True))
    header = rows[0]
    units = rows[1]
    series = rows[2]
    columns = []
    for index in range(1, len(header)):
        code, name = split_header(header[index])
        columns.append((index, code, name, units[index], series[index]))

    records = []
    for row in rows[3:]:
        year = int(str(row[0]).lstrip("Y"))
        for index, code, name, unit, series_id in columns:
            records.append(
                {
                    "direction": direction,
                    "year": year,
                    "code": code,
                    "level": level_of(code),
                    "name": name,
                    "unit": unit,
                    "series_id": series_id,
                    "value": float(row[index]),
                }
            )
    return records


def check(records):
    assert len(records) == 1560, f"expected 1560 rows, got {len(records)}"
    for direction in ("Export", "Import"):
        subset = [r for r in records if r["direction"] == direction]
        years = sorted({r["year"] for r in subset})
        assert years == list(range(2016, 2026)), years
        for level, count in (("main", 10), ("sub", 67), ("total", 1)):
            codes = {r["code"] for r in subset if r["level"] == level}
            assert len(codes) == count, f"{direction} {level}: {len(codes)} not {count}"
        assert {r["unit"] for r in subset} == {"$ Millions"}
        for year in years:
            mains = sum(
                r["value"] for r in subset if r["level"] == "main" and r["year"] == year
            )
            total = next(
                r["value"] for r in subset if r["level"] == "total" and r["year"] == year
            )
            drift = abs(mains - total)
            assert drift <= 10 and drift <= total * 0.0001, (
                f"{direction} {year}: mains {mains} vs total {total}"
            )
    assert not [r for r in records if r["value"] is None]


def main():
    workbook = openpyxl.load_workbook(SOURCE, read_only=True, data_only=True)
    records = []
    for sheet_name, direction in SHEETS.items():
        records += read_sheet(workbook[sheet_name], direction)
    check(records)
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    print(f"wrote {len(records)} rows to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
