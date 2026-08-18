let sessionId = null;

document.getElementById("start-btn").addEventListener("click", async () => {
  const idea = document.getElementById("idea-input").value;
  const res = await fetch("/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idea }),
  });
  const data = await res.json();
  sessionId = data.session_id;
  document.getElementById("idea-form").style.display = "none";
  document.getElementById("pipeline").style.display = "block";
  await advance();
});

document.getElementById("advance-btn").addEventListener("click", advance);

async function advance() {
  const message = document.getElementById("message-input").value;
  const res = await fetch(`/session/${sessionId}/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  const data = await res.json();
  document.getElementById("message-input").value = "";

  if (data.status === "warning") {
    document.getElementById("warning").textContent =
      data.warning + "\n\n" + data.raw_text;
    return;
  }

  document.getElementById("warning").textContent = "";
  document.getElementById("stage-name").textContent = data.stage_name;
  document.getElementById("stage-output").textContent = JSON.stringify(
    data.output,
    null,
    2
  );

  if (data.complete) {
    document.getElementById("advance-btn").disabled = true;
    document.getElementById("stage-name").textContent += " (전체 완료)";
  }
}
