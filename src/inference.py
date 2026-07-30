# -*- coding: utf-8 -*-
import json, base64, io, logging, requests
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def handler(data, context):
    try:
        request_body = data.read().decode('utf-8')
        payload = json.loads(request_body)
        img_b64 = payload.get('image_bytes')
        
        if not img_b64: raise ValueError("Payload thiếu 'image_bytes'")

        image_data = base64.b64decode(img_b64)
        img = Image.open(io.BytesIO(image_data)).convert('RGB')
        img = img.resize((224, 224))
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        tfs_payload = json.dumps({"instances": img_array.tolist()})
        tfs_url = context.rest_uri
        response = requests.post(tfs_url, data=tfs_payload)

        if response.status_code != 200:
            raise RuntimeError(f"TFS Engine Error: {response.text}")

        predictions = response.json().get('predictions', [[]])[0]
        result = {"status": "SUCCESS", "raw_predictions": predictions}

        return json.dumps(result), context.accept_header
    except Exception as e:
        logger.error(f"Lỗi Inference: {str(e)}")
        return json.dumps({"error": f"Internal Server Error: {str(e)}"}), context.accept_header
