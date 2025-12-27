import flet as ft


def main():
    print(f"Flet Version: {ft.version}")
    try:
        fp = ft.FilePicker()
        print("FilePicker instantiated.")
    except Exception as e:
        print(f"FilePicker instantiation failed: {e}")
        return

    print(f"Has on_result: {hasattr(fp, 'on_result')}")
    print(f"Has on_upload: {hasattr(fp, 'on_upload')}")

    try:
        fp.on_result = lambda e: print("Result!")
        print("Assigned on_result successfully.")
    except Exception as e:
        print(f"Failed to assign on_result: {e}")


if __name__ == "__main__":
    main()
