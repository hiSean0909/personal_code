const API_URL = "http://127.0.0.1:8000/square";

const form = document.querySelector("#square-form");
const input = document.querySelector("#number-input");
const button = form.querySelector("button");
const result = document.querySelector("#result");
const interactionData = document.querySelector("#interaction-data");

function showInteraction(details) {
  interactionData.textContent = JSON.stringify(details, null, 2);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const x = input.value;
  const requestBody = { x };
  const requestDetails = {
    timestamp: new Date().toISOString(),
    url: API_URL,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: requestBody,
  };

  button.disabled = true;
  result.textContent = "Calculating…";
  showInteraction({ request: requestDetails, response: "Waiting for API response…" });

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody),
    });
    const responseText = await response.text();
    let data = responseText;

    try {
      data = JSON.parse(responseText);
    } catch {
      // Keep a non-JSON response as text.
    }

    showInteraction({
      request: requestDetails,
      response: {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
        body: data,
      },
    });

    if (!response.ok) {
      result.textContent = `Request failed: ${
        typeof data.detail === "string"
          ? data.detail
          : "The API could not calculate the result."
      }`;
      return;
    }

    result.textContent = `${data.x}² = ${data.square}`;
  } catch (error) {
    result.textContent = `Request failed: ${error.message}`;
    showInteraction({
      request: requestDetails,
      response: null,
      error: { message: error.message },
    });
  } finally {
    button.disabled = false;
  }
});
