"""Simple smoke test to verify NDIlib wrapper and native SDK are reachable.

Usage: python3 check_ndilib.py
"""
import time
import sys

try:
    import NDIlib
except Exception as e:
    print('ERROR: could not import NDIlib:', e)
    sys.exit(2)

print('NDIlib module:', NDIlib)

if not NDIlib.initialize():
    print('NDI initialize failed')
    sys.exit(3)

print('NDI initialized:', NDIlib)

finder = NDIlib.find_create_v2()
if not finder:
    print('Could not create finder')
    NDIlib.destroy()
    sys.exit(4)

print('Looking for sources for 3 seconds...')
NDIlib.find_wait_for_sources(finder, 3000)
sources = NDIlib.find_get_current_sources(finder)
print('Found sources:', len(sources))
for s in sources:
    print(' -', getattr(s,'ndi_name', None) or getattr(s,'p_ndi_name', None))

NDIlib.find_destroy(finder)
NDIlib.destroy()
print('Smoke test completed successfully')