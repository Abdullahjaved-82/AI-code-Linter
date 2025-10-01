from pathlib import Path
import traceback

try:
    import linter
except Exception:
    traceback.print_exc()
    raise


def run_test():
    p = Path('temp_code.py')
    if not p.exists():
        print('temp_code.py not found in project root.')
        return
    code = p.read_text(encoding='utf-8')
    print('--- ORIGINAL CODE ---')
    print(code)

    try:
        print('\n--- ANALYZE (no fix) ---')
        res = linter.analyze_code(code)
        print('Report:\n', res[0])
        print('\nFixed preview:\n', (res[1] if len(res) > 1 else ''))
        if len(res) > 2:
            print('\nHighlights:', res[2])
        if len(res) > 3:
            print('\nApplied fixes:', res[3])
    except Exception:
        print('Error while running analyzer (no fix):')
        traceback.print_exc()

    try:
        print('\n--- ANALYZE (with auto_fix=True) ---')
        res2 = linter.analyze_code(code, auto_fix=True)
        print('Report:\n', res2[0])
        print('\nFixed preview:\n', res2[1])
        if len(res2) > 2:
            print('\nHighlights:', res2[2])
        if len(res2) > 3:
            print('\nApplied fixes:', res2[3])
    except Exception:
        print('Error while running analyzer (with auto_fix):')
        traceback.print_exc()


if __name__ == '__main__':
    run_test()
