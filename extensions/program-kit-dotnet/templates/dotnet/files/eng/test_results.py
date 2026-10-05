"""Read real named test results; skipped/duplicate/empty cases never establish success."""
import xml.etree.ElementTree as ET

def require(condition, message):
    if not condition: raise ValueError(message)

def text(value):
    return isinstance(value, str) and bool(value.strip())

def test_results(path, format_name):
    """Read actual test cases, not aggregate exit codes or a claimed count."""
    tree = ET.parse(path)
    results = {}
    for node in tree.iter():
        tag = node.tag.rsplit('}', 1)[-1]
        if format_name == 'trx' and tag == 'UnitTestResult':
            name, passed = node.get('testName'), node.get('outcome') == 'Passed'
        elif format_name == 'junit' and tag == 'testcase':
            name = '.'.join(filter(None, (node.get('classname'), node.get('name'))))
            passed = not any(c.tag.rsplit('}', 1)[-1] in {'failure', 'error', 'skipped'} for c in node)
        else:
            continue
        require(text(name) and name not in results, 'Missing/duplicate test case name')
        results[name] = passed
    require(results, 'Test runner produced no cases')
    return results
