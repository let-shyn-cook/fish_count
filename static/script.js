const video = document.getElementById('video');
const image = document.getElementById('image');
const fileInput = document.getElementById('file-input');
const chooseFileBtn = document.getElementById('choose-file');
const captureImageBtn = document.getElementById('capture-image');
const startCountingBtn = document.getElementById('start-counting');
const realtimeCountDisplay = document.getElementById('realtime-count');
const totalFishCountDisplay = document.getElementById('total-fish-count');
const dropArea = document.getElementById('drop-area');

let stream;
let isCounting = false;
let isCameraOn = false;

async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        isCameraOn = true;
    } catch (err) {
        console.error('Error accessing camera: ', err);
    }
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
    isCameraOn = false;
}

chooseFileBtn.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            image.src = `/uploads/${data.output_image}`;
            image.style.display = 'block';
            video.style.display = 'none';

            const fishCount = data.detected_boxes.length;
            realtimeCountDisplay.textContent = fishCount;
            totalFishCountDisplay.textContent = fishCount;
        } else {
            const errorData = await response.json();
            alert(`Error: ${errorData.error}`);
        }
    }
});

captureImageBtn.addEventListener('click', async () => {
    if (!isCameraOn) {
        await startCamera();
        captureImageBtn.textContent = 'Capture image';
    } else {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
        const imageDataUrl = canvas.toDataURL('image/jpeg');

        const response = await fetch('/capture', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image: imageDataUrl }),
        });

        if (response.ok) {
            const data = await response.json();
            image.src = `data:image/jpeg;base64,${data.output_image}`;
            image.style.display = 'block';
            video.style.display = 'none';

            const fishCount = data.detected_boxes.length;
            realtimeCountDisplay.textContent = fishCount;
            totalFishCountDisplay.textContent = fishCount;

            stopCamera();
            captureImageBtn.textContent = 'turn on camera';
        } else {
            const errorData = await response.json();
            alert(`Error: ${errorData.error}`);
        }
    }
});

startCountingBtn.addEventListener('click', async () => {
    if (!isCameraOn) {
        await startCamera();
    }
    isCounting = !isCounting;

    if (isCounting) {
        startCountingBtn.textContent = 'Stop count';
        startRealTimeCounting();
    } else {
        startCountingBtn.textContent = 'Realtime (beta)';
    }
});

async function startRealTimeCounting() {
    while (isCounting) {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
        const imageDataUrl = canvas.toDataURL('image/jpeg');

        console.log("Sending image data URL:", imageDataUrl);

        const response = await fetch('/realtime', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image: imageDataUrl }),
        });

        if (response.ok) {
            const data = await response.json();
            const fishCount = data.detected_boxes.length;
            realtimeCountDisplay.textContent = fishCount;
            totalFishCountDisplay.textContent = fishCount;
        } else {
            const errorData = await response.json();
            alert(`Error: ${errorData.error}`);
            break;
        }

        await new Promise(resolve => setTimeout(resolve, 1000));
    }

    if (!isCounting) {
        stopCamera();
    }
}
