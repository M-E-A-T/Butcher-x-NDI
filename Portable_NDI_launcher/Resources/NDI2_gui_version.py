#!/usr/bin/env python3

import cv2
import numpy as np
import time
import NDIlib as ndi

WINDOW_NAME = "NDI Fullscreen"

from ndi_source_selector import choose_source


def find_first_source(finder):
    try:
        src = choose_source(ndi, finder)

        if src:
            print(
                f"[*] User selected source: "
                f"{getattr(src, 'ndi_name', None) or getattr(src, 'p_ndi_name', None)}"
            )
            return src

        print("[*] User cancelled source selection.")
        raise SystemExit(0)

    except (SystemExit, KeyboardInterrupt):
        raise

    except Exception as e:
        print(f"[!] Source selector UI failed: {e}. Falling back to auto-detect.")

    while True:
        ndi.find_wait_for_sources(finder, 2000)
        sources = ndi.find_get_current_sources(finder)

        if len(sources) > 0:
            print(f"[*] Successfully established source: {sources[0].ndi_name}")
            return sources[0]

        print("[!] Waiting for an NDI source broadcast...")
        time.sleep(2)


def create_receiver(source):
    recv_create = ndi.RecvCreateV3()
    recv_create.color_format = ndi.RECV_COLOR_FORMAT_BGRX_BGRA

    if hasattr(ndi, "RECV_BANDWIDTH_HIGHEST"):
        recv_create.bandwidth = ndi.RECV_BANDWIDTH_HIGHEST
        print("[*] Using NDI highest bandwidth mode.")
    else:
        print("[!] No NDI bandwidth constant exposed. Leaving bandwidth unset.")

    # IMPORTANT:
    # Your local NDIlib.py wrapper does not actually pass transmission_type
    # into the native NDI recv_create_v3 struct.
    # So do not fake TCP/UDP with integer values here.
    print("[*] Transmission type not forced.")
    print("[*] Letting the native NDI SDK choose transport.")

    receiver = ndi.recv_create_v3(recv_create)

    if receiver is None:
        raise RuntimeError("Failed to create NDI receiver instance.")

    ndi.recv_connect(receiver, source)

    return receiver


def main():
    if not ndi.initialize():
        raise RuntimeError("NDI initialization failed")

    finder = ndi.find_create_v2()

    if finder is None:
        raise RuntimeError("Could not create NDI finder")

    receiver = None
    window_initialized = False

    print("[*] NDI Engine Started. Searching network...")

    try:
        while True:
            if receiver is None:
                source = find_first_source(finder)
                receiver = create_receiver(source)
                time.sleep(0.5)

            frame_type, video_frame, audio_frame, metadata_frame = (
                ndi.recv_capture_v2(receiver, 500)
            )

            if frame_type == ndi.FRAME_TYPE_VIDEO:
                if video_frame.data is None:
                    ndi.recv_free_video_v2(receiver, video_frame)

                    key = cv2.waitKey(1)
                    if key == 27:
                        break

                    continue

                height = video_frame.yres
                width = video_frame.xres
                stride = video_frame.line_stride_in_bytes
                fourcc = video_frame.FourCC

                try:
                    flat_buffer = np.frombuffer(video_frame.data, dtype=np.uint8)

                    if fourcc == ndi.FOURCC_VIDEO_TYPE_UYVY:
                        # UYVY uses 2 bytes per pixel.
                        expected_bytes_per_row = width * 2

                        frame_2d = flat_buffer.reshape((height, stride))
                        valid_pixels = frame_2d[:, :expected_bytes_per_row]

                        frame = np.reshape(valid_pixels, (height, width, 2))
                        frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_UYVY)

                    else:
                        # BGRX/BGRA uses 4 bytes per pixel.
                        expected_bytes_per_row = width * 4

                        actual_stride = (
                            stride
                            if flat_buffer.size >= height * stride
                            else expected_bytes_per_row
                        )

                        frame_2d = flat_buffer[: height * actual_stride].reshape(
                            (height, actual_stride)
                        )

                        valid_pixels = frame_2d[:, :expected_bytes_per_row]

                        frame = np.reshape(valid_pixels, (height, width, 4))
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                    if not window_initialized:
                        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
                        cv2.setWindowProperty(
                            WINDOW_NAME,
                            cv2.WND_PROP_FULLSCREEN,
                            cv2.WINDOW_FULLSCREEN,
                        )
                        window_initialized = True

                    cv2.imshow(WINDOW_NAME, frame)

                except Exception as e:
                    print(
                        f"[-] Decoding anomaly: {e} | "
                        f"Expected Stride: {stride}, "
                        f"Total Buffer Size: "
                        f"{flat_buffer.size if 'flat_buffer' in locals() else 'Unknown'}"
                    )

                ndi.recv_free_video_v2(receiver, video_frame)

            elif frame_type == ndi.FRAME_TYPE_STATUS_CHANGE:
                print(
                    "[!] NDI Alert: Source status shifted or packet dropped. "
                    "Holding connection..."
                )

            elif frame_type == ndi.FRAME_TYPE_AUDIO:
                ndi.recv_free_audio_v2(receiver, audio_frame)

            elif frame_type == ndi.FRAME_TYPE_METADATA:
                ndi.recv_free_metadata(receiver, metadata_frame)

            elif frame_type == ndi.FRAME_TYPE_NONE:
                time.sleep(0.005)

            key = cv2.waitKey(1)

            if key == 27:  # ESC to exit
                break

    finally:
        print("[*] Shutting down clean...")

        if receiver:
            ndi.recv_destroy(receiver)

        ndi.find_destroy(finder)
        ndi.destroy()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()