"""Điểm khởi động Windows; run-desktop.bat dùng pythonw để ẩn console."""
if __name__ == "__main__":
    try:
        from animal_knn.desktop import main
        main()
    except Exception:
        import ctypes
        import traceback
        from pathlib import Path
        log = Path(__file__).resolve().parent / "desktop-startup.log"
        log.write_text(traceback.format_exc(), encoding="utf-8")
        ctypes.windll.user32.MessageBoxW(None, f"Không khởi động được ứng dụng.\nChạy bootstrap.ps1 theo README.\nChi tiết: {log}",
                                         "Animal K-NN", 0x10)
