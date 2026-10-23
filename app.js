const API = "http://127.0.0.1:8000";

let userId = null;
let intersections = [];

const $ = (id) => document.getElementById(id);

async function request(path, options = {}) {
  const response = await fetch(API + path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers
    }
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Não foi possível concluir a operação.");
  }
  return data;
}

$("register-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  $("register-result").textContent = "Cadastrando...";

  try {
    const user = await request("/api/register", {
      method: "POST",
      body: JSON.stringify({
        name: $("name").value.trim(),
        email: $("email").value.trim(),
        password: $("password").value,
        accessibility_needs: [$("need").value]
      })
    });

    userId = user.id;
    $("register-result").textContent =
      `Cadastro criado para ${user.name}.`;
    $("simulate").disabled = false;
    $("password").value = "";
  } catch (error) {
    $("register-result").textContent = error.message;
  }
});

async function loadIntersections() {
  try {
    intersections = await request("/api/intersections");
    const select = $("intersection");

    select.replaceChildren();

    for (const item of intersections) {
      const option = document.createElement("option");
      option.value = item.id;
      option.textContent = item.name;
      select.appendChild(option);
    }
  } catch (error) {
    $("light-status").textContent =
      "Não foi possível conectar à API: " + error.message;
  }
}

$("simulate").addEventListener("click", async () => {
  if (!userId) return;

  $("simulate").disabled = true;
  $("simulation-result").textContent = "Simulando...";

  try {
    const result = await request("/api/demo/simulate", {
      method: "POST",
      body: JSON.stringify({
        user_id: userId,
        intersection_id: $("intersection").value
      })
    });

    for (const color of ["red", "yellow", "green"]) {
      document.querySelector(".light ." + color)
        .classList.toggle("active", color === "green");
    }

    $("light-status").textContent =
      "VERDE SIMULADO — travessia ampliada";

    $("simulation-result").textContent =
      `Tempo normal: ${result.normal_seconds}s. ` +
      `Tempo adicional: ${result.extra_seconds}s. ` +
      `Total simulado: ${result.total_seconds}s. ` +
      result.message;
  } catch (error) {
    $("simulation-result").textContent = error.message;
  } finally {
    $("simulate").disabled = false;
  }
});

loadIntersections();
