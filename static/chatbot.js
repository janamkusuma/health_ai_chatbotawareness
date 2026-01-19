// ---------------- ENTER KEY ----------------
function checkEnter(e){
  if(e.key === "Enter"){
    sendMessage();
  }
}

// ---------------- TEXT MESSAGE ----------------
function sendMessage(){
  let input = document.getElementById("userInput");
  let msg = input.value.trim();
  let lang = document.getElementById("lang").value;
  if(msg === "") return;

  let chatBox = document.getElementById("chat-box");
  chatBox.innerHTML += `<div class="user-msg">${msg}</div>`;
  input.value = "";

  fetch("/get_response",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({message:msg, lang:lang})
  })
  .then(r=>r.json())
  .then(data=>{
    chatBox.innerHTML += `<div class="bot-msg">${data.answer}</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;
    speakText(data.answer, lang);
  });
}

// ---------------- VOICE INPUT ----------------
function startVoice(){
  if(!('webkitSpeechRecognition' in window)){
    alert("Use Google Chrome Browser");
    return;
  }

  let lang = document.getElementById("lang").value;
  const rec = new webkitSpeechRecognition();
  rec.lang = (lang==="te")?"te-IN":(lang==="hi")?"hi-IN":(lang==="ta")?"ta-IN":"en-IN";

  rec.onresult = e=>{
    document.getElementById("userInput").value = e.results[0][0].transcript;
    sendMessage();
  }
  rec.start();
}

// ---------------- VOICE OUTPUT ----------------
function speakText(text, lang){
  const sp = new SpeechSynthesisUtterance(text);
  sp.lang = (lang==="te")?"te-IN":(lang==="hi")?"hi-IN":(lang==="ta")?"ta-IN":"en-IN";
  window.speechSynthesis.speak(sp);
}

// ---------------- FILE UPLOAD ----------------
function sendFile(){
  let file = document.getElementById("fileInput").files[0];
  if(!file) return;

  let form = new FormData();
  form.append("file", file);

  fetch("/upload_media",{method:"POST", body:form})
  .then(r=>r.json())
  .then(d=>{
    document.getElementById("chat-box").innerHTML += `<div class="bot-msg">${d.answer}</div>`;
  });
}
