import os
from flask import Flask, request, jsonify, send_from_directory, render_template
from ultralytics import YOLO
import cv2
import numpy as np
import base64
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Load YOLO model
model = YOLO('best (32).pt')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Run YOLO model
        img = cv2.imread(filepath)
        results = model(img, conf=0.5, iou=0.5)

        detected_boxes = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                conf = box.conf[0]
                cls = box.cls[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                label = f'{model.names[int(cls)]}: {conf:.2f}'
                detected_boxes.append({
                    'label': label,
                    'coordinates': [x1, y1, x2, y2],
                    'confidence': float(conf),
                    'class': int(cls)
                })

                # Draw bounding box
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Save the image with bounding boxes
        output_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f'output_{filename}')
        cv2.imwrite(output_filepath, img)

        return jsonify({'detected_boxes': detected_boxes, 'output_image': f'output_{filename}'}), 200
    return jsonify({'error': 'File not allowed'}), 400


@app.route('/capture', methods=['POST'])
def capture_image():
    data = request.get_json()
    image_data = data.get('image')
    if not image_data:
        return jsonify({'error': 'No image data provided'}), 400

    image_data = image_data.split(',')[1]  # Remove the data URL prefix
    image_data = np.fromstring(base64.b64decode(image_data), np.uint8)
    img = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

    results = model(img, conf=0.5, iou=0.5)

    detected_boxes = []
    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            conf = box.conf[0]
            cls = box.cls[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            label = f'{model.names[int(cls)]}: {conf:.2f}'
            detected_boxes.append({
                'label': label,
                'coordinates': [x1, y1, x2, y2],
                'confidence': float(conf),
                'class': int(cls)
            })

            # Draw bounding box
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    _, buffer = cv2.imencode('.jpg', img)
    output_image = base64.b64encode(buffer).decode('utf-8')

    return jsonify({'detected_boxes': detected_boxes, 'output_image': output_image}), 200

@app.route('/realtime', methods=['POST'])
def realtime_count():
    data = request.get_json()
    image_data = data.get('image')
    if not image_data:
        return jsonify({'error': 'No image data provided'}), 400

    image_data = image_data.split(',')[1]
    image_data = np.frombuffer(base64.b64decode(image_data), np.uint8)

    if image_data.size == 0:
        return jsonify({'error': 'Failed to decode image: Buffer is empty'}), 400

    img = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

    if img is None:
        return jsonify({'error': 'Failed to decode image'}), 400

    results = model(img, conf=0.5, iou=0.5)

    detected_boxes = []
    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            conf = box.conf[0]
            cls = box.cls[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            label = f'{model.names[int(cls)]}: {conf:.2f}'
            detected_boxes.append({
                'label': label,
                'coordinates': [x1, y1, x2, y2],
                'confidence': float(conf),
                'class': int(cls)
            })

    return jsonify({'detected_boxes': detected_boxes}), 200


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
