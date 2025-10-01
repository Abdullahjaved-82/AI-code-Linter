from linter import analyze_code

wrong_code = '''
# Logical bug: initializing max to 0 fails for all-negative lists
def find_max(nums):
    max_val = 0
    for n in nums:
        if n > max_val:
            max_val = n
    return max_val

# Exception handling issue: bare except swallows errors
def risky_div(a, b):
    try:
        return a / b
    except:
        pass

# Resource handling issue: file opened but not closed
def read_first_line(path):
    f = open(path, 'r')
    line = f.readline()
    return line

# Off-by-one and == None examples
def process(arr):
    total = 0
    for i in range(len(arr) + 1):
        total += arr[i]
    return total

if None == None:
    pass

print('find_max:', find_max([-5, -2, -3]))
print('risky_div:', risky_div(10, 0))
print('read_first_line:', read_first_line('this_file_does_not_exist.txt'))
print('process:', process([1,2,3]))
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
