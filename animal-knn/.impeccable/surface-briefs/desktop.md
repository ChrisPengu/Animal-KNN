# Windows classification window

Mode: Operate. Code-led migration of an existing, approved classification flow.

User confirmation: Windows App, not Web App; source code is sufficient and a .bat launcher is requested. Existing six-class K-NN classification, preprocessing and five neighbors are settled requirements. Keep real models, metrics, source photos and attributions.

Visual direction: preserve the established white / dark green / research green palette and the image-left, result-right composition. Translate controls to Tkinter/ttk with Windows file dialog and Segoe UI. No new brand or decorative imagery. The first viewport should show the task, file/sample selector, image, vote scores and five training examples in the resulting state.

Behavior: model loading and prediction run in a worker thread, UI mutations only in Tk's event thread. Disable source changes while busy. Clear prior predictions when the image changes or is invalid. Inline recoverable errors. Ctrl+O opens file selection, Ctrl+Enter predicts. Closing during work waits for the worker before destroying Tk.

Quality bar: native focus and keyboard navigation, no clipped essential controls at the supported 1080×760 minimum, readable Vietnamese, whole photos without aspect distortion, actual backend labels/scores/reference IDs, friendly corrupt-file recovery. Capture empty/result/info states on Windows; no mobile target and no web detector for the Tk UI.
