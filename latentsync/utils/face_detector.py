from insightface.app import FaceAnalysis
import numpy as np
import torch
import os

INSIGHTFACE_DETECT_SIZE = 640


class FaceDetector:
    def __init__(self, device="cuda"):
        # Get the absolute path to the ComfyUI-LatentSyncWrapper directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # current_dir: /home/george/ComfyUI/app/custom_nodes/ComfyUI-LatentSyncWrapper/latentsync/utils
        # wrapper_root should be: /home/george/ComfyUI/app/custom_nodes/ComfyUI-LatentSyncWrapper
        # Need to go up 2 levels: utils -> latentsync -> ComfyUI-LatentSyncWrapper
        wrapper_root = os.path.dirname(os.path.dirname(current_dir))
        print(f"Wrapper root directory: {wrapper_root} current_dir: {current_dir}")
        
        # Check if buffalo_l model files already exist to prevent re-downloading
        model_dir = os.path.join(wrapper_root, "checkpoints", "auxiliary", "models", "buffalo_l")
        required_files = ["1k3d68.onnx", "2d106det.onnx", "det_10g.onnx", "genderage.onnx", "w600k_r50.onnx"]
        
        # Check if all required files exist
        all_files_exist = True
        for file in required_files:
            file_path = os.path.join(model_dir, file)
            if not os.path.exists(file_path):
                all_files_exist = False
                print(f"Missing model file: {file_path}")
                break
        
        # Set environment variables to control insightface behavior
        if all_files_exist:
            print("All buffalo_l model files already exist, preventing re-download")
            os.environ['INSIGHTFACE_NO_DOWNLOAD'] = '1'
            # Set the correct home directory for insightface
            os.environ['INSIGHTFACE_HOME'] = os.path.join(wrapper_root, "checkpoints", "auxiliary")
        else:
            print("Some model files are missing, allowing insightface to download")
            # Remove the environment variable if it exists to allow download
            if 'INSIGHTFACE_NO_DOWNLOAD' in os.environ:
                del os.environ['INSIGHTFACE_NO_DOWNLOAD']
        
        self.app = FaceAnalysis(
            allowed_modules=["detection", "landmark_2d_106"],
            root=os.path.join(wrapper_root, "checkpoints", "auxiliary"),
            providers=["CUDAExecutionProvider"],
        )
        self.app.prepare(ctx_id=cuda_to_int(device), det_size=(INSIGHTFACE_DETECT_SIZE, INSIGHTFACE_DETECT_SIZE))

    def __call__(self, frame, threshold=0.5):
        f_h, f_w, _ = frame.shape

        faces = self.app.get(frame)

        get_face_store = None
        max_size = 0

        if len(faces) == 0:
            return None, None
        else:
            for face in faces:
                bbox = face.bbox.astype(np.int_).tolist()
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                if w < 50 or h < 80:
                    continue
                if w / h > 1.5 or w / h < 0.2:
                    continue
                if face.det_score < threshold:
                    continue
                size_now = w * h

                if size_now > max_size:
                    max_size = size_now
                    get_face_store = face

        if get_face_store is None:
            return None, None
        else:
            face = get_face_store
            lmk = np.round(face.landmark_2d_106).astype(np.int_)

            halk_face_coord = np.mean([lmk[74], lmk[73]], axis=0)  # lmk[73]

            sub_lmk = lmk[LMK_ADAPT_ORIGIN_ORDER]
            halk_face_dist = np.max(sub_lmk[:, 1]) - halk_face_coord[1]
            upper_bond = halk_face_coord[1] - halk_face_dist  # *0.94

            x1, y1, x2, y2 = (np.min(sub_lmk[:, 0]), int(upper_bond), np.max(sub_lmk[:, 0]), np.max(sub_lmk[:, 1]))

            if y2 - y1 <= 0 or x2 - x1 <= 0 or x1 < 0:
                x1, y1, x2, y2 = face.bbox.astype(np.int_).tolist()

            y2 += int((x2 - x1) * 0.1)
            x1 -= int((x2 - x1) * 0.05)
            x2 += int((x2 - x1) * 0.05)

            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(f_w, x2)
            y2 = min(f_h, y2)

            return (x1, y1, x2, y2), lmk


def cuda_to_int(cuda_str: str) -> int:
    """
    Convert the string with format "cuda:X" to integer X.
    """
    if cuda_str == "cuda":
        return 0
    device = torch.device(cuda_str)
    if device.type != "cuda":
        raise ValueError(f"Device type must be 'cuda', got: {device.type}")
    return device.index


LMK_ADAPT_ORIGIN_ORDER = [
    1,
    10,
    12,
    14,
    16,
    3,
    5,
    7,
    0,
    23,
    21,
    19,
    32,
    30,
    28,
    26,
    17,
    43,
    48,
    49,
    51,
    50,
    102,
    103,
    104,
    105,
    101,
    73,
    74,
    86,
]
