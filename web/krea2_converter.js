import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// Palette based on the mybrolabs logo: mustard accent on warm dark brown.
const C = {
    accent: "#e8a83c",
    accentText: "#2a1d08",
    disabledBg: "#6d5723",
    disabledText: "#d8c89e",
    boxBg: "#221c11",
    boxBorder: "#4a3b1c",
    info: "#d9c9a4",
    ok: "#a9d18d",
    warn: "#e6c35c",
    error: "#e0907a",
    nodeTitle: "#453218",
    nodeBg: "#2b2519",
};

app.registerExtension({
    name: "mybrolabs.Krea2LoraConverter",

    beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "Krea2LoraConverterFal") return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onNodeCreated?.apply(this, arguments);
            const node = this;

            node.color = C.nodeTitle;
            node.bgcolor = C.nodeBg;

            const container = document.createElement("div");
            container.style.cssText =
                "display:flex;flex-direction:column;gap:6px;padding:4px 2px;";

            const button = document.createElement("button");
            button.textContent = "Convert";
            button.style.cssText =
                "border:none;border-radius:6px;padding:8px 0;width:100%;" +
                "font-weight:600;font-size:13px;transition:filter .15s;";
            button.addEventListener("mouseenter", () => {
                if (!button.disabled) button.style.filter = "brightness(1.1)";
            });
            button.addEventListener("mouseleave", () => {
                button.style.filter = "none";
            });

            const status = document.createElement("div");
            status.style.cssText =
                `background:${C.boxBg};border:1px solid ${C.boxBorder};` +
                "border-radius:6px;padding:8px;font-size:12px;line-height:1.45;" +
                `color:${C.info};min-height:56px;white-space:pre-wrap;word-break:break-word;`;
            status.textContent = "Select a LoRA to check its format.";

            container.append(button, status);
            node.addDOMWidget("mybrolabs_ui", "div", container, { serialize: false });

            let convertible = false;

            const setButton = (enabled) => {
                convertible = enabled;
                button.disabled = !enabled;
                button.style.background = enabled ? C.accent : C.disabledBg;
                button.style.color = enabled ? C.accentText : C.disabledText;
                button.style.opacity = enabled ? "1" : "0.55";
                button.style.cursor = enabled ? "pointer" : "not-allowed";
            };
            const setStatus = (text, color) => {
                status.textContent = text;
                status.style.color = color;
            };
            setButton(false);

            const widgetValue = (name) =>
                node.widgets?.find((w) => w.name === name)?.value;

            async function inspect() {
                const lora = widgetValue("lora_name");
                if (!lora) {
                    setButton(false);
                    setStatus("No LoRA selected.", C.info);
                    return;
                }
                setButton(false);
                setStatus("Checking " + lora + " ...", C.info);
                try {
                    const res = await api.fetchApi(
                        "/mybrolabs/krea2/inspect?lora=" + encodeURIComponent(lora)
                    );
                    const data = await res.json();
                    if (data.error) {
                        setStatus(data.error, C.error);
                    } else if (data.fal_format) {
                        setButton(true);
                        const rank = data.rank != null ? `, rank ${data.rank}` : "";
                        setStatus(
                            `✓ fal Krea 2 LoRA: ${data.fal_keys} keys${rank}.\n` +
                                `Saves as: ${data.suggested_name}`,
                            C.ok
                        );
                    } else {
                        setStatus(
                            "Already ComfyUI-compatible (not the fal format). " +
                                "Nothing to convert — it should load in ComfyUI directly.",
                            C.warn
                        );
                    }
                } catch (e) {
                    setStatus("Inspect failed: " + e, C.error);
                }
            }

            button.addEventListener("click", async () => {
                if (!convertible) return;
                setButton(false);
                setStatus("Converting ...", C.info);
                try {
                    const res = await api.fetchApi("/mybrolabs/krea2/convert", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            lora_name: widgetValue("lora_name"),
                            output_name: widgetValue("output_name") ?? "",
                            overwrite: !!widgetValue("overwrite"),
                        }),
                    });
                    const data = await res.json();
                    const ok = (data.status ?? "").startsWith("OK");
                    setStatus(
                        (ok ? "✓ " : "") + (data.status ?? "No response from server."),
                        ok ? C.ok : C.warn
                    );
                    // On failure (e.g. output exists) keep the button usable for a retry.
                    setButton(!ok);
                    if (ok) {
                        try {
                            await app.refreshComboInNodes();
                        } catch {}
                    }
                } catch (e) {
                    setStatus("Convert failed: " + e, C.error);
                    setButton(true);
                }
            });

            const loraWidget = node.widgets?.find((w) => w.name === "lora_name");
            if (loraWidget) {
                const orig = loraWidget.callback;
                loraWidget.callback = function () {
                    const out = orig?.apply(this, arguments);
                    inspect();
                    return out;
                };
            }

            node.mybrolabsInspect = inspect;
            setTimeout(inspect, 150);
            return r;
        };

        // Re-check after a saved workflow restores widget values.
        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            const r = onConfigure?.apply(this, arguments);
            setTimeout(() => this.mybrolabsInspect?.(), 150);
            return r;
        };
    },
});
