from fixer import apply_fixes, attempt_syntax_fixes

samples = [
    ("for i in range(len(arr) + 1):\n    print(i)", "off-by-one"),
    ("try:\n    do_something()\nexcept:\n    handle()", "bare-except"),
    ("if x == None:\n    pass", "eq-none"),
]

for code, name in samples:
    print('---', name, '---')
    new, fixes = apply_fixes(code)
    print('Original:\n', code)
    print('Fixed:\n', new)
    print('Fixes:', fixes)

    # test syntax attempt
    new2, syn = attempt_syntax_fixes(code)
    print('Syntax attempt:', syn)
    print('\n')
