from linter import analyze_code

wrong_code = '''
def broken_divide(a, b)
    x = 42
    return a / b

def process(arr):
    total = 0
    for i in range(len(arr) + 1):
        total += arr[i]
    return total

try:
    r = process([1,2,3])
except:
    print("err")

unused_var = 5
if a == None:
    pass

print(broken_divide(10, 0))
'''

print('--- ORIGINAL CODE ---')
print(wrong_code)

print('\n--- ANALYZE (no fix) ---')
report, fixed, highlights, applied = analyze_code(wrong_code, auto_fix=False)
print('Report:\n', report)
print('\nFixed preview:\n', fixed)
print('\nHighlights:', highlights)
print('\nApplied fixes:', applied)

print('\n--- ANALYZE (with auto_fix=True) ---')
report2, fixed2, highlights2, applied2 = analyze_code(wrong_code, auto_fix=True)
print('Report:\n', report2)
print('\nFixed preview:\n', fixed2)
print('\nHighlights:', highlights2)
print('\nApplied fixes:', applied2)
