# PROTOTYPE image — throwaway
FROM python:3.13-slim
RUN pip install --no-cache-dir numpy opencv-python-headless scikit-image pooch onnxruntime pymixbox google-genai anthropic
ADD https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx /models/yunet.onnx
ADD https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx /models/u2netp.onnx
RUN chmod a+r /models/*
WORKDIR /work
