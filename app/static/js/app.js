// Formatação de moeda brasileira (ex.: 9.000,00)
function formatarMoedaBRL(valorNum) {
  if (isNaN(valorNum)) return "";
  return valorNum.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

// Aplica máscara de moeda brasileira a um campo de entrada de texto
function aplicarMascaraMoeda(input) {
  if (!input) return;
  input.addEventListener("input", function () {
    var digitos = input.value.replace(/\D/g, "");
    if (!digitos) {
      input.value = "";
      return;
    }
    input.value = formatarMoedaBRL(parseInt(digitos, 10) / 100);
  });
}

document.addEventListener("DOMContentLoaded", function () {
  // Máscara de moeda nos campos .mascara-moeda
  document.querySelectorAll(".mascara-moeda").forEach(aplicarMascaraMoeda);

  // Menu lateral retrátil (sidebar)
  var sidebar = document.getElementById("sidebar");
  var btnSidebar = document.getElementById("btn-alternar-sidebar");
  var iconeSidebar = document.getElementById("icone-sidebar");
  var CHAVE_SIDEBAR = "soft_clinica_sidebar_colapsada";

  function aplicarEstadoSidebar(colapsada) {
    if (!sidebar) return;
    sidebar.classList.toggle("colapsada", colapsada);
    if (iconeSidebar) {
      iconeSidebar.classList.toggle("bi-chevron-left", !colapsada);
      iconeSidebar.classList.toggle("bi-chevron-right", colapsada);
    }
    if (btnSidebar) {
      btnSidebar.setAttribute("title", colapsada ? "Expandir menu" : "Retrair menu");
    }
  }

  if (sidebar && btnSidebar && iconeSidebar) {
    var estadoInicial = false;
    try {
      estadoInicial = localStorage.getItem(CHAVE_SIDEBAR) === "1";
    } catch (e) { /* localStorage indisponível */ }
    aplicarEstadoSidebar(estadoInicial);

    btnSidebar.addEventListener("click", function () {
      var colapsada = !sidebar.classList.contains("colapsada");
      aplicarEstadoSidebar(colapsada);
      try {
        localStorage.setItem(CHAVE_SIDEBAR, colapsada ? "1" : "0");
      } catch (e) { /* localStorage indisponível */ }
    });
  }

  // Tooltips (hints) nos botões de ação das listas
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.forEach(function (el) {
    new bootstrap.Tooltip(el);
  });

  // Confirmar exclusão
  window.confirmarExclusao = function () {
    return confirm("Tem certeza que deseja excluir este registro?");
  };

  // Preenchimento automático do valor a partir do procedimento
  var selectProcedimento = document.getElementById("procedimento_id");
  var campoValor = document.getElementById("valor");

  if (selectProcedimento && campoValor) {
    selectProcedimento.addEventListener("change", function () {
      var opcao = selectProcedimento.options[selectProcedimento.selectedIndex];
      if (opcao && opcao.dataset.valor !== undefined && opcao.dataset.valor !== "") {
        var num = parseFloat(opcao.dataset.valor);
        if (!isNaN(num)) {
          campoValor.value = formatarMoedaBRL(num);
        }
      }
    });
  }

  // Componente de data (calendário) nos campos .mascara-data
  var camposData = document.querySelectorAll(".mascara-data");
  camposData.forEach(function (campo) {
    flatpickr(campo, {
      dateFormat: "d/m/Y",
      allowInput: true,
      locale: "pt",
    });
  });

  // Modal de novo paciente
  var salvarNovoPaciente = document.getElementById("salvar-novo-paciente");
  if (salvarNovoPaciente) {
    salvarNovoPaciente.addEventListener("click", function () {
      var nome = document.getElementById("novo_paciente_nome").value.trim();
      var msg = document.getElementById("novo-paciente-msg");

      if (!nome) {
        if (msg) {
          msg.innerHTML =
            '<div class="alert alert-danger py-2">Informe o nome do paciente.</div>';
        }
        return;
      }

      fetch("/api/pacientes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nome: nome }),
      })
        .then(function (res) {
          if (!res.ok) {
            throw new Error("Erro ao cadastrar paciente");
          }
          return res.json();
        })
        .then(function (dados) {
          var select = document.getElementById("paciente_id");
          var opt = document.createElement("option");
          opt.value = dados.id;
          opt.text = dados.nome;
          select.appendChild(opt);
          select.value = dados.id;

          document.getElementById("novo_paciente_nome").value = "";
          if (msg) msg.innerHTML = "";

          var modal = bootstrap.Modal.getInstance(
            document.getElementById("modalNovoPaciente")
          );
          if (modal) modal.hide();
        })
        .catch(function (err) {
          if (msg) {
            msg.innerHTML =
              '<div class="alert alert-danger py-2">' + err.message + "</div>";
          }
        });
    });
  }

  // Exportação respeitando filtros
  var botoesExportar = document.querySelectorAll(".btn-exportar");
  var formFiltros = document.getElementById("form-filtros");

  botoesExportar.forEach(function (botao) {
    botao.addEventListener("click", function () {
      var formato = botao.dataset.formato;
      var params = new URLSearchParams();
      if (formFiltros) {
        var campos = formFiltros.querySelectorAll(
          "select[name], input[type=date][name]"
        );
        campos.forEach(function (campo) {
          if (campo.value) {
            params.append(campo.name, campo.value);
          }
        });
      }
      var url =
        "/api/atendimentos/export/" + formato + "?" + params.toString();
      window.location.href = url;
    });
  });
});
