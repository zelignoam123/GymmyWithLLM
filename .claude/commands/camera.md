---
description: Verify the webcam is accessible — opens a frame and prints resolution. Run before ./run.sh if you suspect camera issues.
allowed-tools: Bash(.venv/bin/python:*)
---

Check camera connectivity.

```bash
OPENCV_AVFOUNDATION_SKIP_AUTH=0 .venv/bin/python -c "
import cv2
cap = cv2.VideoCapture(0)
ok, frame = cap.read()
if ok:
    print('Camera OK — resolution:', frame.shape[1], 'x', frame.shape[0])
else:
    print('FAIL: camera did not return a frame.')
    print('  1. System Settings -> Privacy & Security -> Camera -> enable your terminal app')
    print('  2. Fully quit and reopen the terminal, then re-run /camera')
    print('  3. If still failing: tccutil reset Camera <bundle-id> (see RUN_INSTRUCTIONS.md)')
cap.release()
"
```
