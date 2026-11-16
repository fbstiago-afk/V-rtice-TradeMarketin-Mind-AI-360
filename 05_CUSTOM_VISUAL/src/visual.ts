"use strict";
import powerbi from "powerbi-visuals-api";
import "./../style/visual.less";
import VisualConstructorOptions = powerbi.extensibility.visual.VisualConstructorOptions;
import VisualUpdateOptions = powerbi.extensibility.visual.VisualUpdateOptions;
import IVisual = powerbi.extensibility.visual.IVisual;

const SUGESTOES = [
  "Qual é a definição de ruptura utilizada pela empresa?",
  "Como a execução de campanhas é avaliada?",
  "Quais indicadores devo analisar para investigar uma queda de vendas?",
  "Quais regras determinam o acesso aos dados?"
];

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, text?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;   // textContent: nunca injeta HTML
  return e;
}

export class Visual implements IVisual {
  private root: HTMLElement; private status: HTMLElement; private out: HTMLElement;
  private input: HTMLInputElement; private ctxEl: HTMLElement;
  private url = "http://127.0.0.1:8360"; private usuario = "gestor.demo"; private contexto = "";

  constructor(options: VisualConstructorOptions) {
    this.root = el("div", "tm");
    const head = el("div", "tm-head");
    head.appendChild(el("div", "tm-title", "Assistente RAG · conectado à API local"));
    this.status = el("div", "tm-status", "verificando…"); head.appendChild(this.status);
    this.root.appendChild(head);
    this.ctxEl = el("div", "tm-ctx"); this.root.appendChild(this.ctxEl);
    const form = el("div", "tm-form");
    this.input = el("input", "tm-input") as HTMLInputElement;
    this.input.placeholder = "Pergunte sobre definições, métodos e regras…"; this.input.maxLength = 500;
    const btn = el("button", "tm-btn", "Perguntar");
    btn.onclick = () => this.ask(this.input.value);
    this.input.onkeydown = (ev) => { if (ev.key === "Enter") this.ask(this.input.value); };
    form.appendChild(this.input); form.appendChild(btn); this.root.appendChild(form);
    const chips = el("div", "tm-chips");
    SUGESTOES.forEach(s => { const c = el("button", "tm-chip", s); c.onclick = () => { this.input.value = s; this.ask(s); }; chips.appendChild(c); });
    this.root.appendChild(chips);
    this.out = el("div", "tm-out"); this.root.appendChild(this.out);
    options.element.appendChild(this.root);
    this.health();
    setInterval(() => this.health(), 15000);
  }

  private async health() {
    try {
      const r = await fetch(this.url + "/health");
      const j = await r.json();
      this.status.textContent = j.demo ? "● API online (modo demo)" : "● API online · requer token";
      this.status.className = "tm-status ok";
    } catch {
      this.status.textContent = "● API offline — execute iniciar_api.bat";
      this.status.className = "tm-status off";
    }
  }

  private async ask(q: string) {
    q = (q || "").trim(); if (!q) return;
    this.out.textContent = ""; this.out.appendChild(el("div", "tm-loading", "Consultando documentos autorizados…"));
    const t0 = Date.now();
    try {
      const r = await fetch(this.url + "/ask", { method: "POST", headers: { "Content-Type": "application/json", "X-User": this.usuario },
        body: JSON.stringify({ question: q, contexto: this.contexto }) });
      const j = await r.json(); this.render(j, r.status, Date.now() - t0); this.health();
    } catch {
      this.out.textContent = ""; this.out.appendChild(el("div", "tm-err", "Não foi possível acessar a API em " + this.url + ". Nenhuma resposta foi gerada."));
      this.health();
    }
  }

  private render(j: any, code: number, ms: number) {
    this.out.textContent = "";
    if (code !== 200) { this.out.appendChild(el("div", "tm-err", "Acesso negado pela API: " + (j.erro || code))); return; }
    const badge = { respondido: "Resposta fundamentada", bloqueado: "Bloqueado pelo guardrail", sem_evidencia: "Sem evidência documental" }[j.status as string] || j.status;
    const meta = el("div", "tm-meta " + j.status, badge + " · " + ms + " ms · usuário " + this.usuario);
    this.out.appendChild(meta);
    if (j.status === "bloqueado") { this.out.appendChild(el("div", "tm-ans", "Regra aplicada: " + j.regra)); return; }
    this.out.appendChild(el("div", "tm-ans", j.resposta || ""));
    (j.evidencias || []).slice(0, 4).forEach((e: any) => {
      const card = el("div", "tm-ev");
      card.appendChild(el("div", "tm-ev-h", e.titulo + " · v" + e.versao + " · " + (e.origem || "") + " · relevância " + Number(e.score).toFixed(2)));
      card.appendChild(el("div", "tm-ev-t", e.texto));
      this.out.appendChild(card);
    });
    this.out.appendChild(el("div", "tm-foot", "Resposta extrativa (trechos recuperados); não há LLM generativo conectado. Números de indicadores vêm do modelo semântico, não do RAG."));
  }

  public update(options: VisualUpdateOptions) {
    const dv = options.dataViews && options.dataViews[0];
    const o: any = dv && dv.metadata && dv.metadata.objects && dv.metadata.objects["api"];
    if (o) { if (o.url) this.url = String(o.url).replace(/\/$/, ""); if (o.usuario) this.usuario = String(o.usuario); }
    const v = dv && dv.single && dv.single.value;
    this.contexto = v ? String(v) : "";
    this.ctxEl.textContent = this.contexto ? "Contexto do relatório: " + this.contexto : "";
  }

  public getFormattingModel(): powerbi.visuals.FormattingModel {
    const slice = (uid: string, name: string, prop: string, value: string): powerbi.visuals.FormattingSlice => ({
      uid, displayName: name,
      control: { type: powerbi.visuals.FormattingComponent.TextInput,
        properties: { descriptor: { objectName: "api", propertyName: prop }, value, placeholder: "" } }
    } as powerbi.visuals.FormattingSlice);
    return { cards: [{ uid: "api_card", displayName: "API TradeMind",
      groups: [{ uid: "api_group", displayName: "Conexão",
        slices: [slice("api_url", "URL da API", "url", this.url), slice("api_user", "Usuário (modo demo)", "usuario", this.usuario)] }] }] };
  }
}
