// Text detection
function detectText() {
  let text = document.getElementById("text-input").value;
  fetch("/detect_text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.language)
        document.getElementById("text-result").innerText =
          "Language: " + data.language;
      else document.getElementById("text-result").innerText = data.error;
    });
}

// Image detection
function detectImage() {
  let file = document.getElementById("image-input").files[0];
  let formData = new FormData();
  formData.append("image", file);

  fetch("/detect_image", { method: "POST", body: formData })
    .then((res) => res.json())
    .then((data) => {
      if (data.language)
        document.getElementById("image-result").innerText =
          "Language: " + data.language;
      else document.getElementById("image-result").innerText = data.error;
    });
}

// Audio recording
// Audio recording
let recorder, audioStream;

async function startRecording() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    alert("Your browser does not support microphone access.");
    return;
  }

  try {
    audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recorder = new MediaRecorder(audioStream);
    let chunks = [];

    recorder.ondataavailable = (e) => chunks.push(e.data);

    recorder.onstop = async () => {
      let blob = new Blob(chunks, { type: "audio/webm" });
      let formData = new FormData();
      formData.append("audio", blob, "recording.webm");

      try {
        let res = await fetch("/detect_audio", {
          method: "POST",
          body: formData,
        });
        let data = await res.json();

        if (data.language) {
          document.getElementById("audio-result").innerText =
            "Language: " + data.language + "\nDetected Text: " + data.text;
        } else {
          document.getElementById("audio-result").innerText = data.error;
        }
      } catch (err) {
        console.error(err);
        document.getElementById("audio-result").innerText =
          "Error sending audio.";
      }
    };

    recorder.start();
    console.log("Recording started...");
  } catch (err) {
    console.error(err);
    alert("Could not access microphone. Please allow microphone access.");
  }
}

function stopRecording() {
  if (!recorder) return;
  recorder.stop();
  if (audioStream) {
    audioStream.getTracks().forEach((track) => track.stop());
  }
  console.log("Recording stopped.");
}
