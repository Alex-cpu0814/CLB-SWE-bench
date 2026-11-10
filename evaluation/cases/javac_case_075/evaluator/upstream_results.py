"""Read original TestNG XML without treating missing/skipped tests as passes."""
from pathlib import Path
import xml.etree.ElementTree as ET


def parse_upstream_results(path, expected_ids, ant_exit_code):
    tests = {name: {"status": "missing"} for name in expected_ids}
    details = {"ant_exit_code": ant_exit_code, "configuration_failures": 0,
               "expected_tests": len(expected_ids), "report_valid": False}
    try:
        root = ET.parse(Path(path)).getroot()
        if root.tag != "testng-results":
            raise ValueError("Unexpected TestNG XML root")
    except (OSError, ET.ParseError, ValueError) as error:
        details["reason"] = str(error)
        return tests, details, False
    details.update(root.attrib)
    details["report_valid"] = True
    seen = set()
    duplicates = []
    for cls in root.findall(".//class"):
        for method in cls.findall("test-method"):
            status = method.get("status")
            if method.get("is-config") == "true":
                if status != "PASS":
                    details["configuration_failures"] += 1
                continue
            name = cls.get("name", "") + "::" + method.get("name", "")
            if name in seen:
                duplicates.append(name)
                tests[name] = {"status": "failed", "reason": "duplicate_test_id"}
                continue
            seen.add(name)
            tests[name] = {"status": {"PASS": "passed", "FAIL": "failed",
                                       "SKIP": "skipped"}.get(status, "failed")}
    details["duplicate_ids"] = duplicates
    details["missing_ids"] = sorted(set(expected_ids) - seen)
    details["unexpected_ids"] = sorted(seen - set(expected_ids))
    ok = (ant_exit_code == 0 and not details["configuration_failures"]
          and not duplicates and not details["missing_ids"] and not details["unexpected_ids"]
          and root.get("total") == root.get("passed") == str(len(expected_ids))
          and root.get("failed") == root.get("skipped") == "0"
          and all(item["status"] == "passed" for item in tests.values()))
    return tests, details, ok
